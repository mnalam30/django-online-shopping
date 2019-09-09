from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import TestCase
from vouchers.forms import VoucherGenerationForm, VoucherForm
from vouchers.models import Voucher, VoucherUser

class VoucherGenerationFormTestCase(TestCase):
    def test_form(self):
        form_data = {'quantity': 23, 'value': 42, 'type': 'monetary'}
        form = VoucherGenerationForm(data=form_data)
        self.assertTrue(form.is_valid())

class VoucherFormTestCase(TestCase):
    def setUp(self):
        self.user = User(username="user1")
        self.user.save()
        self.voucher = Voucher.objects.create_voucher('monetary', 100, self.user)

    def test_wrong_code(self):
        form_data = {'code': 'foo'}
        form = VoucherForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_right_code(self):
        form_data = {'code': self.voucher.code}
        form = VoucherForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_types(self):
        form_data = {'code': self.voucher.code}
        form = VoucherForm(data=form_data, user=self.user, types=('percentage',))
        self.assertFalse(form.is_valid())

    def test_user(self):
        other_user = User(username="user2")
        other_user.save()
        form_data = {'code': self.voucher.code}
        form = VoucherForm(data=form_data, user=other_user)
        self.assertFalse(form.is_valid())

    def test_reuse(self):
        self.voucher.redeem()
        self.voucher.save()

        form_data = {'code': self.voucher.code}
        form = VoucherForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_expired(self):
        self.voucher.valid_until = timezone.now() - timedelta(1)
        self.voucher.save()
        form_data = {'code': self.voucher.code}
        form = VoucherForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

class UnboundVoucherFormTestCase(TestCase):
    def setUp(self):
        self.user = User(username="user1")
        self.user.save()
        self.voucher = Voucher.objects.create_voucher('monetary', 100)

    def test_none_voucher_user(self):
        VoucherUser.objects.create(voucher=self.voucher)
        self.assertTrue(self.voucher.users.count(), 1)
        self.assertIsNone(self.voucher.users.first().user)
        self.assertIsNone(self.voucher.users.first().redeemed_at)

        form_data = {'code': self.voucher.code}
        form = VoucherForm(data=form_data, user=self.user)

        self.assertTrue(form.is_valid())
