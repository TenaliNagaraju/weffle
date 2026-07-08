from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Notification, Order, OrderItem, User


def get_cart(request):
    return request.session.get('cart', {})


def save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def cart_count(request):
    cart = get_cart(request)
    return sum(item.get('quantity', 0) for item in cart.values())


def cart_total(cart):
    total = Decimal('0')
    for item in cart.values():
        total += Decimal(str(item['price'])) * item['quantity']
    return total


def notify_user(user, title, message, notification_type='general', order=None):
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        order=order,
    )


def notify_admins(title, message, notification_type='admin', order=None):
    admins = User.objects.filter(role=User.ROLE_ADMIN, is_active=True)
    for admin in admins:
        notify_user(admin, title, message, notification_type, order)


def get_daily_analytics(date=None):
    if date is None:
        date = timezone.localdate()

    day_start = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.min.time()))
    day_end = day_start + timezone.timedelta(days=1)

    orders_today = Order.objects.filter(created_at__gte=day_start, created_at__lt=day_end)
    placed = orders_today.exclude(status=Order.STATUS_CANCELLED)
    cancelled = orders_today.filter(status=Order.STATUS_CANCELLED)
    revenue = placed.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

    top_items = (
        OrderItem.objects.filter(
            order__created_at__gte=day_start,
            order__created_at__lt=day_end,
        )
        .exclude(order__status=Order.STATUS_CANCELLED)
        .values('item_name', 'variant_name')
        .annotate(qty=Sum('quantity'), revenue=Sum('subtotal'))
        .order_by('-qty')[:10]
    )

    return {
        'date': date,
        'orders_placed': placed.count(),
        'orders_cancelled': cancelled.count(),
        'revenue': revenue,
        'top_items': list(top_items),
    }


def get_production_recommendations(days=7):
    since = timezone.now() - timezone.timedelta(days=days)
    items = (
        OrderItem.objects.filter(order__created_at__gte=since)
        .exclude(order__status=Order.STATUS_CANCELLED)
        .values('item_name', 'variant_name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:8]
    )
    return list(items)


def get_weekly_trend():
    since = timezone.now() - timezone.timedelta(days=7)
    return list(
        Order.objects.filter(created_at__gte=since)
        .exclude(status=Order.STATUS_CANCELLED)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(orders=Count('id'), revenue=Sum('total_amount'))
        .order_by('day')
    )
