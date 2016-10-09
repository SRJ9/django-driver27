from django.test import TestCase
from django.core.exceptions import ValidationError

# Create your tests here.
from driver27.models import Circuit, GrandPrix, Competition

class GrandPrixTestCase(TestCase):

    fixtures = ['circuits-2016.json', 'competition.json']

    def setUp(self):
        GrandPrix.objects.create(name="Australian Grand Prix", country="AU", first_held="1928")

    def test_gp_circuit_relation(self):
        """ Test if grand_prix__default_circuit relation not broken
        """

        circuit = Circuit.objects.get(pk=1)
        grand_prix = GrandPrix.objects.get(name='Australian Grand Prix')
        grand_prix.default_circuit = circuit
        grand_prix.save()

        grand_prix_saved = GrandPrix.objects.get(pk=grand_prix.pk)
        # Melbourne GP Circuit opened in 1953
        self.assertEqual(grand_prix_saved.default_circuit.opened_in, 1953)
