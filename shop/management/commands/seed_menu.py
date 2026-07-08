from decimal import Decimal

from django.core.management.base import BaseCommand

from shop.models import Category, MenuItem, MenuVariant, SiteSetting, User


WAFFLE_MENU = [
    ('Dark Fantasy', {'square_puff': 39, 'stick': 69, 'triangle': 49}),
    ('Milk Fantasy', {'square_puff': 39, 'stick': 69, 'triangle': 49}),
    ('White Fantasy', {'square_puff': 45, 'stick': 75, 'triangle': 49}),
    ('Dark & Milk', {'square_puff': 49, 'stick': 79, 'triangle': 59}),
    ('Dark & White', {'square_puff': 49, 'stick': 79, 'triangle': 59}),
    ('Caramel Chocolate', {'square_puff': 59, 'stick': 89, 'triangle': 65}),
    ('Triple Chocolate', {'square_puff': 59, 'stick': 89, 'triangle': 65}),
    ('Crunchy Oreo', {'square_puff': 65, 'stick': 99, 'triangle': 75}),
    ('Crunchy KitKat', {'square_puff': 65, 'stick': 99, 'triangle': 75}),
    ('Gems with Milk', {'square_puff': 65, 'stick': 99, 'triangle': 75}),
    ('Gems with Dark', {'square_puff': 65, 'stick': 99, 'triangle': 75}),
    ('Triple Chocolate (Double)', {'square_puff': 139, 'stick': None, 'triangle': None}),
    ('Lotus Biscoff', {'square_puff': 90, 'stick': 149, 'triangle': 110}),
    ('Dry Fruits', {'square_puff': 80, 'stick': 105, 'triangle': None}),
    ('Special Naughty Nutella', {'square_puff': 120, 'stick': 'Double', 'triangle': None}),
    ('Almond Cake', {'square_puff': 220, 'stick': 'Single', 'triangle': None}),
]

BOWL_MENU = [
    ('Cake Bowl', 89),
    ('Double Chocolate Bowl', 99),
    ('Triple Chocolate Bowl', 99),
    ('KitKat Bowl', 110),
    ('Oreo Bowl', 110),
    ('Biscoff Bowl', 120),
]

SHAPE_MAP = {
    'square_puff': MenuVariant.SHAPE_SQUARE,
    'stick': MenuVariant.SHAPE_STICK,
    'triangle': MenuVariant.SHAPE_TRIANGLE,
}


class Command(BaseCommand):
    help = 'Seed Weffle menu, categories, admin user, and site settings'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Weffle database...')

        waffle_cat, _ = Category.objects.get_or_create(
            slug='waffles',
            defaults={'name': 'Waffles', 'description': 'Delicious handcrafted weffles', 'sort_order': 1},
        )
        bowl_cat, _ = Category.objects.get_or_create(
            slug='bowls',
            defaults={'name': 'Bowls', 'description': 'Weffle bowls — perfect for sharing', 'sort_order': 2},
        )

        for i, (name, prices) in enumerate(WAFFLE_MENU):
            item, _ = MenuItem.objects.get_or_create(
                category=waffle_cat,
                name=name,
                defaults={'sort_order': i, 'is_available': True},
            )
            for shape_key, price_val in prices.items():
                shape = SHAPE_MAP[shape_key]
                if isinstance(price_val, str):
                    MenuVariant.objects.update_or_create(
                        menu_item=item,
                        shape=shape,
                        defaults={'price': None, 'price_label': price_val, 'is_available': True},
                    )
                elif price_val is None:
                    MenuVariant.objects.update_or_create(
                        menu_item=item,
                        shape=shape,
                        defaults={'price': None, 'price_label': '—', 'is_available': False},
                    )
                else:
                    MenuVariant.objects.update_or_create(
                        menu_item=item,
                        shape=shape,
                        defaults={'price': Decimal(str(price_val)), 'is_available': True},
                    )

        for i, (name, price) in enumerate(BOWL_MENU):
            item, _ = MenuItem.objects.get_or_create(
                category=bowl_cat,
                name=name,
                defaults={'sort_order': i, 'is_available': True},
            )
            MenuVariant.objects.update_or_create(
                menu_item=item,
                shape=MenuVariant.SHAPE_STANDARD,
                defaults={'price': Decimal(str(price)), 'is_available': True},
            )

        SiteSetting.set('welcome_message', 'Fresh weffles made with love!', 'Landing page tagline')
        SiteSetting.set('delivery_time', '30-45 minutes', 'Estimated delivery time')
        SiteSetting.set('contact_phone', '+91 9876543210', 'Contact phone number')

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@weffle.com',
                password='Admin@Weffle2026',
                role=User.ROLE_ADMIN,
            )
            self.stdout.write(self.style.SUCCESS('Admin created — username: admin, password: Admin@Weffle2026'))
        else:
            admin = User.objects.get(username='admin')
            admin.role = User.ROLE_ADMIN
            admin.save(update_fields=['role'])

        self.stdout.write(self.style.SUCCESS('Weffle menu seeded successfully!'))
