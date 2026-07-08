from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .decorators import admin_required, customer_required
from .forms import (
    AdminPasswordForm,
    CheckoutForm,
    CustomerQueryForm,
    DeliveryAgentForm,
    LoginForm,
    MenuItemForm,
    MenuVariantForm,
    OrderStatusForm,
    ProfileForm,
    QueryResponseForm,
    RegisterForm,
    SiteSettingForm,
)
from .models import Category, CustomerQuery, DeliveryAgent, MenuItem, MenuVariant, Notification, Order, OrderItem, SiteSetting, User
from .utils import (
    cart_total,
    get_cart,
    get_daily_analytics,
    get_production_recommendations,
    get_weekly_trend,
    notify_admins,
    notify_user,
    save_cart,
)


def landing(request):
    if request.user.is_authenticated:
        if request.user.is_shop_admin:
            return redirect('shop:admin_dashboard')
        return redirect('shop:menu')
    featured = MenuItem.objects.filter(is_available=True, is_featured=True)[:6]
    return render(request, 'shop/landing.html', {'featured': featured})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('shop:dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to Weffle! Your account is ready.')
            return redirect('shop:menu')
    else:
        form = RegisterForm()
    return render(request, 'shop/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_shop_admin:
            return redirect('shop:admin_dashboard')
        return redirect('shop:dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            if user.is_shop_admin:
                return redirect('shop:admin_dashboard')
            return redirect('shop:menu')
        messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'shop/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('shop:landing')


@customer_required
def dashboard(request):
    recent_orders = Order.objects.filter(customer=request.user)[:5]
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(
        request,
        'shop/dashboard.html',
        {'recent_orders': recent_orders, 'unread_notifications': unread},
    )


@customer_required
def menu_view(request):
    categories = Category.objects.filter(is_active=True).prefetch_related(
        'items__variants'
    )
    return render(request, 'shop/menu.html', {'categories': categories})


@customer_required
@require_POST
def add_to_cart(request):
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))
    variant = get_object_or_404(
        MenuVariant.objects.select_related('menu_item'),
        pk=variant_id,
        is_available=True,
        menu_item__is_available=True,
    )
    if variant.price is None:
        messages.error(request, 'This variant is not available for ordering.')
        return redirect('shop:menu')

    cart = get_cart(request)
    key = str(variant_id)
    if key in cart:
        cart[key]['quantity'] += quantity
    else:
        cart[key] = {
            'variant_id': variant_id,
            'item_name': variant.menu_item.name,
            'variant_name': variant.get_shape_display(),
            'price': str(variant.price),
            'quantity': quantity,
        }
    save_cart(request, cart)
    messages.success(request, f'Added {variant.menu_item.name} to cart.')
    return redirect('shop:cart')


@customer_required
def cart_view(request):
    cart = get_cart(request)
    items = [{'key': k, **v} for k, v in cart.items()]
    for item in items:
        item['subtotal'] = Decimal(str(item['price'])) * item['quantity']
    total = cart_total(cart)
    return render(request, 'shop/cart.html', {'items': items, 'total': total})


@customer_required
@require_POST
def update_cart(request):
    cart = get_cart(request)
    for key, item in list(cart.items()):
        qty = int(request.POST.get(f'qty_{key}', item['quantity']))
        if qty <= 0:
            del cart[key]
        else:
            cart[key]['quantity'] = qty
    save_cart(request, cart)
    return redirect('shop:cart')


@customer_required
@require_POST
def remove_from_cart(request, item_key):
    cart = get_cart(request)
    cart.pop(str(item_key), None)
    save_cart(request, cart)
    messages.info(request, 'Item removed from cart.')
    return redirect('shop:cart')


@customer_required
def checkout_view(request):
    cart = get_cart(request)
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('shop:menu')

    total = cart_total(cart)
    cart_items = [{'key': k, **v} for k, v in cart.items()]
    for item in cart_items:
        item['subtotal'] = Decimal(str(item['price'])) * item['quantity']
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = Order.objects.create(
                    customer=request.user,
                    total_amount=total,
                    delivery_address=form.cleaned_data['delivery_address'],
                    delivery_phone=form.cleaned_data['delivery_phone'],
                    notes=form.cleaned_data.get('notes', ''),
                    status=Order.STATUS_PLACED,
                )
                for item in cart.values():
                    OrderItem.objects.create(
                        order=order,
                        menu_item_id=MenuVariant.objects.get(pk=item['variant_id']).menu_item_id,
                        variant_id=item['variant_id'],
                        item_name=item['item_name'],
                        variant_name=item['variant_name'],
                        quantity=item['quantity'],
                        unit_price=Decimal(item['price']),
                        subtotal=Decimal(item['price']) * item['quantity'],
                    )

                notify_user(
                    request.user,
                    'Order Placed!',
                    f'Your order {order.order_number} has been placed successfully. We will notify you when it is ready.',
                    'order',
                    order,
                )
                notify_admins(
                    'New Order!',
                    f'Order {order.order_number} placed by {request.user.username} — ₹{total}',
                    'admin',
                    order,
                )

            save_cart(request, {})
            messages.success(request, f'Order {order.order_number} placed successfully!')
            return redirect('shop:order_detail', pk=order.pk)
    else:
        form = CheckoutForm(
            initial={
                'delivery_address': request.user.address,
                'delivery_phone': request.user.phone,
            }
        )
    return render(request, 'shop/checkout.html', {'form': form, 'items': cart_items, 'total': total})


