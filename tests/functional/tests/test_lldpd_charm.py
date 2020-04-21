import logging
import unittest

import zaza.model as model


class Test(unittest.TestCase):
    """Base for lldpd charm tests."""

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        cls.model_name = model.get_juju_model()
        cls.application_name = "lldpd"
        cls.lead_unit_name = model.get_lead_unit_name(
            cls.application_name, model_name=cls.model_name
        )
        cls.units = model.get_units(
            cls.application_name, model_name=cls.model_name
        )
        logging.debug("Leader unit is {}".format(cls.lead_unit_name))
