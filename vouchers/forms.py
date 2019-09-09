from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import Voucher, VoucherUser, Campaign
from .settings import VOUCHER_TYPES

class VoucherGenerationForm(forms.Form):
    quantity = forms.IntegerField(label=_("Quantity"))
    value = forms.IntegerField(label=_("Voucher Code"))
    type = forms.ChoiceField(label=_("Type"), choices=VOUCHER_TYPES)
    valid_until = forms.SplitDateTimeField(
        label=_("Valid until"), required=False,
        help_text=_("Note: Leave empty for vouchers that never expire")
    )
    prefix = forms.CharField(label="Prefix", required=False)
    campaign = forms.ModelChoiceField(
        label=_("Campaign"), queryset=Campaign.objects.all(), required=False
    )

class VoucherForm(forms.Form):
    code = forms.CharField(label=_("Voucher code"))

    def __init__(self, *args, **kwargs):
        self.user = None
        self.types = None
        if 'user' in kwargs:
            self.user = kwargs['user']
            del kwargs['user']
        if 'types' in kwargs:
            self.types = kwargs['types']
            del kwargs['types']
        super(VoucherForm, self).__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data['code']
        try:
            voucher = Voucher.objects.get(code=code)
        except Voucher.DoesNotExist:
            raise forms.ValidationError(_("This code is not valid."))
        self.voucher = voucher

        if self.user is None and voucher.user_limit is not 1:
            # vouchers with can be used only once can be used without tracking the user, otherwise there is no chance
            # of excluding an unknown user from multiple usages.
            raise forms.ValidationError(_(
                "The server must provide an user to this form to allow you to use this code. Maybe you need to sign in?"
            ))

        if voucher.is_redeemed:
            raise forms.ValidationError(_("This code has already been used."))

        try:  # check if there is a user bound voucher existing
            user_voucher = voucher.users.get(user=self.user)
            if user_voucher.redeemed_at is not None:
                raise forms.ValidationError(_("This code has already been used by your account."))
        except VoucherUser.DoesNotExist:
            if voucher.user_limit is not 0:  # zero means no limit of user count
                # only user bound vouchers left and you don't have one
                if voucher.user_limit is voucher.users.filter(user__isnull=False).count():
                    raise forms.ValidationError(_("This code is not valid for your account."))
                if voucher.user_limit is voucher.users.filter(redeemed_at__isnull=False).count():  # all vouchers redeemed
                    raise forms.ValidationError(_("This code has already been used."))
        if self.types is not None and voucher.type not in self.types:
            raise forms.ValidationError(_("This code is not meant to be used here."))
        if voucher.expired():
            raise forms.ValidationError(_("This code is expired."))
        return code