@customer_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user)
    return render(request, 'shop/order_history.html', {'orders': orders})


@customer_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    return render(request, 'shop/order_detail.html', {'order': order})


@customer_required
@require_POST
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    if not order.can_cancel:
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('shop:order_detail', pk=pk)

    order.status = Order.STATUS_CANCELLED
    order.cancelled_at = timezone.now()
    order.save()

    notify_user(request.user, 'Order Cancelled', f'Order {order.order_number} has been cancelled.', 'order', order)
    notify_admins('Order Cancelled', f'Order {order.order_number} cancelled by {request.user.username}.', 'admin', order)
    messages.success(request, 'Order cancelled successfully.')
    return redirect('shop:order_history')


@customer_required
def track_order(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    agent = None
    if order.delivery_agent and hasattr(order.delivery_agent, 'delivery_profile'):
        agent = order.delivery_agent.delivery_profile
    return render(request, 'shop/track_order.html', {'order': order, 'agent': agent})


@customer_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('shop:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'shop/profile.html', {'form': form})


@customer_required
def query_create(request):
    if request.method == 'POST':
        form = CustomerQueryForm(request.user, request.POST)
        if form.is_valid():
            query = form.save(commit=False)
            query.customer = request.user
            query.save()
            notify_admins(
                'Customer Query',
                f'{request.user.username}: {query.subject}',
                'admin',
                query.order,
            )
            messages.success(request, 'Your query has been sent to admin.')
            return redirect('shop:dashboard')
    else:
        form = CustomerQueryForm(request.user)
    return render(request, 'shop/query_form.html', {'form': form})


@login_required
@require_GET
def notifications_api(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:20]
    data = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'created_at': n.created_at.strftime('%H:%M'),
            'order_id': n.order_id,
        }
        for n in notifications
    ]
    return JsonResponse({'notifications': data, 'count': len(data)})


@login_required
@require_POST
def mark_notification_read(request, pk):
    Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


# ─── Admin Views ───────────────────────────────────────────────────────────────


@admin_required
def admin_dashboard(request):
    today = get_daily_analytics()
    recommendations = get_production_recommendations()
    pending_orders = Order.objects.filter(status__in=Order.ACTIVE_STATUSES).count()
    open_queries = CustomerQuery.objects.filter(status=CustomerQuery.STATUS_OPEN).count()
    recent_orders = Order.objects.all()[:10]
    return render(
        request,
        'shop/admin/dashboard.html',
        {
            'analytics': today,
            'recommendations': recommendations,
            'pending_orders': pending_orders,
            'open_queries': open_queries,
            'recent_orders': recent_orders,
        },
    )


