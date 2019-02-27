# -*- coding: utf-8 -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the reproman package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import os.path as op

from unittest.mock import patch
import pytest

from reproman.consts import TEST_SSH_DOCKER_DIGEST
from reproman.utils import chpwd
from reproman.resource.shell import Shell
from reproman.support.exceptions import MissingExternalDependency
from reproman.support.exceptions import OrchestratorError
from reproman.support.external_versions import external_versions
from reproman.support.jobs import orchestrators as orcs
from reproman.tests.fixtures import get_docker_fixture
from reproman.tests.skip import mark
from reproman.tests.utils import create_tree


docker_container = get_docker_fixture(TEST_SSH_DOCKER_DIGEST,
                                      name="testing-container", scope="module")


@pytest.fixture(scope="module")
def docker_resource(docker_container):
    # TODO: This could be reworked to be included in fixtures.py. It is similar
    # to get_singularity_fixture, which should probably be renamed to include
    # "resource".
    from reproman.resource.docker_container import DockerContainer
    return DockerContainer("testing-container")


@pytest.fixture(scope="module")
def shell():
    return Shell("localshell")


def test_orc_root_directory(shell):
    orc = orcs.PlainOrchestrator(shell, submission_type="local")
    assert orc.root_directory == op.expanduser("~/.reproman/run-root")


@pytest.mark.parametrize("value", [{}, {"HOME": "rel/path"}],
                         ids=["no home", "relative"])
def test_orc_root_directory_error(shell, value):
    orc = orcs.PlainOrchestrator(shell, submission_type="local")
    with patch.object(orc.session, "query_envvars", return_value=value):
        with pytest.raises(OrchestratorError):
            orc.root_directory


@pytest.fixture()
def check_orc_plain(tmpdir):
    local_dir = str(tmpdir)

    def fn(resource, remote_dir):
        job_spec = {"root_directory": op.join(remote_dir, "nm-run"),
                    "inputs": ["in"],
                    "outputs": ["out"],
                    "command_str": 'bash -c "cat in >out && echo more >>out"'}

        create_tree(local_dir, {"in": "content\n"})
        with chpwd(local_dir):
            orc = orcs.PlainOrchestrator(resource, submission_type="local",
                                         job_spec=job_spec)
            orc.prepare_remote()
            assert orc.session.exists(op.join(orc.working_directory, "in"))

            orc.submit()
            orc.follow()
            assert orc.session.exists(op.join(orc.working_directory, "out"))

            orc.fetch()
            assert open("out").read() == "content\nmore\n"
    return fn


def test_orc_plain_shell(check_orc_plain, shell, tmpdir):
    check_orc_plain(shell, str(tmpdir))


def test_orc_plain_docker(check_orc_plain, docker_resource):
    check_orc_plain(docker_resource, "/root/")


@pytest.mark.skipif(external_versions["datalad"], reason="DataLad found")
def test_orc_no_datalad(tmpdir, shell):
    with chpwd(str(tmpdir)):
        with pytest.raises(MissingExternalDependency):
            orcs.DataladLocalRunOrchestrator(shell, submission_type="local")


@mark.skipif_no_datalad
def test_orc_no_dataset(tmpdir, shell):
    with chpwd(str(tmpdir)):
        with pytest.raises(OrchestratorError):
            orcs.DataladLocalRunOrchestrator(shell, submission_type="local")


@pytest.mark.integration
@mark.skipif_no_datalad
@pytest.mark.parametrize("orc_class",
                         [orcs.DataladLocalRunOrchestrator,
                          orcs.DataladPairRunOrchestrator],
                         ids=["orc:local", "orc:pair"])
@pytest.mark.parametrize("sub_type",
                         ["local",
                          pytest.param("condor", marks=mark.skipif_no_condor)],
                         ids=["sub:local", "sub:condor"])
def test_orc_datalad_run(tmpdir, shell, orc_class, sub_type):
    import datalad.api as dl

    tmpdir = str(tmpdir)

    job_spec = {"root_directory": op.join(tmpdir, "nm-run"),
                "inputs": ["in"],
                "outputs": ["out"],
                "command_str": 'bash -c "cat in >out && echo more >>out"'}
    local_dir = op.join(tmpdir, "local")

    create_tree(local_dir, {"in": "content\n"})
    ds = dl.Dataset(local_dir).create(force=True)
    ds.add(".")

    with chpwd(local_dir):
        orc = orc_class(shell, submission_type=sub_type, job_spec=job_spec)
        orc.prepare_remote()
        orc.submit()
        orc.follow()

        orc.fetch()
        assert ds.repo.file_has_content("out")
        assert open("out").read() == "content\nmore\n"


@mark.skipif_no_datalad
def test_orc_datalad_pair(tmpdir, shell):
    import datalad.api as dl

    tmpdir = str(tmpdir)

    job_spec = {"root_directory": op.join(tmpdir, "nm-run"),
                "inputs": ["in"],
                "outputs": ["out"],
                "command_str": 'bash -c "cat in >out && echo more >>out"'}
    local_dir = op.join(tmpdir, "local")

    create_tree(local_dir, {"in": "content\n"})
    ds = dl.Dataset(local_dir).create(force=True)
    ds.add(".")

    with chpwd(local_dir):
        orc = orcs.DataladPairOrchestrator(
            shell, submission_type="local", job_spec=job_spec)
        orc.prepare_remote()
        orc.submit()
        orc.follow()

        orc.fetch()
        # The local fetch variant doesn't currently get the content, so just
        # check that the file is under annex.
        assert ds.repo.is_under_annex("out")
