from django.test import TestCase
from django.core.exceptions import ValidationError

# Create your tests here.
from driver27.models import Driver

class DriverTestCase(TestCase):

    @staticmethod
    def get_test_driver_A():
        return {'last_name':'McQueen', 'first_name':'Lightning', 'year_of_birth': 2105, 'country':'US'}

    @staticmethod
    def get_test_driver_B():
        return {'last_name':'Frederick', 'first_name':'Flintstone', 'year_of_birth': 1884, 'country':'US'}

    @staticmethod
    def get_test_driver_C():
        return {'last_name':'Fangio', 'first_name':'Manuel', 'year_of_birth': 2000, 'country':'AR'}

    def test_check_year_of_birth(self):
        """ Check year_of_birth limits"""
        self.assertRaises(ValidationError, Driver.objects.create, **self.get_test_driver_A())
        self.assertRaises(ValidationError, Driver.objects.create, **self.get_test_driver_B())
        self.assertTrue(Driver.objects.create(**self.get_test_driver_C()))

