#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Configure lldpd operator integration tests."""

import logging
import pathlib
import platform
import subprocess

import jubilant
import pytest

logger = logging.getLogger(__name__)


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--charm-base",
        action="store",
        default="ubuntu@22.04",
        help="Charm base version to use for integration tests",
    )
    parser.addoption(
        "--enable-discovery",
        action="store_true",
        default=False,
        help="Enables lldpd discovery tests. "
        "May not succeed if using VMs or containers",
    )


@pytest.fixture(scope="module")
def charm_base(request) -> str:
    """Get the lldp charm base to use."""
    return request.config.option.charm_base


@pytest.fixture(scope="module")
def juju():
    """Provide a temporary model, torn down at the end of the module."""
    with jubilant.temp_model(config={"update-status-hook-interval": "10s"}) as juju:
        yield juju


@pytest.fixture(scope="module")
def lldpd_charm(charm_base: str) -> pathlib.Path:
    # charmcraft packs one file per platform. Build and return the charm that
    # matches charm_base so the right one is tested.
    subprocess.run(["charmcraft", "pack"], check=True)

    base = charm_base.replace("@", "-")
    arch = platform.machine()
    # convert the x86_64 arch into the amd64 arch used by charmcraft.
    if arch == "x86_64":
        arch = "amd64"

    charm_file = pathlib.Path(f"lldpd_{base}-{arch}.charm").absolute()
    if not charm_file.exists():
        raise ValueError(f"Unable to find charm file {charm_file}")

    return charm_file
