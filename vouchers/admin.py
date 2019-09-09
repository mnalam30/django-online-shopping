from django.conf.urls import url
from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from .forms import VoucherGenerationForm
from .models import Voucher, VoucherUser, Campaign

class VoucherUserInline(admin.TabularInline):
    model = VoucherUser
    extra = 0

    def get_max_num(self, request, obj=None, **kwargs):
        if obj:
            return obj.user_limit
        return None  # disable limit for new objects (e.g. admin add)

class VoucherAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'code', 'type', 'value', 'user_count', 'user_limit', 'is_redeemed', 'valid_until', 'campaign'
    ]
    list_filter = ['type', 'campaign', 'created_at', 'valid_until']
    raw_id_fields = ()
    search_fields = ('code', 'value')
    inlines = (VoucherUserInline,)
    exclude = ('users',)

    def user_count(self, inst):
        return inst.users.count()

    def get_urls(self):
        urls = super(VoucherAdmin, self).get_urls()
        my_urls = [
            url(r'generate-vouchers', self.admin_site.admin_view(GenerateVouchersAdminView.as_view()),
                name='generate_vouchers'),

        ]
        return my_urls + urls

class GenerateVouchersAdminView(TemplateView):
    template_name = 'site-admin/generate_vouchers.html'

    def get_context_data(self, **kwargs):
        context = super(GenerateVouchersAdminView, self).get_context_data(**kwargs)
        if self.request.method == 'POST':
            form = VoucherGenerationForm(self.request.POST)
            if form.is_valid():
                context['vouchers'] = Voucher.objects.create_vouchers(
                    form.cleaned_data['quantity'],
                    form.cleaned_data['type'],
                    form.cleaned_data['value'],
                    form.cleaned_data['valid_until'],
                    form.cleaned_data['prefix'],
                    form.cleaned_data['campaign'],
                )
                messages.success(self.request, _("Your vouchers have been generated."))
        else:
            form = VoucherGenerationForm()
        context['form'] = form
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'num_vouchers', 'num_vouchers_used', 'num_vouchers_unused', 'num_vouchers_expired']

    def num_vouchers(self, obj):
        return obj.vouchers.count()
    num_vouchers.short_description = _("vouchers")

    def num_vouchers_used(self, obj):
        return obj.vouchers.used().count()
    num_vouchers_used.short_description = _("used")

    def num_vouchers_unused(self, obj):
        return obj.vouchers.used().count()
    num_vouchers_unused.short_description = _("unused")

    def num_vouchers_expired(self, obj):
        return obj.vouchers.expired().count()
    num_vouchers_expired.short_description = _("expired")

admin.site.register(Voucher, VoucherAdmin)
admin.site.register(Campaign, CampaignAdmin)
