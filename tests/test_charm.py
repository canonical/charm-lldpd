# Copyright 2022 Tilman Baumann
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest.mock import Mock

from charm import LldpdCharm
from ops.model import ActiveStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(LldpdCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
