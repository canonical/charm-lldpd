# Copyright 2022 Tilman Baumann
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
import os
from unittest.mock import patch, mock_open, MagicMock, PropertyMock

from charm import LldpdCharm, PACKAGES
from ops.testing import Harness
from pathlib import Path


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(LldpdCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    @patch("charm.Path")
    @patch("charm.subprocess.run")
    @patch("charm.logger")
    def test_disable_i40e_lldp_without_i40e_nics(
        self, mock_logger, mock_subprocess, mock_path
    ):
        mock_path("/sys/class/net").iterdir.return_value = []

        self.harness.charm.disable_i40e_lldp()

        mock_logger.info.assert_called_with(
            "Can't find any i40e NICs. Recommend setting the charm config i40e-lldp-stop to false"
        )
        mock_subprocess.assert_not_called()

    @patch("charm.Path")
    @patch("charm.shutil.which")
    @patch("charm.subprocess.run")
    @patch("charm.logger")
    def test_disable_i40e_lldp_with_i40e_nics(
        self, mock_logger, mock_subprocess, mock_which, mock_path
    ):
        mock_which.return_value = "/usr/sbin/ethtool"

        nic_list = ["eth0", "eth1"]
        mock_nics = []
        for nic_name in nic_list:
            mock_nic = MagicMock()
            mock_nic.name = nic_name
            mock_driver = mock_nic / "device/driver"
            mock_driver.resolve.return_value = Path(
                "/sys/class/net/{nic_name}/device/driver/i40e"
            )
            mock_nics.append(mock_nic)

        mock_path("/sys/class/net").iterdir.return_value = mock_nics

        self.harness.charm.disable_i40e_lldp()

        expected_calls = [
            unittest.mock.call(
                [
                    "sudo",
                    "/usr/sbin/ethtool",
                    "--set-priv-flags",
                    nic_name,
                    "disable-fw-lldp",
                    "on",
                ],
                check=True,
            )
            for nic_name in nic_list
        ]

        mock_subprocess.assert_has_calls(expected_calls, any_order=True)

        for nic_name in nic_list:
            mock_logger.info.assert_any_call(
                f"Using ethtool(8) to disable FW lldp for {nic_name}"
            )

    @patch("charm.Path")
    @patch("charm.shutil.which")
    @patch("charm.subprocess.run")
    @patch("charm.logger")
    def test_disable_i40e_lldp_no_ethtool(
        self, mock_logger, mock_subprocess, mock_which, mock_path
    ):
        mock_which.return_value = None

        nic_list = ["eth0", "eth1"]
        mock_nics = []

        for nic_name in nic_list:
            mock_nic = MagicMock()
            mock_nic.name = nic_name
            mock_driver = mock_nic / "device/driver"
            mock_driver.resolve.return_value = Path(
                "/sys/class/net/{nic_name}/device/driver/i40e"
            )
            mock_nics.append(mock_nic)

        mock_path("/sys/class/net").iterdir.return_value = mock_nics

        self.harness.charm.disable_i40e_lldp()

        mock_logger.info.assert_any_call("ethtool not found in PATH")

        mock_subprocess.assert_not_called()

    @patch("charm.apt")
    def test_install(self, _apt):
        self.harness.charm.on.install.emit()
        _apt.update.assert_called_once()
        _apt.add_package.assert_called_once_with(PACKAGES)

    @patch("charm.LldpdCharm.install")
    def test_upgrade_charm(self, _install):
        self.harness.charm.state.ready = False
        evt = MagicMock()
        self.harness.charm.on_upgrade_charm(evt)
        _install.assert_called_once()
        self.assertTrue(self.harness.charm.state.ready)

    @patch("charm.LldpdCharm.configure")
    def test_config_changed(self, _configure):
        # When the state is not ready, then the event is deferred
        self.harness.charm.state.ready = False
        self.harness.update_config({"short-name": True})
        _configure.assert_not_called()

        self.harness.charm.state.ready = True
        self.harness.update_config({"short-name": False})
        _configure.assert_called_once()

    def _test_configure_helper(self, config: dict, args: str) -> None:
        self.harness.disable_hooks()
        if config:
            self.harness.update_config(config)

        m = mock_open()
        svc_reload = patch("charm.service_reload").start()
        disable_i40e = patch.object(self.harness.charm, "disable_i40e_lldp").start()
        with patch("builtins.open", m):
            self.harness.charm.configure()

        if self.harness.charm.config["i40e-lldp-stop"]:
            disable_i40e.assert_called_once()
        else:
            disable_i40e.assert_not_called()

        m.assert_called_once_with("/etc/default/lldpd", "w")
        handle = m()
        handle.write.assert_called_once_with(f'DAEMON_ARGS="{args}"\n')
        svc_reload.assert_called_once()

    def test_configure_defaults(self):
        self._test_configure_helper(dict(), "")

    def test_configure_no_disable_i40e_lldp(self):
        # disable hooks
        self._test_configure_helper(
            {
                "i40e-lldp-stop": False,
            },
            "",
        )

    def test_configure_systemid_from_interface(self):
        config = {
            "i40e-lldp-stop": False,
            "systemid-from-interface": "eth0",
        }
        self._test_configure_helper(config, "-C eth0")

    def test_configure_interfaces_regex(self):
        config = {
            "i40e-lldp-stop": False,
            "interfaces-regex": "eth*",
        }
        self._test_configure_helper(config, "-I eth*")

    def test_configure_enable_snmp(self):
        config = {"enable-snmp": True}
        self._test_configure_helper(config, "-x")

        config = {"enable-snmp": False}
        self._test_configure_helper(config, "")

    @patch("charm.LldpdCharm.update_short_name")
    def test_configure_enable_short_name(self, _update_short_name):
        with patch(
            "charm.LldpdCharm.machine_id", new_callable=PropertyMock
        ) as mock_property:
            mock_property.return_value = "machine-id"
            config = {"short-name": True}
            self._test_configure_helper(config, "-S juju_machine_id=machine-id")

            # When there is no JUJU_MACHINE_ID, the defaults
            # are not updated.
            mock_property.return_value = None
            self._test_configure_helper(config, "")

    def test_configure_multiple_options(self):
        config = {"interfaces-regex": "eth*", "enable-snmp": True}
        self._test_configure_helper(config, "-I eth* -x")

    def test_update_short_name(self):
        hostname = os.uname()[1]
        m = mock_open()
        with patch("builtins.open", m):
            self.harness.charm.update_short_name()
        m.assert_called_once_with("/etc/lldpd.conf", "w")
        handle = m()
        handle.write.assert_called_once_with(f"configure system hostname {hostname}\n")
