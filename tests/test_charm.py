# Copyright 2022 Tilman Baumann
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import Mock, patch, MagicMock

from charm import LldpdCharm
from ops.model import ActiveStatus
from ops.testing import Harness
from pathlib import Path


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(LldpdCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_config_changed(self):
        self.assertEqual(list(self.harness.charm._stored.things), [])
        self.harness.update_config({"thing": "foo"})
        self.assertEqual(list(self.harness.charm._stored.things), ["foo"])

    def test_action(self):
        # the harness doesn't (yet!) help much with actions themselves
        action_event = Mock(params={"fail": ""})
        self.harness.charm._on_fortune_action(action_event)

        self.assertTrue(action_event.set_results.called)

    def test_action_fail(self):
        action_event = Mock(params={"fail": "fail this"})
        self.harness.charm._on_fortune_action(action_event)

        self.assertEqual(action_event.fail.call_args, [("fail this",)])

    def test_httpbin_pebble_ready(self):
        # Simulate making the Pebble socket available
        self.harness.set_can_connect("httpbin", True)
        # Check the initial Pebble plan is empty
        initial_plan = self.harness.get_container_pebble_plan("httpbin")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Expected plan after Pebble ready with default config
        expected_plan = {
            "services": {
                "httpbin": {
                    "override": "replace",
                    "summary": "httpbin",
                    "command": "gunicorn -b 0.0.0.0:80 httpbin:app -k gevent",
                    "startup": "enabled",
                    "environment": {"thing": "🎁"},
                }
            },
        }
        # Get the httpbin container from the model
        container = self.harness.model.unit.get_container("httpbin")
        # Emit the PebbleReadyEvent carrying the httpbin container
        self.harness.charm.on.httpbin_pebble_ready.emit(container)
        # Get the plan now we've run PebbleReady
        updated_plan = self.harness.get_container_pebble_plan("httpbin").to_dict()
        # Check we've got the plan we expected
        self.assertEqual(expected_plan, updated_plan)
        # Check the service was started
        service = self.harness.model.unit.get_container("httpbin").get_service("httpbin")
        self.assertTrue(service.is_running())
        # Ensure we set an ActiveStatus with no message
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

    @patch('charm.Path')
    @patch('charm.subprocess.run')
    @patch('charm.logger')
    def test_disable_i40e_lldp_without_i40e_nics(self, mock_logger, mock_subprocess, mock_path):
        mock_path("/sys/class/net").iterdir.return_value = []

        with self.assertRaises(SystemExit) as cm:
            self.harness.charm.disable_i40e_lldp()

        self.assertEqual(cm.exception.code, 0)
        mock_logger.info.assert_called_with("Can't find any i40e NICs. Recommend setting the charm config i40e-lldp-stop to false")
        mock_subprocess.assert_not_called()

    @patch('charm.Path')
    @patch('charm.subprocess.run')
    @patch('charm.logger')
    def test_disable_i40e_lldp_with_i40e_nics(self, mock_logger, mock_subprocess, mock_path):

        nic_list = ["eth0", "eth1"]
        mock_nics = []
        for nic_name in nic_list:
            mock_nic = MagicMock()
            mock_nic.name = nic_name
            mock_driver = mock_nic / "device/driver"
            mock_driver.resolve.return_value = Path("/sys/class/net/{nic_name}/device/driver/i40e")
            mock_nics.append(mock_nic)

        mock_path("/sys/class/net").iterdir.return_value = mock_nics

        self.harness.charm.disable_i40e_lldp()

        expected_calls = [ unittest.mock.call([
            'sudo',
            '/usr/sbin/ethtool',
            '--set-priv-flags',
            nic_name,
            'disable-fw-lldp',
            'on'], check=True) for nic_name in nic_list]

        mock_subprocess.assert_has_calls(expected_calls, any_order=True)

        for nic_name in nic_list:
            mock_logger.info.assert_any_call(f"Using ethtool(8) to disable FW lldp for {nic_name}")
