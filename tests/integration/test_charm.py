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

"""Test lldpd charm deployment."""

import asyncio
import logging
import pytest

from pytest_operator.plugin import OpsTest


logger = logging.getLogger(__name__)

NUM_UNITS = 2


@pytest.mark.abort_on_fail
@pytest.mark.skip_if_deployed
@pytest.mark.order(1)
async def test_build_and_deploy(
    ops_test: OpsTest, charm_base: str, lldpd_charm
) -> None:
    """Test the lldpd charm builds and deploys."""
    logger.info(f"Building and deploying lldp charms for base: {charm_base}")
    lldpd = await lldpd_charm

    logger.info(f"lldpd charm is located at: {lldpd}")

    # Deploy ubuntu and lldpd charms.
    await asyncio.gather(
        ops_test.model.deploy(
            "ubuntu",
            application_name="ubuntu",
            num_units=NUM_UNITS,
            base=charm_base,
        ),
        ops_test.model.deploy(
            str(lldpd),
            application_name="lldpd",
            num_units=0,
            base=charm_base,
        ),
    )

    # Relate lldpd with ubuntu
    await ops_test.model.relate("ubuntu:juju-info", "lldpd:juju-info")
    async with ops_test.fast_forward():
        await ops_test.model.wait_for_idle(
            apps=["lldpd", "ubuntu"], status="active", timeout=1800
        )
        for unit in range(NUM_UNITS):
            uname = f"lldpd/{unit}"
            assert ops_test.model.units.get(uname).workload_status == "active"


@pytest.mark.order(2)
async def test_lldpd_is_active(ops_test: OpsTest) -> None:
    """Test that the lldpd services are active in each juju unit."""
    logger.info("Validating that lldpd is active inside each juju unit.")
    for unit in ops_test.model.applications["lldpd"].units:
        status = (await unit.ssh("systemctl is-active lldpd")).strip()
        assert status == "active", f"{unit.name} lldpd is not active"