@admin_required
def admin_orders(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all()
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(
        request,
        'shop/admin/orders.html',
        {'orders': orders, 'status_filter': status_filter, 'statuses': Order.STATUS_CHOICES},
    )


@admin_required
def admin_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            old_status = Order.objects.get(pk=pk).status
            order = form.save()

            if order.status == Order.STATUS_READY and old_status != Order.STATUS_READY:
                notify_user(
                    order.customer,
                    'Order Ready! 🧇',
                    f'Your order {order.order_number} is ready!',
                    'ready',
                    order,
                )
            elif order.status == Order.STATUS_OUT_FOR_DELIVERY:
                notify_user(
                    order.customer,
                    'Out for Delivery',
                    f'Your order {order.order_number} is on the way!',
                    'order',
                    order,
                )
            elif order.status == Order.STATUS_DELIVERED:
                order.delivered_at = timezone.now()
                order.save(update_fields=['delivered_at'])
                notify_user(
                    order.customer,
                    'Delivered! ✅',
                    f'Your order {order.order_number} has been delivered. Enjoy!',
                    'delivered',
                    order,
                )
            elif order.status == Order.STATUS_CANCELLED:
                order.cancelled_at = timezone.now()
                order.save(update_fields=['cancelled_at'])
                notify_user(
                    order.customer,
                    'Order Cancelled',
                    f'Your order {order.order_number} has been cancelled by admin.',
                    'order',
                    order,
                )

            messages.success(request, 'Order status updated.')
            return redirect('shop:admin_order_detail', pk=pk)
    else:
        form = OrderStatusForm(instance=order)
    return render(request, 'shop/admin/order_detail.html', {'order': order, 'form': form})


@admin_required
def admin_menu(request):
    items = MenuItem.objects.select_related('category').prefetch_related('variants')
    return render(request, 'shop/admin/menu_manage.html', {'items': items})


@admin_required
def admin_menu_create(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item created.')
            return redirect('shop:admin_menu')
    else:
        form = MenuItemForm()
    return render(request, 'shop/admin/menu_form.html', {'form': form, 'title': 'Add Menu Item'})


@admin_required
def admin_menu_edit(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item updated.')
            return redirect('shop:admin_menu')
    else:
        form = MenuItemForm(instance=item)
    return render(request, 'shop/admin/menu_form.html', {'form': form, 'title': 'Edit Menu Item', 'item': item})


@admin_required
@require_POST
def admin_menu_delete(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    item.delete()
    messages.success(request, 'Menu item deleted.')
    return redirect('shop:admin_menu')


@admin_required
def admin_variant_edit(request, item_pk):
    item = get_object_or_404(MenuItem, pk=item_pk)
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        if variant_id:
            variant = get_object_or_404(MenuVariant, pk=variant_id, menu_item=item)
            form = MenuVariantForm(request.POST, instance=variant)
        else:
            form = MenuVariantForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.menu_item = item
            variant.save()
            messages.success(request, 'Variant saved.')
            return redirect('shop:admin_variant_edit', item_pk=item_pk)
    else:
        form = MenuVariantForm()

    variants = item.variants.all()
    return render(
        request,
        'shop/admin/variant_form.html',
        {'item': item, 'variants': variants, 'form': form},
    )


@admin_required
def admin_customers(request):
    customers = (
        User.objects.filter(role=User.ROLE_CUSTOMER)
        .annotate(order_count=Count('orders'))
        .order_by('-date_joined')
    )
    return render(request, 'shop/admin/customers.html', {'customers': customers})


@admin_required
def admin_queries(request):
    queries = CustomerQuery.objects.select_related('customer', 'order')
    status_filter = request.GET.get('status', '')
    if status_filter:
        queries = queries.filter(status=status_filter)
    return render(request, 'shop/admin/queries.html', {'queries': queries, 'status_filter': status_filter})


@admin_required
def admin_query_detail(request, pk):
    query = get_object_or_404(CustomerQuery, pk=pk)
    if request.method == 'POST':
        form = QueryResponseForm(request.POST, instance=query)
        if form.is_valid():
            query = form.save()
            if query.admin_response:
                notify_user(
                    query.customer,
                    'Query Response',
                    f'Re: {query.subject} — {query.admin_response[:100]}',
                    'query',
                    query.order,
                )
            messages.success(request, 'Query updated.')
            return redirect('shop:admin_queries')
    else:
        form = QueryResponseForm(instance=query)
    return render(request, 'shop/admin/query_detail.html', {'query': query, 'form': form})


@admin_required
def admin_analytics(request):
    today = get_daily_analytics()
    week = get_weekly_trend()
    recommendations = get_production_recommendations()
    return render(
        request,
        'shop/admin/analytics.html',
        {'today': today, 'week': week, 'recommendations': recommendations},
    )


@admin_required
def admin_delivery_agents(request):
    agents = DeliveryAgent.objects.select_related('user')
    return render(request, 'shop/admin/delivery_agents.html', {'agents': agents})


@admin_required
def admin_delivery_create(request):
    if request.method == 'POST':
        form = DeliveryAgentForm(request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password') or User.objects.make_random_password()
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=request.POST.get('first_name', ''),
                role=User.ROLE_DELIVERY,
            )
            agent = form.save(commit=False)
            agent.user = user
            agent.save()
            messages.success(request, f'Delivery agent {username} created.')
            return redirect('shop:admin_delivery_agents')
    else:
        form = DeliveryAgentForm()
    return render(request, 'shop/admin/delivery_form.html', {'form': form})


@admin_required
def admin_settings(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'password':
            pw_form = AdminPasswordForm(request.POST)
            if pw_form.is_valid():
                if not request.user.check_password(pw_form.cleaned_data['current_password']):
                    messages.error(request, 'Current password is incorrect.')
                else:
                    request.user.set_password(pw_form.cleaned_data['new_password'])
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, 'Password updated successfully.')
                return redirect('shop:admin_settings')
        elif action == 'setting':
            setting_form = SiteSettingForm(request.POST)
            if setting_form.is_valid():
                setting_form.save()
                messages.success(request, 'Setting saved.')
                return redirect('shop:admin_settings')
    else:
        pw_form = AdminPasswordForm()
        setting_form = SiteSettingForm()

    settings_list = SiteSetting.objects.all()
    return render(
        request,
        'shop/admin/settings.html',
        {'pw_form': pw_form, 'setting_form': setting_form, 'settings_list': settings_list},
    )


@admin_required
@require_GET
def admin_orders_api(request):
    new_orders = Order.objects.filter(
        status=Order.STATUS_PLACED,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=30),
    ).count()
    open_queries = CustomerQuery.objects.filter(status=CustomerQuery.STATUS_OPEN).count()
    return JsonResponse({'new_orders': new_orders, 'open_queries': open_queries})
