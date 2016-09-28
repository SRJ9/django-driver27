from django.test import TestCase
from django.core.exceptions import ValidationError

class ZeroTestCase(TestCase):

    fixtures = ['circuits-2016.json', 'competition.json', 'drivers-2016.json', 'grands-prix.json',
    'seasons-2016.json', 'teams-2016.json']

    def test_okey(self):
        print('Se han cargado todos los fixtures')