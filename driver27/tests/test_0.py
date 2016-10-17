from django.test import TestCase
from django.core.exceptions import ValidationError
from driver27.models import Driver

class ZeroTestCase(TestCase):

    fixtures = ['circuits-2016.json', 'competition.json', 'drivers-2016.json', 'grands-prix.json',
    'seasons-2016.json', 'teams-2016.json', 'driver-competition-2016.json', 'driver-competition-team-2016.json',
    'races-2016.json']

    def test_okey(self):
        print('Se han cargado todos los fixtures')

    def test_driver_unicode(self):
        hamilton = Driver.objects.get(last_name='Hamilton', first_name='Lewis')
        expected_unicode = ', '.join(('Hamilton', 'Lewis'))
        self.assertEquals("%s" % hamilton, expected_unicode)

    def test_driver_save_exception(self):
        emmet_brown = {"last_name": "Brown", "first_name": "Emmet", "year_of_birth": 1885}
        self.assertRaises(ValidationError, Driver.objects.create, **emmet_brown)
        emmet_brown['year_of_birth'] = 1985
        self.assertTrue(Driver.objects.create(**emmet_brown))