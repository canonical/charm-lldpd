# Contributing to the lldpd charm

## Overview

This document explains the processes and practices recommended for contributing enhancements to
this charm.

- Generally, before developing enhancements to this charm you should consider [opening an issue](
  https://github.com/canonical/charm-lldp/issues) explaining your bug or use case.
- Familiarising yourself with the [Charmed Operator Framework](https://juju.is/docs/sdk)
  library will help you when working on new features or bug fixes.
- All enhancements and code changes require review before being merged. Code review typically
  examines:
  - code quality
  - test coverage
  - user experience for administrators deploying and operating this charm
- Please help us out by ensuring easy to review branches by rebasing your pull request branch
  onto the `main` branch. This also avoids merge commits and creates a linear Git commit
  history. Please do *not* merge the main branch into your PR.

## Developing

Install `tox`, `charmcraft` and `juju`.

```bash
sudo apt-get install tox
sudo snap install charmcraft --classic
sudo snap install juju
```

## Testing

To test the charm, there are several tox targets which can be used

```commandline
tox run -e format       # update your code according to linting rules
tox run -e lint         # code style tests
tox run -e static-charm # runs static analysis on the charm
tox run -e unit         # unit tests
tox                     # runs lint, static analysis and unit tests
```

## Building

Build the charm in the local repository using the `charmcraft` tool.

```commandline
charmcraft pack
```

## Deploy

```commandline
# Create a model
juju add-model test

# Enable debug logging (optional)
juju model-config logging-config="<root>=INFO;unit=DEBUG"

# Deploy the charm
juju deploy --base ubuntu@22.04 ./lldpd_ubuntu-22.04-amd64.charm
```

## Canonical Contributor Agreement
Canonical welcomes contributions to the lldpd charm. Please check out our [contributor 
agreement](https://ubuntu.com/legal/contributors) if you are interested in contributing to this
code base.
