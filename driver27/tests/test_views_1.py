from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, Client, RequestFactory
from ..models import Season

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse


class MockRequest(object):
    pass


class MockSuperUser(object):
    def has_perm(self, perm):
        return True


def get_request():
    request = MockRequest()
    request.user = MockSuperUser()
    return request


def get_fixtures_test():
    # django test uses a new db, while pytest use transaction no_commit in the same settings db
    if hasattr(settings, 'PYTEST_SETTING') and settings.PYTEST_SETTING:
        return None
    else:
        return ['driver27.json']


class FixturesTest(TestCase):
    fixtures = get_fixtures_test()


class ViewTest(FixturesTest):

    def setUp(self):
        self.site = AdminSite()
        self.client = Client()
        self.factory = RequestFactory()

    # def test_spider_admin(self):
    #     client = Client()
    #     client.login(username='admin', password='pass')
    #     base_admin = '/admin/driver27'
    #     models = ['circuit', 'competition', 'driver', 'grandprix', 'race', 'season', 'seat', 'team']
    #     for model in models:
    #         url = base_admin + '/' + model + '/'
    #         resp = client.get(url, follow=True)
    #         self.assertEqual(resp.status_code, 200, url + ' code='+str(resp.status_code))
    #         url = base_admin + '/' + model + '/add/'
    #         resp = client.get(url, follow=True)
    #         self.assertEqual(resp.status_code, 200, url + ' code='+str(resp.status_code))
    #         url = base_admin + '/' + model + '/1/change/'
    #         resp = client.get(url, follow=True)
    #         self.assertEqual(resp.status_code, 200, url + ' code='+str(resp.status_code))

