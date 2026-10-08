from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'hotel_secret_key_2024'

DB_PATH = 'hotel.db'

# ─────────────────────────────────────────
#  Database Setup
# ─────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE IF NOT EXISTS rooms (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            number      TEXT UNIQUE NOT NULL,
            type        TEXT NOT NULL,          -- Single, Double, Suite, Deluxe
            price       REAL NOT NULL,
            capacity    INTEGER NOT NULL,
            status      TEXT DEFAULT 'available', -- available, occupied, maintenance
            floor       INTEGER NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS guests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            phone       TEXT,
            id_number   TEXT,
            nationality TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_id     INTEGER NOT NULL,
            room_id      INTEGER NOT NULL,
            check_in     TEXT NOT NULL,
            check_out    TEXT NOT NULL,
            total_price  REAL,
            status       TEXT DEFAULT 'confirmed',  -- confirmed, checked_in, checked_out, cancelled
            notes        TEXT,
            created_at   TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (guest_id) REFERENCES guests(id),
            FOREIGN KEY (room_id)  REFERENCES rooms(id)
        );

        CREATE TABLE IF NOT EXISTS payments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id  INTEGER NOT NULL,
            amount      REAL NOT NULL,
            method      TEXT NOT NULL,           -- cash, card, bank_transfer
            paid_at     TEXT DEFAULT (datetime('now')),
            notes       TEXT,
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        );
    ''')

    # Seed rooms if empty
    c.execute("SELECT COUNT(*) FROM rooms")
    if c.fetchone()[0] == 0:
        rooms = [
            ('101', 'Single',  80,  1, 'available', 1, 'Cozy single room with city view'),
            ('102', 'Single',  80,  1, 'available', 1, 'Quiet single room facing garden'),
            ('103', 'Double', 120,  2, 'available', 1, 'Spacious double room'),
            ('201', 'Double', 130,  2, 'available', 2, 'Double room with balcony'),
            ('202', 'Deluxe', 180,  2, 'available', 2, 'Deluxe room with ocean view'),
            ('203', 'Deluxe', 180,  2, 'maintenance',2,'Under renovation'),
            ('301', 'Suite',  280,  4, 'available', 3, 'Luxury suite with living area'),
            ('302', 'Suite',  300,  4, 'available', 3, 'Presidential suite'),
        ]
        c.executemany(
            "INSERT INTO rooms (number,type,price,capacity,status,floor,description) VALUES (?,?,?,?,?,?,?)",
            rooms
        )

    conn.commit()
    conn.close()

# ─────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────
@app.route('/')
def dashboard():
    conn = get_db()
    c = conn.cursor()

    total_rooms     = c.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
    available_rooms = c.execute("SELECT COUNT(*) FROM rooms WHERE status='available'").fetchone()[0]
    occupied_rooms  = c.execute("SELECT COUNT(*) FROM rooms WHERE status='occupied'").fetchone()[0]
    total_guests    = c.execute("SELECT COUNT(*) FROM guests").fetchone()[0]

    today = date.today().isoformat()
    active_bookings = c.execute(
        "SELECT COUNT(*) FROM bookings WHERE status IN ('confirmed','checked_in')"
    ).fetchone()[0]

    revenue = c.execute(
        "SELECT COALESCE(SUM(amount),0) FROM payments"
    ).fetchone()[0]

    recent_bookings = c.execute('''
        SELECT b.id, g.name, r.number, r.type, b.check_in, b.check_out, b.status, b.total_price
        FROM bookings b
        JOIN guests g ON g.id = b.guest_id
        JOIN rooms  r ON r.id = b.room_id
        ORDER BY b.created_at DESC LIMIT 6
    ''').fetchall()

    conn.close()
    return render_template('dashboard.html',
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        occupied_rooms=occupied_rooms,
        total_guests=total_guests,
        active_bookings=active_bookings,
        revenue=revenue,
        recent_bookings=recent_bookings
    )

# ─────────────────────────────────────────
#  ROOMS
# ─────────────────────────────────────────
@app.route('/rooms')
def rooms():
    conn = get_db()
    rooms = conn.execute("SELECT * FROM rooms ORDER BY number").fetchall()
    conn.close()
    return render_template('rooms.html', rooms=rooms)

@app.route('/rooms/add', methods=['GET','POST'])
def add_room():
    if request.method == 'POST':
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO rooms (number,type,price,capacity,status,floor,description) VALUES (?,?,?,?,?,?,?)",
                (request.form['number'], request.form['type'], float(request.form['price']),
                 int(request.form['capacity']), request.form['status'],
                 int(request.form['floor']), request.form.get('description',''))
            )
            conn.commit()
            flash('Room added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Room number already exists.', 'error')
        finally:
            conn.close()
        return redirect(url_for('rooms'))
    return render_template('room_form.html', room=None)

@app.route('/rooms/edit/<int:room_id>', methods=['GET','POST'])
def edit_room(room_id):
    conn = get_db()
    if request.method == 'POST':
        conn.execute(
            "UPDATE rooms SET number=?,type=?,price=?,capacity=?,status=?,floor=?,description=? WHERE id=?",
            (request.form['number'], request.form['type'], float(request.form['price']),
             int(request.form['capacity']), request.form['status'],
             int(request.form['floor']), request.form.get('description',''), room_id)
        )
        conn.commit()
        conn.close()
        flash('Room updated!', 'success')
        return redirect(url_for('rooms'))
    room = conn.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone()
    conn.close()
    return render_template('room_form.html', room=room)

@app.route('/rooms/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    conn = get_db()
    conn.execute("DELETE FROM rooms WHERE id=?", (room_id,))
    conn.commit()
    conn.close()
    flash('Room deleted.', 'info')
    return redirect(url_for('rooms'))

# ─────────────────────────────────────────
#  GUESTS
# ─────────────────────────────────────────
@app.route('/guests')
def guests():
    conn = get_db()
    guests = conn.execute(
        "SELECT g.*, COUNT(b.id) as total_bookings FROM guests g LEFT JOIN bookings b ON b.guest_id=g.id GROUP BY g.id ORDER BY g.name"
    ).fetchall()
    conn.close()
    return render_template('guests.html', guests=guests)

@app.route('/guests/add', methods=['GET','POST'])
def add_guest():
    if request.method == 'POST':
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO guests (name,email,phone,id_number,nationality) VALUES (?,?,?,?,?)",
                (request.form['name'], request.form['email'], request.form.get('phone',''),
                 request.form.get('id_number',''), request.form.get('nationality',''))
            )
            conn.commit()
            flash('Guest registered!', 'success')
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'error')
        finally:
            conn.close()
        return redirect(url_for('guests'))
    return render_template('guest_form.html', guest=None)

@app.route('/guests/edit/<int:guest_id>', methods=['GET','POST'])
def edit_guest(guest_id):
    conn = get_db()
    if request.method == 'POST':
        conn.execute(
            "UPDATE guests SET name=?,email=?,phone=?,id_number=?,nationality=? WHERE id=?",
            (request.form['name'], request.form['email'], request.form.get('phone',''),
             request.form.get('id_number',''), request.form.get('nationality',''), guest_id)
        )
        conn.commit()
        conn.close()
        flash('Guest updated!', 'success')
        return redirect(url_for('guests'))
    guest = conn.execute("SELECT * FROM guests WHERE id=?", (guest_id,)).fetchone()
    conn.close()
    return render_template('guest_form.html', guest=guest)

@app.route('/guests/delete/<int:guest_id>', methods=['POST'])
def delete_guest(guest_id):
    conn = get_db()
    conn.execute("DELETE FROM guests WHERE id=?", (guest_id,))
    conn.commit()
    conn.close()
    flash('Guest removed.', 'info')
    return redirect(url_for('guests'))

# ─────────────────────────────────────────
#  BOOKINGS
# ─────────────────────────────────────────
@app.route('/bookings')
def bookings():
    conn = get_db()
    bookings = conn.execute('''
        SELECT b.*, g.name as guest_name, r.number as room_number, r.type as room_type
        FROM bookings b
        JOIN guests g ON g.id = b.guest_id
        JOIN rooms  r ON r.id = b.room_id
        ORDER BY b.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('bookings.html', bookings=bookings)

