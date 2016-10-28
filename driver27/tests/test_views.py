from django.test import TestCase, Client
# from django.core.urlresolvers import reverse
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from ..models import Season, Competition

class ViewTest(TestCase):
    fixtures = ['circuits-2016.json', 'competition.json', 'drivers-2016.json', 'grands-prix.json',
    'seasons-2016.json', 'teams-2016.json', 'teams-season.json', 'driver-competition-2016.json', 'driver-competition-team-2016.json',
    'races-2016.json']
    def setUp(self):
        # Every test needs a client.
        self.client = Client()

    def test_competition_list(self):
        # Issue a GET request.
        response = self.client.get(reverse('competition-list'))

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

    def test_competition_view(self):
        # Issue a GET request.
        response = self.client.get(reverse('competition-view', kwargs={'competition_slug': 'f1'}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('competition-view', kwargs={'competition_slug': 'f19'}))
        # Check that the response is 404.
        self.assertEqual(response.status_code, 404)

    def test_season_view(self):
        # Issue a GET request.
        response = self.client.get(reverse('season-view', kwargs={'competition_slug': 'f1', 'year': 2016}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('season-driver', kwargs={'competition_slug': 'f1', 'year': 2016}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('season-team', kwargs={'competition_slug': 'f1', 'year': 2016}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('season-race-list', kwargs={'competition_slug': 'f1', 'year': 2016}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('season-view', kwargs={'competition_slug': 'f19', 'year': 2006}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 404)

    def test_race_view(self):
        # Issue a GET request.
        response = self.client.get(reverse('season-race-view', kwargs={'competition_slug': 'f1', 'year': 2016, 'race_id':1}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)
        # Issue a GET request.
        response = self.client.get(reverse('season-race-view', kwargs={'competition_slug': 'f1', 'year': 2016, 'race_id': 200}))
        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 404)

