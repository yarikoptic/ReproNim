# ReproMan

[![Supports python version](https://img.shields.io/pypi/pyversions/datalad)](https://pypi.org/project/datalad/)
[![GitHub release](https://img.shields.io/github/release/ReproNim/reproman.svg)](https://GitHub.com/ReproNim/reproman/releases/)
[![PyPI version fury.io](https://badge.fury.io/py/reproman.svg)](https://pypi.python.org/pypi/reproman/)
[![Travis tests status](https://secure.travis-ci.org/ReproNim/reproman.png?branch=master)](https://travis-ci.org/ReproNim/reproman)
[![codecov.io](https://codecov.io/github/ReproNim/reproman/coverage.svg?branch=master)](https://codecov.io/github/ReproNim/reproman?branch=master)
[![Documentation](https://readthedocs.org/projects/reproman/badge/?version=latest)](https://reproman.readthedocs.io/en/latest/?badge=latest)


ReproMan aims to simplify creation and management of computing environments
in Neuroimaging.  While concentrating on Neuroimaging use-cases, it is
by no means is limited to this field of science and tools will find
utility in other fields as well.

# Status

ReproMan is under rapid development. While
the code base is still growing the focus is increasingly shifting towards
robust and safe operation with a sensible API. There has been no major public
release yet, as organization and configuration are still subject of
considerable reorganization and standardization. 


See [CONTRIBUTING.md](CONTRIBUTING.md) if you are interested in
internals and/or contributing to the project.

# Installation

ReproMan requires Python 3 (>= 3.6).

## Linux'es and OSX (Windows yet TODO) - via pip

By default, installation via pip (`pip install reproman`) installs core functionality of reproman
allowing for managing datasets etc.  Additional installation schemes
are available, so you could provide enhanced installation via
`pip install 'reproman[SCHEME]'` where `SCHEME` could be

- tests
     to also install dependencies used by unit-tests battery of the reproman
- full
     to install all of possible dependencies, e.g. [DataLad](http://datalad.org)

For installation through `pip` you would need some external dependencies
not shipped from it (e.g. `docker`, `singularity`, etc.) for which please refer to
the next section.  

## Debian-based systems

On Debian-based systems we recommend to enable [NeuroDebian](http://neuro.debian.net)
from which we will soon provide recent releases of ReproMan.  We will also provide backports of
all necessary packages from that repository.


## Dependencies

Our `setup.py` and corresponding packaging describes all necessary dependencies.
On Debian-based systems we recommend to enable [NeuroDebian](http://neuro.debian.net)
since we use it to provide backports of recent fixed external modules we
depend upon.  Additionally, if you would
like to develop and run our tests battery see [CONTRIBUTING.md](CONTRIBUTING.md)
regarding additional dependencies.

# A typical workflow for `reproman run`

This example is heavily based on the ["Typical workflow"](https://github.com/ReproNim/containers/#a-typical-workflow)
example created for [///repronim/containers](https://github.com/ReproNim/containers/) ...

## Step 1: Create the HTCondor AWS EC2 cluster

Run (need to be done once, makes resource available for `reproman login` or `reproman run`):

```shell
reproman create aws-hpc2 -t aws-condor -b size=2 -b instance_type=t2.medium
```
to create a new ReproMan resource: 2 AWS EC2 instances, with HTCondor installed...

## Step 2: Create analysis dataset and run computation on aws-hpc2


```shell
#!/bin/sh
... all exactly the same as in ///repronim/containers
# Execute desired preprocessing in parallel across two subjects
# on remote AWS EC2 cluster, creating a provenance record
# in git history containing all condor submission scripts and logs, and
# fetching them locally
reproman run -r aws-hpc2 \
   --sub condor --orc datalad-pair \
   --jp "container=containers/bids-mriqc" --bp subj=02,13 --follow \
   --input 'sourcedata/sub-{p[subj]}' \
   --output . \
   '{inputs}' . participant group -w workdir --participant_label '{p[subj]}'
)
```

## Step 3: Remove resource

... use `reproman delete aws-hpc2` to terminate remote cluster in AWS, to not cause unnecessary charges.

# License

MIT/Expat


# Disclaimer

It is in a beta stage -- majority of the functionality is usable but
Documentation and API enhancements is WiP to make it better.  Please do not be
shy of filing an issue or a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md)
for the guidance.

[Git]: https://git-scm.com
[Git-annex]: http://git-annex.branchable.com
