# Copyright 2022 Tilman Baumann
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import patch, MagicMock

from charm import LldpdCharm
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
    @patch("charm.subprocess.run")
    @patch("charm.logger")
    def test_disable_i40e_lldp_with_i40e_nics(
        self, mock_logger, mock_subprocess, mock_path
    ):

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
