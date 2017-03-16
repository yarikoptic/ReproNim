# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil; coding: utf-8 -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the niceman package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Classes to identify conda-managed files/packages"""

"""
## Some notes

$> conda info --json  # for general info about conda setup
{
  "GID": 47522,
  "UID": 47521,
  "channels": [
    "https://conda.anaconda.org/conda-forge/linux-64",
    "https://conda.anaconda.org/conda-forge/noarch",
    "https://repo.continuum.io/pkgs/free/linux-64",
    "https://repo.continuum.io/pkgs/free/noarch",
    "https://repo.continuum.io/pkgs/r/linux-64",
    "https://repo.continuum.io/pkgs/r/noarch",
    "https://repo.continuum.io/pkgs/pro/linux-64",
    "https://repo.continuum.io/pkgs/pro/noarch"
  ],
  "conda_build_version": "not installed",
  "conda_env_version": "4.3.14",
  "conda_prefix": "/home/yoh/anaconda2",
  "conda_private": false,
  "conda_version": "4.3.14",
  "default_prefix": "/home/yoh/anaconda2/envs/datalad",
...

$> conda list --json
[
  {
    "base_url": null,
    "build_number": 1,
    "build_string": "py27_1",
    "channel": "conda-forge",
    "dist_name": "backports.shutil_get_terminal_size-1.0.0-py27_1",
    "name": "backports.shutil_get_terminal_size",
    "platform": null,
    "version": "1.0.0",
    "with_features_depends": null
  },
...

# for information about specific package with version/revision.   Still could be
# multiple hits (I guess) if coming from different channels, and definetely could
# have multiple entries in the list here because of different arch's, builds
$> conda info git='2.8.2 3' --json
{
  "git=2.8.2 3": [
    {
      "arch": "x86_64",
      "build": "3",
      "build_number": 3,
      "channel": "https://conda.anaconda.org/conda-forge/linux-64",
      "depends": [
        "curl",
        "expat",
        "openssl 1.0.*",
        "zlib 1.2.*"
      ],
      "fn": "git-2.8.2-3.tar.bz2",
      "has_prefix": true,
      "license": "GPL v2 and LGPL 2.1",
      "md5": "863b666a88deebe8a8dbe5b870a69c2f",
      "name": "git",
      "noarch": null,
      "platform": "linux",
      "requires": [],
      "schannel": "conda-forge",
      "size": 8752840,
      "subdir": "linux-64",
      "url": "https://conda.anaconda.org/conda-forge/linux-64/git-2.8.2-3.tar.bz2",
      "version": "2.8.2"
    }
  ]
}

But I think we will just need to load all the meta-information stored
in conda-meta which has EVERYTHING we would need -- build, files, url, md5sum of
the package etc.  I guess we could just take it as is, prune "null"'ed items
and prune files not referenced (although keep .py for any .pyc used?)

hopa:~/anaconda2/envs/datalad
$> head -n 20 conda-meta/gitpython-2.1.1-py27_0.json
{
  "arch": "x86_64",
  "auth": null,
  "build": "py27_0",
  "build_number": 0,
  "channel": "https://conda.anaconda.org/conda-forge/linux-64",
  "depends": [
    "gitdb >=0.6.4",
    "python 2.7*"
  ],
  "files": [
    "lib/python2.7/site-packages/GitPython-2.1.1-py2.7.egg-info/PKG-INFO",
    "lib/python2.7/site-packages/GitPython-2.1.1-py2.7.egg-info/SOURCES.txt",
    "lib/python2.7/site-packages/GitPython-2.1.1-py2.7.egg-info/dependency_links.txt",
    "lib/python2.7/site-packages/GitPython-2.1.1-py2.7.egg-info/not-zip-safe",

# but may be we don't need to collect all of that information? e.g. may be
  sufficient just as much as conda's own history contains? e.g.

  +conda-forge::ca-certificates-2017.1.23-0
  +conda-forge::certifi-2017.1.23-py27_0

  thus the channel, name, version, and the build
  BUT it does not contain the channel... and multiple channels could provide
  "identical" according to those fields packages.  so would be great to at
  least point to the correct channel/origin ;)

# or   conda export   itself provides all packages for the environment
  with their versions and builds and also includes 'pip' installed stuff as
  well

# note that conda simply overrides over what pip might have installed, while
  leaving behind any pip-install specific files such as ...dist-info/ and
  then e.g. wiping out actual content of the package upon 'conda uninstall'.
  So -- altogether a messy user could have installed conda over pip or vise
  versa and it would not be 'rebuildable' per se since order of those installations
  would be not really feasible to track/replicate.  We might just want to warn
  if we detect such situations

# pip provides "local" information  but has no clue about which build etc

$> pip show  GitPython
Name: GitPython
Version: 2.1.1
Summary: Python Git Library
Home-page: https://github.com/gitpython-developers/GitPython
Author: Sebastian Thiel, Michael Trier
Author-email: byronimo@gmail.com, mtrier@gmail.com
License: BSD License
Location: /home/yoh/anaconda2/envs/datalad/lib/python2.7/site-packages
Requires: gitdb2

# pip freeze then could provide a full list of modules installed with their versions

# pip provides meta-information about the installation under
  ./lib/python2.7/site-packages/*dist-info
  so we could "theoretically" figure out whenever
# conda list --explicit is somewhat nice to provide exact URLs for where
# to fetch those packages from

$> conda list --explicit
# This file may be used to create an environment using:
# $ conda create --name <env> --file <this file>
# platform: linux-64
@EXPLICIT
https://conda.anaconda.org/conda-forge/linux-64/backports.shutil_get_terminal_size-1.0.0-py27_1.tar.bz2

# Notes

-  has "fuzzy" version matching with a single = by matching the leading
   version, while == is for precise matching

- pip does not store "True origin" for the package, i.e. I could not find
  any record to reflect that I have installed directly from git e.g.

  pip install git+git://github.com/tqdm/tqdm

  so we would be able only to store information to install from pypi, but
  should allow to provide a 'url' field!
"""
