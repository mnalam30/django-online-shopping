import re

from datetime import timedelta
from django.utils import timezone
from django.test import TestCase
from vouchers.models import Voucher, Campaign
from vouchers.settings import (
    CODE_LENGTH,
    CODE_CHARS,
    SEGMENT_LENGTH,
    SEGMENT_SEPARATOR,
)

class VoucherTestCase(TestCase):
    def test_generate_code(self):
        self.assertIsNotNone(re.match("^[%s]{%d}" % (CODE_CHARS, CODE_LENGTH,), Voucher.generate_code()))

    def test_generate_code_segmented(self):
        num_segments = CODE_LENGTH // SEGMENT_LENGTH  # full ones
        num_rest = CODE_LENGTH - num_segments * SEGMENT_LENGTH
        self.assertIsNotNone(
            re.match(
                "^([{chars}]{{{sl}}}{sep}){{{ns}}}[{chars}]{{{nr}}}$".format(
                    chars=CODE_CHARS,
                    sep=SEGMENT_SEPARATOR,
                    sl=SEGMENT_LENGTH,
                    ns=num_segments,
                    nr=num_rest),
                Voucher.generate_code("", True)
            )
        )

    def test_save(self):
        voucher = Voucher(type='monetary', value=100)
        voucher.save()
        self.assertTrue(voucher.pk)

    def test_create_voucher(self):
        voucher = Voucher.objects.create_voucher('monetary', 100)
        self.assertTrue(voucher.pk)

    def test_create_vouchers(self):
        vouchers = Voucher.objects.create_vouchers(50, 'monetary', 100)
        for voucher in vouchers:
            self.assertTrue(voucher.pk)

    def test_redeem(self):
        voucher = Voucher.objects.create_voucher('monetary', 100)
        voucher.redeem()
        self.assertIsNotNone(voucher.redeemed_at)

    def test_expired(self):
        voucher = Voucher.objects.create_voucher('monetary', 100)
        self.assertFalse(voucher.expired())
        self.assertEqual(Voucher.objects.expired().count(), 0)
        voucher.valid_until = timezone.now() - timedelta(1)
        voucher.save()
        self.assertTrue(voucher.expired())
        self.assertEqual(Voucher.objects.expired().count(), 1)

    def test_str(self):
        voucher = Voucher.objects.create_voucher('monetary', 100)
        self.assertEqual(voucher.code, str(voucher))

    def test_prefix(self):
        voucher = Voucher.objects.create_voucher('monetary', 100, None, None, "prefix-")
        self.assertTrue(voucher.code.startswith("prefix-"))

    def test_used_unused(self):
        voucher = Voucher.objects.create_voucher('monetary', 100)
        self.assertEqual(Voucher.objects.used().count(), 0)
        self.assertEqual(Voucher.objects.unused().count(), 1)
        voucher.redeem()
        voucher.save()
        self.assertEqual(Voucher.objects.used().count(), 1)
        self.assertEqual(Voucher.objects.unused().count(), 0)


class CampaignTestCase(TestCase):
    def test_str(self):
        campaign = Campaign(name="test")
        campaign.save()
        self.assertEqual("test", str(campaign))
