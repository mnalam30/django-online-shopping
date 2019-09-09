import django

from distutils.version import StrictVersion
from unittest import skipIf
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from vouchers.admin import VoucherAdmin
from vouchers.models import Voucher

class MockRequest(object):
    pass

request = MockRequest()

class VoucherAdminTestCase(TestCase):
    def setUp(self):
        self.site = AdminSite()

    @skipIf(StrictVersion(django.get_version()) < StrictVersion('1.7'), "Skip list display test due to missing method.")
    def test_list_display(self):
        admin = VoucherAdmin(Voucher, self.site)

        self.assertEquals(
            list(admin.get_fields(request)),
            ['value', 'code', 'type', 'user_limit', 'valid_until', 'campaign']
        )
