import random

from django.conf import settings
from django.db import IntegrityError
from django.db import models
from django.db.models import CASCADE
from django.dispatch import Signal
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .settings import (
    VOUCHER_TYPES,
    CODE_LENGTH,
    CODE_CHARS,
    SEGMENTED_CODES,
    SEGMENT_LENGTH,
    SEGMENT_SEPARATOR,
)

try:
    user_model = settings.AUTH_USER_MODEL
except AttributeError:
    from django.contrib.auth.models import User as user_model
redeem_done = Signal(providing_args=["voucher"])


class VoucherManager(models.Manager):
    def create_voucher(self, type, value, users=[], valid_until=None, prefix="", campaign=None, user_limit=None):
        voucher = self.create(
            value=value,
            code=Voucher.generate_code(prefix),
            type=type,
            valid_until=valid_until,
            campaign=campaign,
        )
        if user_limit is not None:  # otherwise use default value of model
            voucher.user_limit = user_limit
        try:
            voucher.save()
        except IntegrityError:
            # Try again with other code
            voucher = Voucher.objects.create_voucher(type, value, users, valid_until, prefix, campaign)
        if not isinstance(users, list):
            users = [users]
        for user in users:
            if user:
                VoucherUser(user=user, voucher=voucher).save()
        return voucher

    def create_vouchers(self, quantity, type, value, valid_until=None, prefix="", campaign=None):
        vouchers = []
        for i in range(quantity):
            vouchers.append(self.create_voucher(type, value, None, valid_until, prefix, campaign))
        return vouchers

    def used(self):
        return self.exclude(users__redeemed_at__isnull=True)

    def unused(self):
        return self.filter(users__redeemed_at__isnull=True)

    def expired(self):
        return self.filter(valid_until__lt=timezone.now())


@python_2_unicode_compatible
class Voucher(models.Model):
    value = models.IntegerField(_("Value"), help_text=_("Arbitrary voucher value"))
    code = models.CharField(
        _("Code"), max_length=30, unique=True, blank=True,
        help_text=_("Note: Leaving this field empty will generate a random code."))
    type = models.CharField(_("Type"), max_length=20, choices=VOUCHER_TYPES)
    user_limit = models.PositiveIntegerField(_("User limit"), default=1)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    valid_until = models.DateTimeField(
        _("Valid until"), blank=True, null=True,
        help_text=_("Note: Leave empty for vouchers that never expire"))
    campaign = models.ForeignKey('Campaign', verbose_name=_("Campaign"), on_delete=CASCADE, blank=True, null=True, related_name='vouchers')

    objects = VoucherManager()

    class Meta:
        ordering = ['created_at']
        verbose_name = _("Voucher")
        verbose_name_plural = _("Vouchers")

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = Voucher.generate_code()
        super(Voucher, self).save(*args, **kwargs)

    def expired(self):
        return self.valid_until is not None and self.valid_until < timezone.now()

    @property
    def is_redeemed(self):
        """ Returns true is a voucher is redeemed (completely for all users) otherwise returns false. """
        return self.users.filter(
            redeemed_at__isnull=False
        ).count() >= self.user_limit and self.user_limit is not 0

    @property
    def redeemed_at(self):
        try:
            return self.users.filter(redeemed_at__isnull=False).order_by('redeemed_at').last().redeemed_at
        except self.users.through.DoesNotExist:
            return None

    @classmethod
    def generate_code(cls, prefix="", segmented=SEGMENTED_CODES):
        code = "".join(random.choice(CODE_CHARS) for i in range(CODE_LENGTH))
        if segmented:
            code = SEGMENT_SEPARATOR.join([code[i:i + SEGMENT_LENGTH] for i in range(0, len(code), SEGMENT_LENGTH)])
            return prefix + code
        else:
            return prefix + code

    def redeem(self, user=None):
        try:
            voucher_user = self.users.get(user=user)
        except VoucherUser.DoesNotExist:
            try:  # silently fix unbouned or nulled voucher users
                voucher_user = self.users.get(user__isnull=True)
                voucher_user.user = user
            except VoucherUser.DoesNotExist:
                voucher_user = VoucherUser(voucher=self, user=user)
        voucher_user.redeemed_at = timezone.now()
        voucher_user.save()
        redeem_done.send(sender=self.__class__, voucher=self)


@python_2_unicode_compatible
class Campaign(models.Model):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class VoucherUser(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=CASCADE, related_name='users')
    user = models.ForeignKey(user_model, verbose_name=_("User"), on_delete=CASCADE, null=True, blank=True)
    redeemed_at = models.DateTimeField(_("Redeemed at"), blank=True, null=True)

    class Meta:
        unique_together = (('voucher', 'user'),)

    def __str__(self):
        return str(self.user)
