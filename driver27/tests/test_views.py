from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, Client, RequestFactory

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


    def test_spider_admin(self):
        client = Client()
        client.login(username='admin', password='pass')
        admin_pages = [
            # put all the admin pages for your models in here.
            "/admin/driver27/circuit/",
            "/admin/driver27/competition/",
            "/admin/driver27/driver/",
            "/admin/driver27/grandprix/",
            "/admin/driver27/race/",
            "/admin/driver27/season/",
            "/admin/driver27/seat/",
            "/admin/driver27/team/",

            "/admin/driver27/circuit/1/change/",
            "/admin/driver27/competition/1/change/",
            "/admin/driver27/driver/1/change/",
            "/admin/driver27/grandprix/1/change/",
            "/admin/driver27/race/1/change/",
            "/admin/driver27/season/1/change/",
            "/admin/driver27/seat/1/change/",
            "/admin/driver27/team/1/change/",

            "/admin/driver27/circuit/add/",
            "/admin/driver27/competition/add/",
            "/admin/driver27/driver/add/",
            "/admin/driver27/grandprix/add/",
            "/admin/driver27/race/add/",
            "/admin/driver27/season/add/",
            "/admin/driver27/seat/add/",
            "/admin/driver27/team/add/",
        ]
        for page in admin_pages:
            resp = client.get(page, follow=True)
            print(page)
            print(resp.status_code)
            assert resp.status_code == 200
            assert "<!DOCTYPE html" in resp.content