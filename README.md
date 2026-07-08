# Weffle — Food Delivery Platform

A full-featured waffle ordering web application built with **Django 5**, **Bootstrap 5**, and **SQLite**.

## Features

- Cover page → Register → Login → Menu → Cart → Checkout flow
- Real-time order notifications (polling-based, no paid services)
- Admin panel: menu CRUD, order management, analytics, customer queries
- Delivery tracking with free OpenStreetMap/Leaflet maps
- Configurable site settings without code changes
- Secure: CSRF, password validation, role-based access, production-ready settings

## Quick Start

```bash
cd weffle
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_menu
python manage.py runserver
```

Open **http://127.0.0.1:8000**

### Default Admin Login
- **Username:** `admin`
- **Password:** `Admin@Weffle2026`

Change password in Admin Panel → Settings.

## Deploy to Your Domain (No Code Changes)

1. Copy `.env.example` to `.env`
2. Set `DEBUG=False`
3. Set `SECRET_KEY` to a long random string
4. Set `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
5. Set `CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com`
6. Run `python manage.py collectstatic`
7. Serve with Gunicorn + Nginx (free)

## Admin Capabilities

- CRUD menu items & prices
- View/manage all orders & update delivery status
- Assign delivery agents
- Respond to customer queries
- Daily analytics: orders, revenue, top sellers
- Production recommendations (what to make more of)
- Change admin password & site settings from UI

## Tech Stack (100% Free)

- Python Django 5
- SQLite (built-in, zero setup)
- Bootstrap 5 + AOS animations
- Leaflet + OpenStreetMap (free maps)
- No paid APIs required