@app.route('/bookings/add', methods=['GET','POST'])
def add_booking():
    conn = get_db()
    if request.method == 'POST':
        guest_id  = int(request.form['guest_id'])
        room_id   = int(request.form['room_id'])
        check_in  = request.form['check_in']
        check_out = request.form['check_out']
        notes     = request.form.get('notes','')

        room  = conn.execute("SELECT price FROM rooms WHERE id=?", (room_id,)).fetchone()
        d1    = datetime.strptime(check_in,  '%Y-%m-%d')
        d2    = datetime.strptime(check_out, '%Y-%m-%d')
        nights = max((d2-d1).days, 1)
        total  = nights * room['price']

        conn.execute(
            "INSERT INTO bookings (guest_id,room_id,check_in,check_out,total_price,notes) VALUES (?,?,?,?,?,?)",
            (guest_id, room_id, check_in, check_out, total, notes)
        )
        conn.execute("UPDATE rooms SET status='occupied' WHERE id=?", (room_id,))
        conn.commit()
        conn.close()
        flash(f'Booking confirmed! Total: ${total:.2f}', 'success')
        return redirect(url_for('bookings'))

    guests = conn.execute("SELECT id,name,email FROM guests ORDER BY name").fetchall()
    rooms  = conn.execute("SELECT id,number,type,price FROM rooms WHERE status='available' ORDER BY number").fetchall()
    conn.close()
    return render_template('booking_form.html', guests=guests, rooms=rooms, booking=None)

