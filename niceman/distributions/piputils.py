# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the niceman package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Utilities for working with pip.
"""
import itertools
import os
import re

from niceman.utils import execute_command_batch


def parse_pip_show(out):
    pip_info = {}
    list_tag = None
    for line in out.splitlines():
        if line.startswith("#"):   # Skip if comment
            continue
        if line.startswith("  "):  # List item
            item = line[2:].strip()
            if list_tag and item:  # Add the item to the existing list
                pip_info[list_tag].append(item)
            continue
        if ":" in line:            # List tag or tag/value
            split_line = line.split(":", 1)
            tag = split_line[0].strip()
            value = None
            if len(split_line) > 1:  # Parse the value if there
                value = split_line[1].strip()
            if value:                # We have both a tag and a value
                pip_info[tag] = value
                list_tag = None      # A new tag stops the previous list
            else:                    # We have just a list_tag so start it
                list_tag = tag
                pip_info[list_tag] = []

    return pip_info


def _pip_batched_show(session, which_pip, pkgs):
    cmd = [which_pip, "show", "-f"]
    batch = execute_command_batch(session, cmd, pkgs)
    sep_re = re.compile("^---$", flags=re.MULTILINE)
    entries = (sep_re.split(stacked) for stacked, _, _ in batch)

    for pkg, entry in zip(pkgs, itertools.chain(*entries)):
        info = parse_pip_show(entry)
        yield pkg, info


def pip_show(session, which_pip, pkgs):
    """Gather package details from `pip show`.

    Parameters
    ----------
    session : Session instance
        Session in which to execute the command.
    which_pip : str
        Name of the pip executable.
    pkgs : sequence
        Collection of packages pass to the command.

    Returns
    -------
    A tuple of two dicts, where the first maps a package name to its
    details, and the second maps package files to the package name.
    """
    packages = {}
    file_to_pkg = {}

    show_entries = _pip_batched_show(session, which_pip, pkgs)

    for pkg, info in show_entries:
        details = {"name": info["Name"],
                   "version": info["Version"],
                   "location": info["Location"]}
        packages[pkg] = details
        for path in info["Files"]:
            full_path = os.path.normpath(
                os.path.join(info["Location"], path))
            file_to_pkg[full_path] = pkg
    return packages, file_to_pkg


def parse_pip_list(out):
    """Parse the output of `pip list --format=legacy`.
    """
    pkg_re = re.compile(r"^(?P<package>[^(]+) "
                        r"\((?P<version>.*?)"
                        r"(?:, (?P<location>.*))?\)$",
                        re.MULTILINE)
    for pkg, version, location in pkg_re.findall(out):
        yield pkg.lower(), version, location or None


def pip_list(session, which_pip, local_only=False):
    """Return output of `pip list --format=legacy`.

    Parameters
    ----------
    session : Session instance
        Session in which to execute the command.
    which_pip : str
        Name of the pip executable.
    local_only : boolean, optional
        Do not include globally installed packages.  Otherwise, global
        packages will be included if pip has global access (e.g.,
        "--system-site-packages" was used when creating the virtualenv
        directory).

    Returns
    -------
    A generator that yields (name, version, location) for each
    package.  Location will be None unless the package is editable.
    """
    # We could use either 'pip list' or 'pip freeze' to get a list
    # of packages.  The choice to use 'list' rather than 'freeze'
    # is based on how they show editable packages.  'list' outputs
    # a source directory of the package, whereas 'freeze' outputs
    # a URL like "-e git+https://github.com/[...]".
    #
    # It would be nice to use 'pip list --format=json' rather than
    # the legacy format.  However, currently (pip 9.0.1, 2018/01),
    # the json format does not include location information for
    # editable packages (though it is supported in a developmental
    # version).
    cmd = [which_pip, "list", "--format=legacy"]
    if local_only:
        cmd.append("--local")
    out, _ = session.execute_command(cmd)
    return parse_pip_list(out)


def get_pip_packages(session, which_pip, local_only=False):
    """Return a list of pip packages.

    Parameters
    ----------
    session : Session instance
        Session in which to execute the command.
    which_pip : str
        Name of the pip executable.
    local_only : boolean, optional
        Do not include globally installed packages.  Otherwise, global
        packages will be included if pip has global access (e.g.,
        "--system-site-packages" was used when creating the virtualenv
        directory).

    Returns
    -------
    A generator that yields package names.
    """
    return (pkg for pkg, _, _ in pip_list(session, which_pip, local_only))


def get_package_details(session, which_pip, packages=None):
    """Get package details from `pip show` and `pip list`.

    This is similar to `pip_show`, but it uses `pip list` to get information
    about editable locations and to optionally generate the list of packages.

    Parameters
    ----------
    session : Session instance
        Session in which to execute the command.
    which_pip : str
        Name of the pip executable.
    packages : list of str, optional
        Package names.  If not given, all packages returned by `pip list` are
        used.

    Returns
    -------
    A tuple of two dicts, where the first maps a package name to its
    details and the second maps package files to the package name.
    """
    pkgs, _, editlocs = zip(*pip_list(session, which_pip))

    if packages is None:
        packages = pkgs

    pkg_to_editloc = dict(zip(pkgs, editlocs))
    details, file_to_pkg = pip_show(session, which_pip, packages)
    for pkg in details:
        details[pkg]["editable"] = pkg_to_editloc[pkg] is not None
    return details, file_to_pkg
