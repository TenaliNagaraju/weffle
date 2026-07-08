from django.conf import settings

from .utils import cart_count


def site_settings(request):
    return {
        'SITE_NAME': settings.SITE_NAME,
        'CURRENCY': settings.CURRENCY_SYMBOL,
        'cart_count': cart_count(request) if request.user.is_authenticated else 0,
    }