@app.route('/bookings/status/<int:booking_id>/<status>', methods=['POST'])
def update_booking_status(booking_id, status):
    conn = get_db()
    conn.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
    if status == 'checked_out' or status == 'cancelled':
        room = conn.execute("SELECT room_id FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if room:
            conn.execute("UPDATE rooms SET status='available' WHERE id=?", (room['room_id'],))
    conn.commit()
    conn.close()
    flash(f'Booking status updated to {status}.', 'success')
    return redirect(url_for('bookings'))

@app.route('/bookings/delete/<int:booking_id>', methods=['POST'])
def delete_booking(booking_id):
    conn = get_db()
    booking = conn.execute("SELECT room_id FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if booking:
        conn.execute("UPDATE rooms SET status='available' WHERE id=?", (booking['room_id'],))
    conn.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()
    flash('Booking deleted.', 'info')
    return redirect(url_for('bookings'))

# ─────────────────────────────────────────
#  PAYMENTS
# ─────────────────────────────────────────
@app.route('/payments')
def payments():
    conn = get_db()
    payments = conn.execute('''
        SELECT p.*, b.total_price, g.name as guest_name, r.number as room_number
        FROM payments p
        JOIN bookings b ON b.id = p.booking_id
        JOIN guests   g ON g.id = b.guest_id
        JOIN rooms    r ON r.id = b.room_id
        ORDER BY p.paid_at DESC
    ''').fetchall()
    conn.close()
    return render_template('payments.html', payments=payments)

@app.route('/payments/add', methods=['GET','POST'])
def add_payment():
    conn = get_db()
    if request.method == 'POST':
        conn.execute(
            "INSERT INTO payments (booking_id,amount,method,notes) VALUES (?,?,?,?)",
            (int(request.form['booking_id']), float(request.form['amount']),
             request.form['method'], request.form.get('notes',''))
        )
        conn.commit()
        conn.close()
        flash('Payment recorded!', 'success')
        return redirect(url_for('payments'))
    bookings = conn.execute('''
        SELECT b.id, g.name, r.number, b.total_price
        FROM bookings b
        JOIN guests g ON g.id=b.guest_id
        JOIN rooms  r ON r.id=b.room_id
        WHERE b.status IN ('confirmed','checked_in')
        ORDER BY b.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('payment_form.html', bookings=bookings)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
