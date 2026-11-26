# UkayTaNa

UkayTaNa is a Django full-stack web app for discovering Cebu ukay-ukay sellers.
The interface is rendered with Django templates, and PostgreSQL stores account
and application data.

## Requirements

- Python 3.11 or newer
- PostgreSQL, or a Supabase PostgreSQL database

## Local setup (Windows PowerShell)

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install Python dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set a private `SECRET_KEY` and the
   PostgreSQL connection values. For a local PostgreSQL server, set
   `DB_SSLMODE=disable`; for Supabase, use the database host and credentials
   from its connection settings and keep SSL enabled.

   ```powershell
   Copy-Item .env.example .env
   ```

   Never commit `.env` or share its database password. `.env`, virtual
   environments, bytecode caches, and the local media directory are ignored by
   Git.

4. Create the database tables and an administrator account:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. Start the Django development server:

   ```powershell
   python manage.py runserver
   ```

   Open `http://127.0.0.1:8000/`. Registration is at
   `http://127.0.0.1:8000/accounts/signup/`.

Run the automated checks with `python manage.py check` and the test suite with
`python manage.py test`. Django uses PostgreSQL for both the app and its test
database; the configured PostgreSQL user must be allowed to create test
databases.

## Account features

- Buyer and seller registration with unique usernames and case-insensitive
  unique email addresses, validated email, and matching passwords.
- Django authentication with hashed passwords, login, POST logout, and
  login-protected profile pages.
- Role-specific dashboards with server-side access checks.
- Personal profile viewing and editing, including seller shop details and an
  optional profile photo.

## Core feature: Item Listing & Marketplace (PD2)

Sellers publish women's secondhand clothing listings and buyers browse them.
The feature works end to end: PostgreSQL/Supabase models, Django views, forms
and URL routes, and Django templates.

- **Seller (Create / Update / Delete):** create, edit and delete own listings
  (title, category, description, size, condition, price, up to 5 photos);
  publish, unpublish and mark as sold from **My listings**.
- **Buyer (Read):** browse published listings with keyword search, filters
  (category, size, condition, price range) and sorting (newest, oldest, price).
- **Rules:** price must be greater than ₱0; at most 5 photos (5 MB each, images
  only); a listing needs at least one photo to be published; sold listings can
  no longer be edited or republished; sellers can only change their own
  listings; buyers only see published listings from active sellers.
- **Models:** `Listing` (ForeignKey to `CustomUser` as seller) and
  `ListingPhoto` (ForeignKey to `Listing`).
- **Dashboards:** sellers see listing counts and their latest listings, buyers
  see the latest published listings, administrators see listing totals.

Payments and meetups are arranged by users outside the system. Uploaded photos
are stored in the local `media/` folder (the database stores the file path).

### Setup steps

1. Copy `.env.example` to `.env` and fill in your own database values.
2. Create and activate a virtual environment, then install the packages:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

3. Apply the migrations and create an admin account:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. Start the server and open http://127.0.0.1:8000/:

   ```powershell
   python manage.py runserver
   ```