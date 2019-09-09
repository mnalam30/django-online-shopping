import string

from django.conf import settings

VOUCHER_TYPES = getattr(settings, 'VOUCHERS_VOUCHER_TYPES', (
    ('monetary', 'Ringgit Malaysia value discount'),
    ('percentage', 'Percentage-based discount'),
))

CODE_LENGTH = getattr(settings, 'VOUCHERS_CODE_LENGTH', 15)

CODE_CHARS = getattr(settings, 'VOUCHERS_CODE_CHARS', string.ascii_letters+string.digits)

SEGMENTED_CODES = getattr(settings, 'VOUCHERS_SEGMENTED_CODES', False)
SEGMENT_LENGTH = getattr(settings, 'VOUCHERS_SEGMENT_LENGTH', 4)
SEGMENT_SEPARATOR = getattr(settings, 'VOUCHERS_SEGMENT_SEPARATOR', "-")
