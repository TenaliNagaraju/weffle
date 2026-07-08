from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def customer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('shop:login')
        if request.user.is_shop_admin:
            return redirect('shop:admin_dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Admin login required.')
            return redirect('shop:login')
        if not request.user.is_shop_admin:
            messages.error(request, 'Access denied. Admin only.')
            return redirect('shop:dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


def delivery_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_delivery_agent:
            messages.error(request, 'Delivery agent access only.')
            return redirect('shop:login')
        return view_func(request, *args, **kwargs)

    return wrapper
