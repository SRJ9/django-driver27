# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils.translation import ugettext as _
from .common import CommonContenderTestCase, retro_encode


class ContenderTestCase(TestCase, CommonContenderTestCase):
    def test_contender_unicode(self):
        contender = self.get_test_contender()
        expected_str = _(u'%(driver)s in %(competition)s') % {'driver': contender.driver,
                                                              'competition': contender.competition}
        self.assertEquals(str(contender), retro_encode(expected_str))

    def test_contender_team(self):
        contender = self.get_test_contender()
        self.assertEquals(contender.teams_verbose, None)
