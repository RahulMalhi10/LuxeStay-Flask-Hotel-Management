# 🏨 LuxeStay — Hotel Management System

A full-featured Hotel Management System built with **Python Flask + SQLite**.

## Features
- **Dashboard** — Occupancy stats, revenue, recent bookings
- **Rooms** — Add, edit, delete rooms (Single / Double / Deluxe / Suite)
- **Guests** — Guest registry with full profile
- **Bookings** — Create bookings, auto-calculates price, check-in/check-out/cancel
- **Payments** — Record payments by cash, card, or bank transfer

---

## 🚀 Setup & Run

### 1. Install Python (3.8+)
Make sure Python is installed: https://python.org

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
```
http://127.0.0.1:5000
```

The SQLite database (`hotel.db`) is created automatically on first run with 8 sample rooms pre-loaded.

---

## 📁 Project Structure
```
hotel_mgmt/
├── app.py              # Main Flask app + all routes
├── hotel.db            # SQLite database (auto-created)
├── requirements.txt
└── templates/
    ├── base.html       # Layout with sidebar
    ├── dashboard.html
    ├── rooms.html
    ├── room_form.html
    ├── guests.html
    ├── guest_form.html
    ├── bookings.html
    ├── booking_form.html
    ├── payments.html
    └── payment_form.html
```

## 🗄️ Database Tables
| Table    | Purpose                        |
|----------|-------------------------------|
| rooms    | Room info, type, price, status |
| guests   | Guest profiles                 |
| bookings | Reservation records            |
| payments | Payment tracking               |
