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
import sys
import subprocess

sys.path.insert(0, "lib/")  # noqa: E402


from ops.charm import CharmBase  # noqa: E402
from ops.framework import StoredState  # noqa: E402
from ops.main import main  # noqa: E402
from ops.model import ActiveStatus, MaintenanceStatus  # noqa: E402
from charms.operator_libs_linux.v0 import apt
from charms.operator_libs_linux.v0.systemd import service_running, service_reload

PACKAGES = ["lldpd"]
PATHS = {
    'lldpddef': "/etc/default/lldpd",
    'lldpdconf': "/etc/lldpd.conf",
}
logger = logging.getLogger(__name__)


class LldpdCharm(CharmBase):
    """Charm to deploy and manage lldpd"""

    state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self.on_upgrade_charm)
        self.framework.observe(self.on.upgrade_charm, self.on_upgrade_charm)
        self.framework.observe(self.on.config_changed, self.on_config_changed)
        self.framework.observe(
            self.on.nrpe_external_master_relation_changed,
            self.on_nrpe_external_master_relation_changed,
        )
        self.framework.observe(
            self.on.nrpe_external_master_relation_joined,
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
        noop = True

    def configure(self):
        """Base config-changed hook."""
        configs = self.model.config
        if "i40e-lldp-stop" in configs:
            self.disable_i40e_lldp()
        conf = open(PATHS["lldpddef"], "w")
        args = ['DAEMON_ARGS="']
        if configs.get("systemid-from-interface"):
            args.append("-C {} ".format(
                str(configs["systemid-from-interface"])))
        if configs.get("interfaces-regex"):
            args.append("-I {} ".format(str(configs["interfaces-regex"])))
        if configs.get("enable-snmp"):
            args.append("-x ")
        if configs.get("short-name"):
            self.short_name()
        machine_id = os.environ["JUJU_MACHINE_ID"]
        if machine_id:
            args.append("-S juju_machine_id={}".format(str(machine_id)))
        args.append('"\n')
        conf.write("".join(args))
        conf.close()
        service_reload("lldpd", restart_on_failure=True)
        self.framework.model.unit.status = ActiveStatus("ready")

    def disable_i40e_lldp(self):
        """Disable i40e."""
        getnics = "stat --format '%N' /sys/class/net/*/device/driver | grep 'drivers/i40e' | cut -d/ -f 5"
        nics = subprocess.check_output(getnics, shell=True)

        if nics == "":
            logger.info("Can't find any i40e NICs in kern.log")
            exit(0)

        for nic in nics.decode('UTF-8').splitlines():
            logger.info("Using ethtool(8) to disable FW lldp for %s" % nic)
            subprocess.run(['sudo', '/usr/sbin/ethtool', '--set-priv-flags', nic, 'disable-fw-lldp', 'on'])
            
    def short_name(self):
        """Add system shortname to lldpd."""
        shortname = os.uname()[1]
        cmd = open(PATHS["lldpdconf"], "w")
        cmd.write("configure system hostname {}\n".format(str(shortname)))
        cmd.close()

    def setup_nrpe(self):
        ## FIXME use ops-lib-nrpe
        nop = 0

if __name__ == "__main__":
    main(LldpdCharm)
