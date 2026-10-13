# Rent House Management System (RHMS)

**A simple, clean, beginner-friendly web-based rental management system for small landlords and property managers.**

---

## 1. Project Overview

The **Rent House Management System (RHMS)** is designed to replace manual paper records with a streamlined digital workflow for managing rental properties, rooms, apartments, tenants, rental agreements, monthly rent charges, payments, and balances.

Built strictly with standard **Python 3.14**, **Django 5.2**, **SQLite3**, **HTML5**, **CSS3**, and **Vanilla JavaScript ES6+**, it avoids complex external frontend frameworks (no React, Vue, Next.js, Bootstrap, or Tailwind) to remain clear, maintainable, robust, and ideal for a University Computer Science project.

---

## 2. Technology Stack

- **Backend:** Python 3.14, Django 5.2 (Django ORM, Forms, Built-in Auth, Django Admin)
- **Database:** SQLite3
- **Frontend:** Semantic HTML5, Custom Responsive CSS3, Vanilla JavaScript ES6+
- **Testing:** Django Test Runner (`python manage.py test`)

---

## 3. Main Workflow

```
Property (House / Room / Apartment)
   ↓
Available Rental Unit (PROP-0001)
   ↓
Tenant Registration (TEN-0001)
   ↓
Rental Agreement (RENT-0001)
   ↓
Monthly Rent Charge (Billing Month & Due Date)
   ↓
Payment Recording (Cash, ZAAD, eDahab, Card, Bank)
   ↓
Automatic Financial Balance Calculation
   ↓
Official Printable Payment Receipt (window.print() / @media print)
   ↓
Agreement Completion or Renewal (Property reverts to Available)
```

---

## 4. Key Features & Business Rules

1. **User Authentication & Roles:**
   - **Admin / Property Manager:** Full CRUD on properties, tenants, agreements, rent charges, and payments; access to Django Admin; permission to delete records when safe.
   - **Staff / Receptionist:** Can view properties, register tenants, create rental agreements, generate charges, record payments, and print receipts. Cannot access Django admin or perform destructive deletions.
   - Server-side permission enforcement on all views (manual URL tampering is strictly blocked).
2. **Property Management:**
   - Auto-generated property codes (`PROP-0001`, `PROP-0002`).
   - Property types: *House*, *Room*, *Apartment*.
   - Statuses: *Available*, *Rented*, *Maintenance*, *Inactive*.
   - A property cannot be marked Available or deleted while an active rental agreement exists.
3. **Tenant Management:**
   - Auto-generated tenant numbers (`TEN-0001`, `TEN-0002`).
   - Protected identity information and active rental tracking.
   - Safe deletion protection preventing removal of active tenants.
4. **Rental Agreements:**
   - Auto-generated rental numbers (`RENT-0001`, `RENT-0002`).
   - Only *Available* properties can be rented.
   - Concurrency protection: A property can never have two active agreements simultaneously.
   - When an agreement is marked *Active*, property status automatically changes to *Rented*.
   - When marked *Completed* or *Cancelled*, property automatically returns to *Available*.
5. **Monthly Rent Tracking & Accounting:**
   - Specific `RentCharge` database records for each billing month.
   - Database constraint prevents duplicate charges for the same rental and month.
   - Accurate tracking: distinguishing between billed charges and future unbilled periods.
6. **Payments & Overpayment Protection:**
   - Auto-generated payment numbers (`PAY-0001`, `PAY-0002`).
   - Payment methods: *Cash*, *ZAAD*, *eDahab*, *Card*, *Bank*.
   - Exact mathematical calculation: `Amount Due - Payments = Outstanding Balance`.
   - Server-side validation rejects any payment exceeding the remaining charge balance.
   - Financial deletion protection preserving audit history.
7. **Printable Receipts & Summaries:**
   - Dedicated print-optimized receipts and agreement summaries using browser `window.print()` and `@media print` CSS (no heavy external PDF libraries needed).
8. **Dashboard:**
   - Live database statistics: Total Properties, Available Properties, Rented Properties, Total Tenants, Active Rentals, Pending Rent Balance, and Total Rent Collected.

---

## 5. System Setup & Installation

### Step 1 — Create a Virtual Environment

Open your terminal or PowerShell in the project directory:

```bash
python -m venv venv
```

### Step 2 — Activate the Virtual Environment

