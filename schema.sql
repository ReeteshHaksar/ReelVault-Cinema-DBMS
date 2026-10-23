PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    genre TEXT NOT NULL,
    language TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    certificate TEXT NOT NULL DEFAULT 'UA',
    release_date TEXT,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS screens (
    screen_id INTEGER PRIMARY KEY AUTOINCREMENT,
    screen_name TEXT NOT NULL UNIQUE,
    total_seats INTEGER NOT NULL DEFAULT 0 CHECK (total_seats >= 0)
);

CREATE TABLE IF NOT EXISTS seats (
    seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    screen_id INTEGER NOT NULL,
    seat_number TEXT NOT NULL,
    seat_type TEXT NOT NULL DEFAULT 'REGULAR'
        CHECK (seat_type IN ('REGULAR', 'PREMIUM', 'RECLINER')),
    FOREIGN KEY (screen_id) REFERENCES screens(screen_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (screen_id, seat_number)
);

CREATE TABLE IF NOT EXISTS shows (
    show_id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    screen_id INTEGER NOT NULL,
    show_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    base_price REAL NOT NULL CHECK (base_price >= 0),
    status TEXT NOT NULL DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED', 'CANCELLED')),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (screen_id) REFERENCES screens(screen_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (screen_id, show_date, start_time)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    phone TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    show_id INTEGER NOT NULL,
    booking_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'CONFIRMED' CHECK (status IN ('CONFIRMED', 'CANCELLED')),
    total_amount REAL NOT NULL CHECK (total_amount >= 0),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (show_id) REFERENCES shows(show_id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    show_id INTEGER NOT NULL,
    seat_id INTEGER NOT NULL,
    seat_price REAL NOT NULL CHECK (seat_price >= 0),
    status TEXT NOT NULL DEFAULT 'BOOKED' CHECK (status IN ('BOOKED', 'CANCELLED')),
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (show_id) REFERENCES shows(show_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (seat_id) REFERENCES seats(seat_id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL UNIQUE,
    amount REAL NOT NULL CHECK (amount >= 0),
    payment_method TEXT NOT NULL CHECK (payment_method IN ('UPI', 'CARD', 'CASH')),
    payment_status TEXT NOT NULL DEFAULT 'PAID' CHECK (payment_status IN ('PAID', 'REFUNDED', 'PENDING')),
    transaction_ref TEXT NOT NULL UNIQUE,
    paid_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_shows_date_time ON shows(show_date, start_time, status);
CREATE INDEX IF NOT EXISTS idx_shows_movie ON shows(movie_id, show_date);
CREATE INDEX IF NOT EXISTS idx_bookings_customer ON bookings(customer_id, booking_time DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_booking ON tickets(booking_id);
CREATE INDEX IF NOT EXISTS idx_tickets_show_status ON tickets(show_id, status);

-- A seat can only have one active ticket for a specific show. Cancelled tickets
-- remain as history but no longer block the seat from being booked again.
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_show_seat
ON tickets(show_id, seat_id)
WHERE status = 'BOOKED';

-- Business-rule validation: a ticket must belong to the booking's show, and
-- the selected seat must belong to the screen hosting that show.
CREATE TRIGGER IF NOT EXISTS trg_ticket_guard_insert
BEFORE INSERT ON tickets
BEGIN
    SELECT CASE
        WHEN (SELECT show_id FROM bookings WHERE booking_id = NEW.booking_id) != NEW.show_id
        THEN RAISE(ABORT, 'Ticket show does not match booking')
    END;
    SELECT CASE
        WHEN (SELECT screen_id FROM shows WHERE show_id = NEW.show_id) !=
             (SELECT screen_id FROM seats WHERE seat_id = NEW.seat_id)
        THEN RAISE(ABORT, 'Seat does not belong to the selected show screen')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_ticket_guard_update
BEFORE UPDATE OF booking_id, show_id, seat_id ON tickets
BEGIN
    SELECT CASE
        WHEN (SELECT show_id FROM bookings WHERE booking_id = NEW.booking_id) != NEW.show_id
        THEN RAISE(ABORT, 'Ticket show does not match booking')
    END;
    SELECT CASE
        WHEN (SELECT screen_id FROM shows WHERE show_id = NEW.show_id) !=
             (SELECT screen_id FROM seats WHERE seat_id = NEW.seat_id)
        THEN RAISE(ABORT, 'Seat does not belong to the selected show screen')
    END;
END;
