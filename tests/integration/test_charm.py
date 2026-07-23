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

import logging
import pathlib

import jubilant
import pytest

logger = logging.getLogger(__name__)

NUM_UNITS = 2


@pytest.mark.order(1)
def test_build_and_deploy(
    juju: jubilant.Juju, charm_base: str, lldpd_charm: pathlib.Path
) -> None:
    """Test the lldpd charm builds and deploys."""
    logger.info(f"Building and deploying lldp charms for base: {charm_base}")
    logger.info(f"lldpd charm is located at: {lldpd_charm}")

    # Deploy the ubuntu principal and the lldpd subordinate. The juju CLI
    # resolves the ubuntu charm revision for the requested base.
    juju.deploy("ubuntu", "ubuntu", num_units=NUM_UNITS, base=charm_base)
    # lldpd is a subordinate; it takes no units of its own (they come from the
    # principal relation), so num_units is left unset for it.
    juju.deploy(lldpd_charm, "lldpd", base=charm_base)

    juju.integrate("ubuntu:juju-info", "lldpd:juju-info")
    juju.wait(
        lambda status: jubilant.all_active(status, "ubuntu", "lldpd"),
        error=jubilant.any_error,
        timeout=1800,
    )


@pytest.mark.order(2)
def test_lldpd_is_active(juju: jubilant.Juju) -> None:
    """Test that the lldpd services are active in each juju unit."""
    logger.info("Validating that lldpd is active inside each juju unit.")
    status = juju.status()
    # lldpd is a subordinate, so its units live under the principal's units in
    # status; get_units() resolves them via subordinate_to.
    units = status.get_units("lldpd")
    assert (
        len(units) == NUM_UNITS
    ), f"expected {NUM_UNITS} lldpd units, got {len(units)}"
    for unit in units:
        result = juju.ssh(unit, "systemctl is-active lldpd").strip()
        assert result == "active", f"{unit} lldpd is not active"