- **Windows (PowerShell):**
  ```powershell
  venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

### Step 3 — Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4 — Create Database Migrations

```bash
python manage.py makemigrations
```

### Step 5 — Apply Migrations

```bash
python manage.py migrate
```

### Step 6 — Create an Administrator (Optional if using Seed Data)

```bash
python manage.py createsuperuser
```

### Step 7 — Load Demonstration Data (Recommended)

To quickly populate the database with demonstration properties, tenants, agreements, monthly charges, and payments:

```bash
python manage.py seed_demo
```

This creates two ready-to-use accounts:
- **Administrator:** Username `admin` | Password `admin123`
- **Staff Receptionist:** Username `staff` | Password `staff123`

### Step 8 — Run the Development Server

```bash
python manage.py runserver
```

Open your web browser and navigate to:
- **Web Application:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Django Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 6. How to Use the System

1. **Sign In:**
   - Access [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/) and enter your credentials (`admin` / `admin123`).
2. **Register a Property:**
   - Go to **Properties** &rarr; Click **+ Add Property**.
   - Enter name, type (*House*, *Apartment*, *Room*), address, city, and monthly rent.
   - Status defaults to *Available*.
3. **Register a Tenant:**
   - Go to **Tenants** &rarr; Click **+ Register Tenant**.
   - Enter full name, phone number, and optional ID/email.
4. **Create a Rental Agreement:**
   - Go to **Rentals** &rarr; Click **+ Create Agreement** (or click *Rent Out This Property* directly from the property details page).
   - Select the property and tenant. Specify the agreed monthly rent, security deposit, and start date.
   - Saving the agreement automatically marks the property as *Rented*.
5. **Generate Monthly Rent Charges:**
   - Open the rental agreement detail page &rarr; Click **+ Generate Monthly Charge**.
   - Select the billing month (e.g. November 2026) and due date.
6. **Record a Payment:**
   - Click **+ Record Payment** on the rental agreement or from the **Payments** tab.
   - Choose the charge and enter the amount paid (e.g. $100 or full $150).
   - Select payment method (*Cash*, *ZAAD*, *eDahab*, *Card*, *Bank*).
   - The outstanding balance updates automatically. Overpayments are prevented.
7. **Print Receipts & Summaries:**
   - View any payment and click **Print Receipt**. The browser print window opens with a formatted receipt excluding navigation elements.
   - You can also click **Print Agreement Summary** on the rental detail page.
8. **End a Rental Agreement:**
   - Change the agreement status on the detail page to *Completed* or *Cancelled*.
   - The property automatically becomes *Available* for new tenants.

---

## 7. Running the Test Suite

The project includes unit and integration tests covering models, code generation, financial balance calculations, overpayment rejection, date validations, permissions, and dashboard metrics.

Run the test runner:

```bash
python manage.py test
```

Expected output:
```
Ran 22 tests in ...s
OK
```

---

## 8. Project Structure

```
rent_house/
│
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3
│
├── rent_house/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── utils.py            # Unique code generator
│   ├── asgi.py
│   └── wsgi.py
│
├── accounts/               # Authentication & role permissions
│   ├── permissions.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
│
├── dashboard/              # Metrics & analytics
│   ├── management/commands/seed_demo.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
│
├── properties/             # Property models, views, forms
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
│
├── tenants/                # Tenant records
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
│
├── rentals/                # Rental agreements & rent charges
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
│
├── payments/               # Payments & financial accounting
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
│
├── templates/              # HTML5 Templates
│   ├── base.html
│   ├── registration/
│   │   └── login.html
│   ├── dashboard/
│   │   └── dashboard.html
│   ├── properties/
│   │   ├── property_list.html
│   │   ├── property_form.html
│   │   ├── property_detail.html
│   │   └── property_confirm_delete.html
│   ├── tenants/
│   │   ├── tenant_list.html
│   │   ├── tenant_form.html
│   │   ├── tenant_detail.html
│   │   └── tenant_confirm_delete.html
│   ├── rentals/
│   │   ├── rental_list.html
│   │   ├── rental_form.html
│   │   ├── rental_detail.html
│   │   ├── rental_confirm_delete.html
│   │   ├── rental_print_summary.html
│   │   ├── rent_charge_list.html
│   │   └── rent_charge_form.html
│   └── payments/
│       ├── payment_list.html
│       ├── payment_form.html
│       ├── payment_detail.html
│       ├── payment_confirm_delete.html
│       └── receipt.html
│
└── static/                 # Static assets
    ├── css/
    │   └── style.css       # Clean responsive styles & print CSS
    └── js/
        └── main.js         # Mobile drawer & print triggers
```

---

## 9. Security & Simplicity Note

- Built specifically for local/demonstration and academic deployment.
- Passwords are securely hashed with Django's default PBKDF2 algorithm.
- Cross-Site Request Forgery (CSRF) protection is active on all forms.
- Deletions are guarded behind POST requests and explicit confirmation views.
- Financial integrity is preserved using `on_delete=models.PROTECT` and server-side checks.
#   r e n t - h a u s e - m s  
 