import uuid
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CUSTOMER = 'customer'
    ROLE_ADMIN = 'admin'
    ROLE_DELIVERY = 'delivery'

    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_ADMIN, 'Admin'),
        (ROLE_DELIVERY, 'Delivery Agent'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_shop_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_delivery_agent(self):
        return self.role == self.ROLE_DELIVERY


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='menu/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    @property
    def min_price(self):
        prices = self.variants.filter(is_available=True, price__isnull=False).values_list('price', flat=True)
        return min(prices) if prices else None


class MenuVariant(models.Model):
    SHAPE_SQUARE = 'square_puff'
    SHAPE_STICK = 'stick'
    SHAPE_TRIANGLE = 'triangle'
    SHAPE_SINGLE = 'single'
    SHAPE_DOUBLE = 'double'
    SHAPE_STANDARD = 'standard'

    SHAPE_CHOICES = [
        (SHAPE_SQUARE, 'Square Puff'),
        (SHAPE_STICK, 'Stick'),
        (SHAPE_TRIANGLE, 'Triangle'),
        (SHAPE_SINGLE, 'Single'),
        (SHAPE_DOUBLE, 'Double'),
        (SHAPE_STANDARD, 'Standard'),
    ]

    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='variants')
    shape = models.CharField(max_length=20, choices=SHAPE_CHOICES)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    price_label = models.CharField(
        max_length=50,
        blank=True,
        help_text='Display text when price is custom (e.g. "Double")',
    )
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ['menu_item', 'shape']
        ordering = ['menu_item', 'shape']

    def __str__(self):
        return f'{self.menu_item.name} — {self.get_shape_display()}'

    @property
    def display_price(self):
        if self.price is not None:
            return self.price
        return self.price_label or '—'


class DeliveryAgent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_profile')
    is_active = models.BooleanField(default=True)
    phone = models.CharField(max_length=15)
    vehicle_info = models.CharField(max_length=100, blank=True)
    current_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} (Delivery)'


class Order(models.Model):
    STATUS_PLACED = 'placed'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PREPARING = 'preparing'
    STATUS_READY = 'ready'
    STATUS_OUT_FOR_DELIVERY = 'out_for_delivery'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PLACED, 'Order Placed'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_READY, 'Ready'),
        (STATUS_OUT_FOR_DELIVERY, 'Out for Delivery'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    ACTIVE_STATUSES = [
        STATUS_PLACED,
        STATUS_CONFIRMED,
        STATUS_PREPARING,
        STATUS_READY,
        STATUS_OUT_FOR_DELIVERY,
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLACED)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_address = models.TextField()
    delivery_phone = models.CharField(max_length=15)
    delivery_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    delivery_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    delivery_agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_deliveries',
        limit_choices_to={'role': User.ROLE_DELIVERY},
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f'WF{timezone.now().strftime("%y%m%d")}{uuid.uuid4().hex[:6].upper()}'
        super().save(*args, **kwargs)

    @property
    def can_cancel(self):
        return self.status in (self.STATUS_PLACED, self.STATUS_CONFIRMED)

    @property
    def status_progress(self):
        steps = [
            self.STATUS_PLACED,
            self.STATUS_CONFIRMED,
            self.STATUS_PREPARING,
            self.STATUS_READY,
            self.STATUS_OUT_FOR_DELIVERY,
            self.STATUS_DELIVERED,
        ]
        if self.status == self.STATUS_CANCELLED:
            return 0
        try:
            return steps.index(self.status) + 1
        except ValueError:
            return 0


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(MenuVariant, on_delete=models.SET_NULL, null=True)
    item_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity}x {self.item_name} ({self.variant_name})'


class Notification(models.Model):
    TYPE_ORDER = 'order'
    TYPE_READY = 'ready'
    TYPE_DELIVERED = 'delivered'
    TYPE_QUERY = 'query'
    TYPE_GENERAL = 'general'
    TYPE_ADMIN = 'admin'

    TYPE_CHOICES = [
        (TYPE_ORDER, 'Order Update'),
        (TYPE_READY, 'Order Ready'),
        (TYPE_DELIVERED, 'Delivered'),
        (TYPE_QUERY, 'Query Response'),
        (TYPE_GENERAL, 'General'),
        (TYPE_ADMIN, 'Admin Alert'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_GENERAL)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} → {self.user.username}'


class CustomerQuery(models.Model):
    STATUS_OPEN = 'open'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='queries')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='queries')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    admin_response = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Customer queries'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} — {self.customer.username}'


class SiteSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site setting'
        verbose_name_plural = 'Site settings'

    def __str__(self):
        return self.key

    @classmethod
    def get(cls, key, default=''):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value, description=''):
        obj, _ = cls.objects.update_or_create(
            key=key,
            defaults={'value': value, 'description': description},
        )
        return obj
