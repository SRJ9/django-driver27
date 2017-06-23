# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core.exceptions import ValidationError
from .common import retro_encode, CommonDriverTestCase
from ..models import Driver


class DriverTestCase(TestCase, CommonDriverTestCase):
    def test_driver_unicode(self):
        driver = self.get_test_driver()
        expected_unicode = ', '.join((driver.last_name, driver.first_name))
        self.assertEquals(str(driver), retro_encode(expected_unicode))