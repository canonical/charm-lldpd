#!/usr/bin/env python3
# Copyright 2020 Canonical Ltd.
#
# This file is part of the lldpd charm for Juju.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Main Charm module."""

import logging
import os
import subprocess
from typing import cast

from ops.charm import CharmBase, RelationChangedEvent, RelationJoinedEvent
from ops.framework import EventSource, ObjectEvents, StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus
from charms.operator_libs_linux.v0 import apt
from charms.operator_libs_linux.v0.systemd import service_reload
from pathlib import Path

PACKAGES = ["lldpd"]
PATHS = {
    "lldpddef": "/etc/default/lldpd",
    "lldpdconf": "/etc/lldpd.conf",
}
logger = logging.getLogger(__name__)


class LldpCharmEvents(ObjectEvents):
    """Declare relation-specific events for the type checker."""

    nrpe_external_master_relation_changed = EventSource(RelationChangedEvent)
    nrpe_external_master_relation_joined = EventSource(RelationJoinedEvent)


class LldpdCharm(CharmBase):
    """Charm to deploy and manage lldpd"""

    state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self.on_upgrade_charm)
        self.framework.observe(self.on.upgrade_charm, self.on_upgrade_charm)
        self.framework.observe(self.on.config_changed, self.on_config_changed)
        self.framework.observe(
            cast(LldpCharmEvents, self.on).nrpe_external_master_relation_changed,
            self.on_nrpe_external_master_relation_changed,
        )
        self.framework.observe(
            cast(LldpCharmEvents, self.on).nrpe_external_master_relation_joined,
            self.on_nrpe_external_master_relation_changed,
        )

    def on_upgrade_charm(self, event):
        """Install lldpd package."""
        logger.info("Installing lldpd.")
        self.unit.status = MaintenanceStatus("Installing packages")
        self.install()
        self.state.ready = True

    def on_config_changed(self, event):
        """Base config-changed hook."""
        if not self.state.ready:
            event.defer()
            return
        logger.info("Running config-changed")
        self.unit.status = MaintenanceStatus("Updating configuration")
        self.configure()

    def on_nrpe_external_master_relation_changed(self, event):
        self.setup_nrpe()
        # TODO get this working for config-changed, but only if relation exists

    def install(self):
        apt.update()
        apt.add_package(PACKAGES)

    @property
    def machine_id(self):
        return os.environ.get("JUJU_MACHINE_ID", None)

    def configure(self):
        """Base config-changed hook."""
        config = self.model.config

        # handle the side effects first
        if config["i40e-lldp-stop"]:
            self.disable_i40e_lldp()
        if config["short-name"]:
            self.update_short_name()

        args = []
        if config["systemid-from-interface"]:
            args.append("-C {}".format(config["systemid-from-interface"]))
        if config["interfaces-regex"]:
            args.append("-I {}".format(config["interfaces-regex"]))
        if config["enable-snmp"]:
            args.append("-x")
        if self.machine_id:
            args.append("-S juju_machine_id={}".format(self.machine_id))

        with open(PATHS["lldpddef"], "w") as conf:
            conf.write('DAEMON_ARGS="{}"\n'.format(" ".join(args)))
        service_reload("lldpd", restart_on_failure=True)
        self.framework.model.unit.status = ActiveStatus("ready")

    def disable_i40e_lldp(self):
        """Disable i40e."""
        I40E_DRIVER_NAME = "i40e"

        def i40e_filter(path: Path) -> bool:
            """Filter for devices using i40e driver."""
            if not path or not path.exists():
                return False
            driver = path / "device/driver"
            if not driver.exists() or not driver.is_symlink():
                return False
            return I40E_DRIVER_NAME == driver.resolve(strict=True).name

        nics = [
            device.name
            for device in filter(i40e_filter, Path("/sys/class/net").iterdir())
        ]

        if not nics:
            logger.info(
                "Can't find any i40e NICs. Recommend setting the charm config i40e-lldp-stop to false"
            )
            return

        for nic in nics:
            logger.info("Using ethtool(8) to disable FW lldp for %s" % nic)
            subprocess.run(
                [
                    "sudo",
                    "/usr/sbin/ethtool",
                    "--set-priv-flags",
                    nic,
                    "disable-fw-lldp",
                    "on",
                ],
                check=True,
            )

    def update_short_name(self):
        """Add system shortname to lldpd."""
        shortname = os.uname()[1]
        with open(PATHS["lldpdconf"], "w") as f:
            f.write("configure system hostname {}\n".format(str(shortname)))

    def setup_nrpe(self):
        ## FIXME use ops-lib-nrpe
        pass


if __name__ == "__main__":
    main(LldpdCharm)
