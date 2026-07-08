from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Customer
    path('dashboard/', views.dashboard, name='dashboard'),
    path('menu/', views.menu_view, name='menu'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/<str:item_key>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/<int:pk>/track/', views.track_order, name='track_order'),
    path('profile/', views.profile_view, name='profile'),
    path('query/', views.query_create, name='query_create'),

    # Real-time API
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Admin panel
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/orders/', views.admin_orders, name='admin_orders'),
    path('admin-panel/orders/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-panel/menu/', views.admin_menu, name='admin_menu'),
    path('admin-panel/menu/create/', views.admin_menu_create, name='admin_menu_create'),
    path('admin-panel/menu/<int:pk>/edit/', views.admin_menu_edit, name='admin_menu_edit'),
    path('admin-panel/menu/<int:pk>/delete/', views.admin_menu_delete, name='admin_menu_delete'),
    path('admin-panel/menu/<int:item_pk>/variants/', views.admin_variant_edit, name='admin_variant_edit'),
    path('admin-panel/customers/', views.admin_customers, name='admin_customers'),
    path('admin-panel/queries/', views.admin_queries, name='admin_queries'),
    path('admin-panel/queries/<int:pk>/', views.admin_query_detail, name='admin_query_detail'),
    path('admin-panel/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin-panel/delivery/', views.admin_delivery_agents, name='admin_delivery_agents'),
    path('admin-panel/delivery/create/', views.admin_delivery_create, name='admin_delivery_create'),
    path('admin-panel/settings/', views.admin_settings, name='admin_settings'),
    path('admin-panel/api/alerts/', views.admin_orders_api, name='admin_orders_api'),
]
