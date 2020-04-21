import os

from mock import patch

from ops.charm import (
    ConfigChangedEvent,
    RelationChangedEvent,
)

import shutil
import tempfile
import unittest

import charm
from ops.charm import UpgradeCharmEvent
from ops.testing import Harness

os.environ['JUJU_UNIT_NAME'] = 'lldpd'
os.environ['CHARM_DIR'] = '..'
os.environ['JUJU_MACHINE_ID'] = '1'


class HarnessTestBase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.harness = Harness(charm.LldpdCharm)
        self.harness.set_leader(is_leader=True)
        nrpe_relation = self.harness.add_relation('nrpe-external-master',
                                                  'ubuntu')
        self.harness.add_relation_unit(nrpe_relation, 'ubuntu/0')
        charm.PATHS = {
            "lldpdconf": os.path.join(self.tempdir, "test_lldpd.conf"),
            "lldpddef": os.path.join(self.tempdir, "test_etc_default_lldpd"),
        }

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def start_app(self):
        self.harness.begin()
        self.run_install_time_hooks()

    def run_install_time_hooks(self):
        """Runs a few common hooks which would fire on a freshly-installed unit.

        The operator framework Harness, upon calling begin(), doesn't
        automatically fire any hooks.  This is a good thing for the purpose of
        unit testing, but if you're testing a part of a charm that depends on
        other hooks having fired, you may be surprised if those hooks are not
        fired automatically.  This function provides the hooks which this charm
        would fire if it were freshly installed.

        Note: This is not intelligent. It does not fire any leader nor relation
        hooks, even if they normally would be triggered.  You will need to call
        those handlers yourself if necessary.

        """
        self.harness.charm.on_upgrade_charm(
            UpgradeCharmEvent(self.harness.framework))
        # Other hooks which may commonly fire at initial startup, if we care to
        # implement them:
        # - start
        # - leader-elected
        # - leader-settings-changed
        # - update-status
        # - relation hooks for already-established relations
        # Anything else that gets fired right away?

    @patch("charmhelpers.core.host.service_restart")
    @patch("charmhelpers.fetch.apt_update")
    @patch("charmhelpers.fetch.apt_install")
    @patch("charmhelpers.contrib.charmsupport.nrpe.NRPE")
    @patch("charmhelpers.contrib.charmsupport.nrpe.get_nagios_hostname")
    @patch("charmhelpers.contrib.charmsupport.nrpe.get_nagios_unit_name")
    @patch("charmhelpers.contrib.charmsupport.nrpe.add_init_service_checks")
    def test_configure_nrpe(
        self,
        mock_init_service_checks,
        mock_get_nagios_unit_name,
        mock_get_nagios_hostname,
        mock_nrpe,
        mock_apt_install,
        mock_apt_update,
        mock_service_restart,
    ):

        mock_get_nagios_hostname.return_value = "foohostname"
        mock_get_nagios_unit_name.return_value = "ubuntu/0"

        self.start_app()
        self.harness.charm.on_nrpe_external_master_relation_changed(
            RelationChangedEvent(self.harness.framework, 'ubuntu/0'))
        self.harness.charm.on_config_changed(
            ConfigChangedEvent(self.harness.framework))
        assert mock_nrpe.called_with("write")
        assert mock_init_service_checks.called_with(["lldpd"])
