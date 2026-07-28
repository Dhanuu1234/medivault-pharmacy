# MediVault — Pharmacy Management System

A full-stack pharmacy management system built with **Django 5**. MediVault covers both sides of a real
pharmacy: a customer-facing storefront (search, cart, checkout, prescriptions, order tracking) and a staff
dashboard (stock, expiry alerts, order fulfilment, categories, messages).

Built as a portfolio / resume project — deployable to [Render](https://render.com) in a few minutes.

---

## ✨ Features

**Customer storefront**
- Browse & search medicines by name, brand, composition or condition, filter by category, sort by price/newest
- Detailed medicine pages: composition, uses, dosage guidance, side effects, precautions, related products
- Session-based shopping cart (works for guests, checkout requires login)
- Checkout with shipping details, Cash-on-Delivery or Online payment selection
- Automatic prescription upload prompt when the cart contains an Rx-only medicine
- Order history, order detail/receipt view, and order cancellation
- Product reviews & star ratings
- Account registration/login, editable profile (address, phone, city, pincode)
- Contact form

**Staff / admin dashboard** (`/dashboard/`, staff & admin roles only)
- Live stats: total medicines, low-stock count, out-of-stock count, expiring-soon count, total & pending orders, revenue
- Add / edit / soft-delete medicines with full clinical detail fields
- Category management
- Order queue with status filter and one-click status updates (Pending → Processing → Shipped → Delivered)
- Contact message inbox
- Everything is also manageable from the built-in Django Admin at `/admin/`

**Engineering**
- Custom `User` model with roles (`customer`, `pharmacist`, `admin`)
- Clean app separation: `accounts` (auth) + `store` (catalogue, cart, orders)
- A `seed_medicines` management command populates ~30 real-world medicines across 12 categories with
  genuine composition/dosage/side-effect data
- A `create_demo_users` command creates ready-to-use demo logins
- Production-ready settings: environment variables, Whitenoise static files, `dj-database-url` for Postgres,
  Gunicorn, Render blueprint

---

## 🗂 Project structure

```
medivault/
├── pharmacy/            # Django project settings, root urls, wsgi/asgi
├── accounts/            # Custom User model, auth views, profile
├── store/                # Medicines, categories, cart, orders, dashboard views
│   └── management/commands/
│       ├── seed_medicines.py     # populates the catalogue
│       └── create_demo_users.py  # creates demo admin/pharmacist/customer
├── templates/            # All HTML templates (base, store, accounts, dashboard)
├── static/css/style.css  # Design system (custom, no framework)
├── requirements.txt
├── Procfile               # gunicorn start command (Render/Heroku style)
├── build.sh                # Render build command (install, collectstatic, migrate, seed)
├── render.yaml            # One-click Render Blueprint
└── manage.py
```

---

## 🚀 Run locally

```bash
# 1. Create & activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. Populate the catalogue and demo accounts
python manage.py seed_medicines
python manage.py create_demo_users

# 5. Run the server
python manage.py runserver
```

Visit **http://127.0.0.1:8000/**.

### Demo logins (created by `create_demo_users`)

| Role | Username | Password |
|---|---|---|
| Admin (full access + Django Admin) | `admin` | `MediVault@123` |
| Pharmacist (dashboard only) | `pharmacist` | `MediVault@123` |
| Customer | `customer` | `MediVault@123` |

> ⚠️ Change these passwords before deploying anywhere public.

---

## ☁️ Deploy to Render

**Option A — One-click Blueprint**
1. Push this project to a GitHub repository.
2. On [render.com](https://render.com), choose **New → Blueprint** and point it at your repo. Render reads
   `render.yaml` and provisions both the web service and a free Postgres database automatically.
3. Wait for the build to finish — `build.sh` installs dependencies, runs migrations, collects static files,
   and seeds the medicine catalogue.
4. Open the live URL Render gives you. Log in with the demo accounts above, or run
   `python manage.py createsuperuser` from the Render shell for your own admin account.

**Option B — Manual web service**
1. New → Web Service → connect your repo.
2. Build Command: `./build.sh`
3. Start Command: `gunicorn pharmacy.wsgi:application`
4. Add environment variables: `SECRET_KEY` (generate one), `DEBUG=False`, `ALLOWED_HOSTS=.onrender.com`,
   and `DATABASE_URL` (from a Render Postgres instance, or omit to fall back to SQLite).

---

## 🔑 Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | dev-only fallback (set your own in production) |
| `DEBUG` | Debug mode | `True` locally, set to `False` in production |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `127.0.0.1,localhost` |
| `DATABASE_URL` | Postgres connection string | falls back to local SQLite if unset |

Copy `.env.example` to `.env` and adjust for local overrides if you use `python-dotenv` or a process manager
that loads `.env` files.

---

## 🧭 Roadmap ideas (good talking points in an interview)

- Razorpay/Stripe integration for real online payments
- Email notifications on order status change
- Barcode/QR based batch tracking for pharmacists
- REST API (Django REST Framework) for a future mobile app
- Automated low-stock reorder suggestions

---

## ⚠️ Disclaimer

This is a portfolio/demonstration project. Medicine information shown (uses, dosage, side effects) is general
product information for demo purposes and is **not** medical advice. Do not use this application for real
medical transactions.
