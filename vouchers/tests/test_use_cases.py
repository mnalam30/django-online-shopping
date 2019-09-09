from datetime import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from vouchers.forms import VoucherForm
from vouchers.models import Voucher

class DefaultVoucherTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.voucher = Voucher.objects.create_voucher('monetary', 100)

    def test_redeem(self):
        self.voucher.redeem(self.user)
        self.assertTrue(self.voucher.is_redeemed)
        self.assertEquals(self.voucher.users.count(), 1)
        self.assertIsInstance(self.voucher.users.first().redeemed_at, datetime)
        self.assertEquals(self.voucher.users.first().user, self.user)

    def test_redeem_via_form(self):
        form = VoucherForm(data={'code': self.voucher.code}, user=self.user)
        # form should be valid
        self.assertTrue(form.is_valid())
        # perform redeem
        self.voucher.redeem(self.user)
        # voucher should be redeemed properly now
        self.assertTrue(self.voucher.is_redeemed)
        self.assertEquals(self.voucher.users.count(), 1)
        self.assertIsInstance(self.voucher.users.first().redeemed_at, datetime)
        self.assertEquals(self.voucher.users.first().user, self.user)
        # form should be invalid after redeem
        self.assertTrue(form.is_valid())

    def test_redeem_via_form_without_user(self):
        form = VoucherForm(data={'code': self.voucher.code})
        # form should be valid
        self.assertTrue(form.is_valid())
        # perform redeem
        self.voucher.redeem()
        # voucher should be redeemed properly now
        self.assertTrue(self.voucher.is_redeemed)
        self.assertEquals(self.voucher.users.count(), 1)
        self.assertIsInstance(self.voucher.users.first().redeemed_at, datetime)
        self.assertIsNone(self.voucher.users.first().user)
        # form should be invalid after redeem
        self.assertTrue(form.is_valid())


class SingleUserVoucherTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.voucher = Voucher.objects.create_voucher('monetary', 100, self.user)

    def test_user_limited_voucher(self):
        self.assertEquals(self.voucher.users.count(), 1)
        self.assertEquals(self.voucher.users.first().user, self.user)
        # not redeemed yet
        self.assertIsNone(self.voucher.users.first().redeemed_at)

    def test_redeem_with_user(self):
        self.voucher.redeem(self.user)
        # voucher should be redeemed properly now
        self.assertTrue(self.voucher.is_redeemed)
        self.assertEquals(self.voucher.users.count(), 1)
        self.assertIsInstance(self.voucher.users.first().redeemed_at, datetime)
        self.assertEquals(self.voucher.users.first().user, self.user)

    def test_form_without_user(self):
        """ This should fail since the voucher is bound to an user, but we do not provide any user. """
        form = VoucherForm(data={'code': self.voucher.code})
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.errors,
            {'code': ['This code is not valid for your account.']}
        )

    def test_redeem_with_user_twice(self):
        self.test_redeem_with_user()
        # try to redeem again with form
        form = VoucherForm(data={'code': self.voucher.code}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.errors,
            {'code': ['This code has already been used.']}
        )

class UnlimitedVoucherTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")
        self.voucher = Voucher.objects.create_voucher('monetary', 100, user_limit=0)

    def test_redeem_with_user(self):
        self.voucher.redeem(self.user)
        # voucher is not redeemed since it can be used unlimited times
        self.assertFalse(self.voucher.is_redeemed)
        # voucher should be redeemed properly now
        self.assertEquals(self.voucher.users.count(), 1)
        self.assertIsInstance(self.voucher.users.first().redeemed_at, datetime)
        self.assertEquals(self.voucher.users.first().user, self.user)

    def test_redeem_with_multiple_users(self):
        for i in range(100):
            user = User.objects.create(username="test%s" % (i))
            form = VoucherForm(data={'code': self.voucher.code}, user=user)
            self.assertTrue(form.is_valid())

    def test_form_without_user(self):
        """ This should fail since we cannot track single use of a voucher without an user. """
        form = VoucherForm(data={'code': self.voucher.code})
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.errors,
            {'code': ['The server must provide an user to this form to allow you to use this code. Maybe you need to sign in?']}
        )

    def test_redeem_with_user_twice(self):
        self.test_redeem_with_user()
        # try to redeem again with form
        form = VoucherForm(data={'code': self.voucher.code}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.errors,
            {'code': ['This code has already been used by your account.']}
        )
