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
import platform
from pathlib import Path

import pytest
from pytest_operator.plugin import OpsTest


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
async def lldpd_charm(ops_test: OpsTest, charm_base: str) -> Path:
    # Multiple charms will be built, but the build_charm function only returns
    # the path to one of the charms. Find the charm that matches the charm_base
    # in order to test the right one.
    await ops_test.build_charm(".")

    base = charm_base.replace("@", "-")
    arch = platform.machine()
    # convert the x86_64 arch into the amd64 arch used by charmcraft.
    if arch == "x86_64":
        arch = "amd64"

    build_dir = (ops_test.tmp_path / "charms").absolute()
    charm_file = build_dir / f"lldpd_{base}-{arch}.charm"
    if not charm_file.exists():
        raise ValueError(f"Unable to find charm file {charm_file}")

    return charm_file
