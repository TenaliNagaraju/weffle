from django.contrib import admin

from .models import (
    Category,
    CustomerQuery,
    DeliveryAgent,
    MenuItem,
    MenuVariant,
    Notification,
    Order,
    OrderItem,
    SiteSetting,
    User,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'phone', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'email', 'phone']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'sort_order']
    prepopulated_fields = {'slug': ('name',)}


class MenuVariantInline(admin.TabularInline):
    model = MenuVariant
    extra = 1


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_available', 'is_featured', 'sort_order']
    list_filter = ['category', 'is_available']
    inlines = [MenuVariantInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['item_name', 'variant_name', 'quantity', 'unit_price', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'customer__username']
    inlines = [OrderItemInline]


@admin.register(CustomerQuery)
class CustomerQueryAdmin(admin.ModelAdmin):
    list_display = ['subject', 'customer', 'status', 'created_at']
    list_filter = ['status']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']


@admin.register(DeliveryAgent)
class DeliveryAgentAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'is_active']


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'updated_at']
