"""ReelVault Cinema: a DBMS mini-project built with Flask and SQLite.

Academic demo application. It simulates payment outcomes; it does not charge money.
"""
from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
KOLKATA = ZoneInfo("Asia/Kolkata")


def now_local() -> datetime:
    return datetime.now(KOLKATA).replace(tzinfo=None)


def connect_database(database_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path, timeout=8, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 8000")
    return connection


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect_database(str(g._database_path))
    return g.db


def price_for_seat(base_price: float, seat_type: str) -> float:
    surcharges = {"REGULAR": 0, "PREMIUM": 50, "RECLINER": 120}
    return round(float(base_price) + surcharges.get(seat_type, 0), 2)


def seed_demo_data(db: sqlite3.Connection) -> None:
    """Load original sample films, three screens, 144 seats and future shows."""
    movies = [
        ("The Last Monsoon", "Drama", "Hindi", 128, "UA", "2026-08-14",
         "Two estranged siblings return to their coastal hometown before the monsoon arrives."),
        ("Orbit Nine", "Sci-Fi", "English", 116, "UA", "2026-08-21",
         "A small research crew receives a signal that appears to predict their next decisions."),
        ("City of Echoes", "Thriller", "Hindi", 134, "A", "2026-09-04",
         "A journalist follows a missing-person case through a city full of contradictory stories."),
        ("Paper Kingdom", "Family", "Marathi", 109, "U", "2026-08-28",
         "A family-run print shop tries to survive after its neighbourhood starts changing."),
        ("The Silent Signal", "Mystery", "English", 121, "UA", "2026-09-11",
         "An audio engineer uncovers a pattern hidden inside recordings from an abandoned station."),
        ("Chai and Satellites", "Comedy", "Hindi", 102, "U", "2026-09-18",
         "A tea-stall owner and an amateur astronomer accidentally start a very local space race."),
    ]
    db.executemany(
        "INSERT INTO movies (title, genre, language, duration_minutes, certificate, release_date, description) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)", movies
    )

    for index in range(1, 4):
        db.execute("INSERT INTO screens (screen_name, total_seats) VALUES (?, ?)", (f"Screen {index}", 48))
    screens = db.execute("SELECT screen_id FROM screens ORDER BY screen_id").fetchall()
    for screen in screens:
        for row_letter in "ABCDEF":
            seat_type = "REGULAR" if row_letter in "ABCD" else ("PREMIUM" if row_letter == "E" else "RECLINER")
            for number in range(1, 9):
                db.execute(
                    "INSERT INTO seats (screen_id, seat_number, seat_type) VALUES (?, ?, ?)",
                    (screen["screen_id"], f"{row_letter}{number:02d}", seat_type),
                )

    movie_rows = db.execute("SELECT movie_id FROM movies ORDER BY movie_id").fetchall()
    movie_ids = [row["movie_id"] for row in movie_rows]
    schedule = [("10:30", 180.0), ("14:15", 240.0), ("18:45", 300.0)]
    start_day = now_local().date()
    for day_index in range(14):
        show_date = (start_day + timedelta(days=day_index)).isoformat()
        for slot_index, (start_time, base_price) in enumerate(schedule):
            for screen_index, screen in enumerate(screens):
                movie_index = (day_index + slot_index + screen_index) % len(movie_ids)
                db.execute(
                    "INSERT INTO shows (movie_id, screen_id, show_date, start_time, base_price) VALUES (?, ?, ?, ?, ?)",
                    (movie_ids[movie_index], screen["screen_id"], show_date, start_time, base_price),
                )

    # Clearly-labelled sample records make the joins and reports demonstrate non-zero output.
    demo_customers = [
        ("Demo Guest One", "demo.one@example.com", "9000000001"),
        ("Demo Guest Two", "demo.two@example.com", "9000000002"),
        ("Demo Guest Three", "demo.three@example.com", "9000000003"),
    ]
    for customer in demo_customers:
        db.execute("INSERT INTO customers (full_name, email, phone) VALUES (?, ?, ?)", customer)

    demo_specs = [
        (1, "10:30", 1, ["A01", "A02"], "demo.one@example.com", "UPI"),
        (1, "14:15", 2, ["B01", "E01"], "demo.two@example.com", "CARD"),
        (2, "18:45", 3, ["C01"], "demo.three@example.com", "UPI"),
    ]
    for day_offset, show_time, screen_id, seat_numbers, email, payment_method in demo_specs:
        show_date = (start_day + timedelta(days=day_offset)).isoformat()
        show = db.execute(
            "SELECT show_id, base_price FROM shows WHERE show_date = ? AND start_time = ? AND screen_id = ?",
            (show_date, show_time, screen_id),
        ).fetchone()
        if not show:
            continue
        customer = db.execute("SELECT customer_id FROM customers WHERE email = ?", (email,)).fetchone()
        placeholders = ",".join("?" for _ in seat_numbers)
        seats = db.execute(
            f"SELECT seat_id, seat_number, seat_type FROM seats WHERE screen_id = ? AND seat_number IN ({placeholders})",
            (screen_id, *seat_numbers),
        ).fetchall()
        prices = [price_for_seat(show["base_price"], seat["seat_type"]) for seat in seats]
        total = round(sum(prices), 2)
        cur = db.execute(
            "INSERT INTO bookings (customer_id, show_id, total_amount) VALUES (?, ?, ?)",
            (customer["customer_id"], show["show_id"], total),
        )
        booking_id = cur.lastrowid
        for seat, seat_price in zip(seats, prices):
            db.execute(
                "INSERT INTO tickets (booking_id, show_id, seat_id, seat_price, status) VALUES (?, ?, ?, ?, 'BOOKED')",
                (booking_id, show["show_id"], seat["seat_id"], seat_price),
            )
        db.execute(
            "INSERT INTO payments (booking_id, amount, payment_method, payment_status, transaction_ref) "
            "VALUES (?, ?, ?, 'PAID', ?)",
            (booking_id, total, payment_method, f"DEMO-RV-{booking_id:05d}"),
        )


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("CINEMA_SECRET_KEY", "academic-demo-key-change-before-deployment"),
        DATABASE=os.environ.get("CINEMA_DB_PATH", str(BASE_DIR / "instance" / "cinema.db")),
    )
    if test_config:
        app.config.update(test_config)

    db_path = Path(app.config["DATABASE"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = connect_database(str(db_path))
    db.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))
    movie_count = db.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    if movie_count == 0:
        seed_demo_data(db)
    db.close()

    @app.before_request
    def attach_database_path() -> None:
        g._database_path = app.config["DATABASE"]

    @app.teardown_appcontext
    def close_db(_error: Exception | None = None) -> None:
        connection = g.pop("db", None)
        if connection is not None:
            if connection.in_transaction:
                connection.rollback()
            connection.close()

    @app.context_processor
    def inject_globals() -> dict:
        return {"current_year": now_local().year, "current_date": now_local().date().isoformat(),
                "tomorrow_date": (now_local().date() + timedelta(days=1)).isoformat()}

    @app.template_filter("pretty_date")
    def pretty_date(value: str) -> str:
        try:
            return datetime.strptime(value, "%Y-%m-%d").strftime("%a, %d %b")
        except (ValueError, TypeError):
            return value or ""

    @app.template_filter("pretty_time")
    def pretty_time(value: str) -> str:
        try:
            return datetime.strptime(value, "%H:%M").strftime("%I:%M %p")
        except (ValueError, TypeError):
            return value or ""

    @app.template_filter("inr")
    def inr(value: float | int | None) -> str:
        return f"₹{float(value or 0):,.0f}"

    def show_is_future(show_row: sqlite3.Row) -> bool:
        starts = datetime.strptime(f"{show_row['show_date']} {show_row['start_time']}", "%Y-%m-%d %H:%M")
        return starts >= now_local().replace(second=0, microsecond=0)

    def get_show_details(show_id: int) -> sqlite3.Row | None:
        return get_db().execute(
            """SELECT sh.*, m.title, m.genre, m.language, m.duration_minutes, m.certificate,
                      sc.screen_name, sc.total_seats
               FROM shows sh JOIN movies m ON m.movie_id = sh.movie_id
               JOIN screens sc ON sc.screen_id = sh.screen_id
               WHERE sh.show_id = ?""",
            (show_id,),
        ).fetchone()

    @app.route("/")
    def index():
        db = get_db()
        current = now_local()
        today, clock = current.date().isoformat(), current.strftime("%H:%M")
        movies = db.execute("SELECT * FROM movies ORDER BY title").fetchall()
        shows = db.execute(
            """SELECT sh.show_id, sh.movie_id, sh.show_date, sh.start_time, sh.base_price,
                      m.title, m.genre, m.language, m.duration_minutes, m.certificate,
                      sc.screen_name,
                      (SELECT COUNT(*) FROM tickets t WHERE t.show_id = sh.show_id AND t.status = 'BOOKED') AS booked_seats,
                      sc.total_seats
               FROM shows sh JOIN movies m ON m.movie_id = sh.movie_id
               JOIN screens sc ON sc.screen_id = sh.screen_id
               WHERE sh.status = 'SCHEDULED'
                 AND (sh.show_date > ? OR (sh.show_date = ? AND sh.start_time >= ?))
               ORDER BY sh.show_date, sh.start_time, sc.screen_name
               LIMIT 120""",
            (today, today, clock),
        ).fetchall()
        shows_by_movie: dict[int, list[sqlite3.Row]] = {}
        for show in shows:
            shows_by_movie.setdefault(show["movie_id"], []).append(show)
        return render_template("index.html", movies=movies, shows_by_movie=shows_by_movie,
                               today=today, show_count=len(shows))

    @app.route("/book/<int:show_id>", methods=["GET", "POST"])
    def book_show(show_id: int):
        db = get_db()
        show = get_show_details(show_id)
        if not show or show["status"] != "SCHEDULED":
            abort(404)
        if not show_is_future(show):
            flash("That show has already started. Choose an upcoming showtime.", "error")
            return redirect(url_for("index"))

        if request.method == "POST":
            name = " ".join(request.form.get("full_name", "").split())
            email = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip()
            payment_method = request.form.get("payment_method", "UPI").upper()
            raw_seat_ids = request.form.getlist("seat_ids")
            try:
                seat_ids = list(dict.fromkeys(int(value) for value in raw_seat_ids))
            except ValueError:
                seat_ids = []
            if not name or len(name) > 100 or "@" not in email or len(email) > 160 or len(phone) < 7 or len(phone) > 20:
                flash("Enter a name, a valid email address and a phone number (7-20 characters).", "error")
                return redirect(url_for("book_show", show_id=show_id))
            if not (1 <= len(seat_ids) <= 8):
                flash("Select between 1 and 8 seats for one booking.", "error")
                return redirect(url_for("book_show", show_id=show_id))
            if payment_method not in {"UPI", "CARD", "CASH"}:
                flash("Choose UPI, card or cash for the simulated payment.", "error")
                return redirect(url_for("book_show", show_id=show_id))

            placeholders = ",".join("?" for _ in seat_ids)
            selected = db.execute(
                f"SELECT seat_id, seat_number, seat_type FROM seats WHERE screen_id = ? AND seat_id IN ({placeholders}) ORDER BY seat_number",
                (show["screen_id"], *seat_ids),
            ).fetchall()
            if len(selected) != len(seat_ids):
                flash("One or more selected seats do not belong to this screen.", "error")
                return redirect(url_for("book_show", show_id=show_id))

            prices = {seat["seat_id"]: price_for_seat(show["base_price"], seat["seat_type"]) for seat in selected}
            total = round(sum(prices.values()), 2)
            try:
                db.execute("BEGIN IMMEDIATE")
                # Recheck inside the write transaction to prevent double booking.
                occupied = db.execute(
                    f"SELECT seat_id FROM tickets WHERE show_id = ? AND status = 'BOOKED' AND seat_id IN ({placeholders})",
                    (show_id, *seat_ids),
                ).fetchall()
                if occupied:
                    db.rollback()
                    flash("At least one seat was just booked by someone else. Refresh the seat map and try again.", "error")
                    return redirect(url_for("book_show", show_id=show_id))
                db.execute(
                    "INSERT INTO customers (full_name, email, phone) VALUES (?, ?, ?) "
                    "ON CONFLICT(email) DO UPDATE SET full_name = excluded.full_name, phone = excluded.phone",
                    (name, email, phone),
                )
                customer = db.execute("SELECT customer_id FROM customers WHERE email = ?", (email,)).fetchone()
                result = db.execute(
                    "INSERT INTO bookings (customer_id, show_id, total_amount, status) VALUES (?, ?, ?, 'CONFIRMED')",
                    (customer["customer_id"], show_id, total),
                )
                booking_id = result.lastrowid
                for seat in selected:
                    db.execute(
                        "INSERT INTO tickets (booking_id, show_id, seat_id, seat_price, status) VALUES (?, ?, ?, ?, 'BOOKED')",
                        (booking_id, show_id, seat["seat_id"], prices[seat["seat_id"]]),
                    )
                transaction_ref = f"RV-{uuid.uuid4().hex[:10].upper()}"
                db.execute(
                    "INSERT INTO payments (booking_id, amount, payment_method, payment_status, transaction_ref) VALUES (?, ?, ?, 'PAID', ?)",
                    (booking_id, total, payment_method, transaction_ref),
                )
                db.commit()
                return redirect(url_for("booking_detail", booking_id=booking_id, new="1"))
            except sqlite3.IntegrityError:
                if db.in_transaction:
                    db.rollback()
                flash("The database rejected that booking because a seat is no longer available. Refresh and retry.", "error")
                return redirect(url_for("book_show", show_id=show_id))
            except sqlite3.Error:
                if db.in_transaction:
                    db.rollback()
                app.logger.exception("Database error during booking")
                flash("The booking could not be completed. No partial booking was saved.", "error")
                return redirect(url_for("book_show", show_id=show_id))

        seat_rows = db.execute(
            """SELECT s.seat_id, s.seat_number, s.seat_type,
                      CASE WHEN EXISTS (
                          SELECT 1 FROM tickets t WHERE t.show_id = ? AND t.seat_id = s.seat_id AND t.status = 'BOOKED'
                      ) THEN 1 ELSE 0 END AS is_booked
               FROM seats s WHERE s.screen_id = ? ORDER BY s.seat_number""",
            (show_id, show["screen_id"]),
        ).fetchall()
        return render_template("book.html", show=show, seats=seat_rows,
                               seat_surcharges={"REGULAR": 0, "PREMIUM": 50, "RECLINER": 120})

    @app.route("/booking/<int:booking_id>")
    def booking_detail(booking_id: int):
        db = get_db()
        booking = db.execute(
            """SELECT b.*, c.full_name, c.email, c.phone, sh.show_date, sh.start_time, sh.status AS show_status,
                      m.title, m.language, m.duration_minutes, sc.screen_name,
                      p.payment_method, p.payment_status, p.transaction_ref, p.paid_at
               FROM bookings b JOIN customers c ON c.customer_id = b.customer_id
               JOIN shows sh ON sh.show_id = b.show_id JOIN movies m ON m.movie_id = sh.movie_id
               JOIN screens sc ON sc.screen_id = sh.screen_id
               LEFT JOIN payments p ON p.booking_id = b.booking_id
               WHERE b.booking_id = ?""",
            (booking_id,),
        ).fetchone()
        if not booking:
            abort(404)
        tickets = db.execute(
            """SELECT s.seat_number, s.seat_type, t.seat_price, t.status
               FROM tickets t JOIN seats s ON s.seat_id = t.seat_id
               WHERE t.booking_id = ? ORDER BY s.seat_number""",
            (booking_id,),
        ).fetchall()
        return render_template("booking_detail.html", booking=booking, tickets=tickets,
                               newly_booked=request.args.get("new") == "1")

    @app.route("/booking/<int:booking_id>/cancel", methods=["POST"])
    def cancel_booking(booking_id: int):
        email = request.form.get("email", "").strip().lower()
        db = get_db()
        booking = db.execute(
            "SELECT b.booking_id, b.status, c.email FROM bookings b JOIN customers c ON c.customer_id = b.customer_id WHERE b.booking_id = ?",
            (booking_id,),
        ).fetchone()
        if not booking or booking["email"].lower() != email:
            flash("Booking ID and email did not match. Cancellation was not performed.", "error")
            return redirect(url_for("booking_detail", booking_id=booking_id))
        if booking["status"] == "CANCELLED":
            flash("This booking is already cancelled.", "info")
            return redirect(url_for("booking_detail", booking_id=booking_id))
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("UPDATE bookings SET status = 'CANCELLED' WHERE booking_id = ?", (booking_id,))
            db.execute("UPDATE tickets SET status = 'CANCELLED' WHERE booking_id = ?", (booking_id,))
            db.execute("UPDATE payments SET payment_status = 'REFUNDED' WHERE booking_id = ?", (booking_id,))
            db.commit()
            flash("Booking cancelled. Payment status is marked REFUNDED for this simulation.", "success")
        except sqlite3.Error:
            db.rollback()
            flash("Cancellation failed; the database transaction was rolled back.", "error")
        return redirect(url_for("booking_detail", booking_id=booking_id))

    @app.route("/lookup", methods=["GET", "POST"])
    def lookup_booking():
        if request.method == "POST":
            raw_id = request.form.get("booking_id", "").strip()
            email = request.form.get("email", "").strip().lower()
            if not raw_id.isdigit():
                flash("Enter the numeric booking ID shown on the confirmation page.", "error")
                return redirect(url_for("lookup_booking"))
            booking = get_db().execute(
                "SELECT b.booking_id FROM bookings b JOIN customers c ON c.customer_id = b.customer_id WHERE b.booking_id = ? AND lower(c.email) = lower(?)",
                (int(raw_id), email),
            ).fetchone()
            if not booking:
                flash("No booking matched that ID and email combination.", "error")
                return redirect(url_for("lookup_booking"))
            return redirect(url_for("booking_detail", booking_id=booking["booking_id"]))
        return render_template("lookup.html")

    @app.route("/reports")
    def reports():
        db = get_db()
        metrics = db.execute(
            """SELECT
                 (SELECT COUNT(*) FROM bookings WHERE status = 'CONFIRMED') AS confirmed_bookings,
                 (SELECT COUNT(*) FROM tickets WHERE status = 'BOOKED') AS seats_sold,
                 (SELECT ROUND(COALESCE(SUM(amount), 0), 2) FROM payments WHERE payment_status = 'PAID') AS gross_collection,
                 (SELECT COUNT(*) FROM movies) AS movie_count,
                 (SELECT COUNT(*) FROM shows WHERE status = 'SCHEDULED') AS scheduled_shows"""
        ).fetchone()
        film_stats = db.execute(
            """SELECT m.title,
                      COUNT(DISTINCT CASE WHEN b.status = 'CONFIRMED' THEN b.booking_id END) AS bookings,
                      COUNT(CASE WHEN t.status = 'BOOKED' AND b.status = 'CONFIRMED' THEN t.ticket_id END) AS seats_sold,
                      ROUND(COALESCE(SUM(CASE WHEN t.status = 'BOOKED' AND b.status = 'CONFIRMED' THEN t.seat_price ELSE 0 END), 0), 2) AS revenue
               FROM movies m LEFT JOIN shows sh ON sh.movie_id = m.movie_id
               LEFT JOIN bookings b ON b.show_id = sh.show_id
               LEFT JOIN tickets t ON t.booking_id = b.booking_id
               GROUP BY m.movie_id ORDER BY revenue DESC, seats_sold DESC, m.title"""
        ).fetchall()
        occupancy = db.execute(
            """SELECT sh.show_id, m.title, sh.show_date, sh.start_time, sc.screen_name, sc.total_seats,
                      COUNT(t.ticket_id) AS booked_seats,
                      sc.total_seats - COUNT(t.ticket_id) AS available_seats,
                      ROUND(100.0 * COUNT(t.ticket_id) / NULLIF(sc.total_seats, 0), 1) AS occupancy_pct
               FROM shows sh JOIN movies m ON m.movie_id = sh.movie_id
               JOIN screens sc ON sc.screen_id = sh.screen_id
               LEFT JOIN tickets t ON t.show_id = sh.show_id AND t.status = 'BOOKED'
               WHERE sh.status = 'SCHEDULED'
               GROUP BY sh.show_id ORDER BY sh.show_date, sh.start_time, sc.screen_name LIMIT 24"""
        ).fetchall()
        recent = db.execute(
            """SELECT b.booking_id, c.full_name, m.title, sh.show_date, sh.start_time,
                      b.total_amount, b.status, p.payment_method, p.payment_status
               FROM bookings b JOIN customers c ON c.customer_id = b.customer_id
               JOIN shows sh ON sh.show_id = b.show_id JOIN movies m ON m.movie_id = sh.movie_id
               LEFT JOIN payments p ON p.booking_id = b.booking_id
               ORDER BY b.booking_time DESC LIMIT 12"""
        ).fetchall()
        max_revenue = max((float(row["revenue"] or 0) for row in film_stats), default=0)
        return render_template("reports.html", metrics=metrics, film_stats=film_stats,
                               occupancy=occupancy, recent=recent, max_revenue=max_revenue)

    @app.route("/admin")
    def admin():
        db = get_db()
        movies = db.execute("SELECT * FROM movies ORDER BY title").fetchall()
        screens = db.execute("SELECT * FROM screens ORDER BY screen_id").fetchall()
        shows = db.execute(
            """SELECT sh.*, m.title, sc.screen_name
               FROM shows sh JOIN movies m ON m.movie_id = sh.movie_id
               JOIN screens sc ON sc.screen_id = sh.screen_id
               ORDER BY sh.show_date DESC, sh.start_time DESC LIMIT 50"""
        ).fetchall()
        return render_template("admin.html", movies=movies, screens=screens, shows=shows)

    @app.route("/admin/movies/add", methods=["POST"])
    def admin_add_movie():
        fields = [request.form.get(key, "").strip() for key in
                  ("title", "genre", "language", "duration_minutes", "certificate", "release_date", "description")]
        title, genre, language, duration, certificate, release_date, description = fields
        try:
            duration_minutes = int(duration)
            if not title or not genre or not language or duration_minutes <= 0:
                raise ValueError
            get_db().execute(
                "INSERT INTO movies (title, genre, language, duration_minutes, certificate, release_date, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (title, genre, language, duration_minutes, certificate or "UA", release_date or None, description),
            )
            flash(f"Movie '{title}' added to the database.", "success")
        except ValueError:
            flash("Movie title, genre, language and a positive duration are required.", "error")
        except sqlite3.IntegrityError:
            flash("The movie could not be added because a database constraint was violated.", "error")
        return redirect(url_for("admin") + "#movies")

    @app.route("/admin/movies/<int:movie_id>/update", methods=["POST"])
    def admin_update_movie(movie_id: int):
        title = request.form.get("title", "").strip()
        genre = request.form.get("genre", "").strip()
        language = request.form.get("language", "").strip()
        description = request.form.get("description", "").strip()
        try:
            duration = int(request.form.get("duration_minutes", "0"))
        except ValueError:
            duration = 0
        if not title or not genre or not language or duration <= 0:
            flash("Enter valid movie details and a positive duration.", "error")
        else:
            cursor = get_db().execute(
                "UPDATE movies SET title = ?, genre = ?, language = ?, duration_minutes = ?, description = ? WHERE movie_id = ?",
                (title, genre, language, duration, description, movie_id),
            )
            flash("Movie details updated." if cursor.rowcount else "Movie not found.", "success" if cursor.rowcount else "error")
        return redirect(url_for("admin") + "#movies")

    @app.route("/admin/movies/<int:movie_id>/delete", methods=["POST"])
    def admin_delete_movie(movie_id: int):
        try:
            cursor = get_db().execute("DELETE FROM movies WHERE movie_id = ?", (movie_id,))
            if cursor.rowcount:
                flash("Movie deleted. This only works when no show references it.", "success")
            else:
                flash("Movie not found.", "error")
        except sqlite3.IntegrityError:
            flash("This movie is used by one or more shows. Cancel/archive those shows first; the foreign key protected your data.", "error")
        return redirect(url_for("admin") + "#movies")

    @app.route("/admin/shows/add", methods=["POST"])
    def admin_add_show():
        try:
            movie_id = int(request.form.get("movie_id", "0"))
            screen_id = int(request.form.get("screen_id", "0"))
            show_date = request.form.get("show_date", "").strip()
            start_time = request.form.get("start_time", "").strip()
            base_price = float(request.form.get("base_price", "0"))
            datetime.strptime(f"{show_date} {start_time}", "%Y-%m-%d %H:%M")
            if base_price < 0 or datetime.strptime(f"{show_date} {start_time}", "%Y-%m-%d %H:%M") < now_local():
                raise ValueError
            get_db().execute(
                "INSERT INTO shows (movie_id, screen_id, show_date, start_time, base_price, status) VALUES (?, ?, ?, ?, ?, 'SCHEDULED')",
                (movie_id, screen_id, show_date, start_time, base_price),
            )
            flash("Show added and scheduled.", "success")
        except ValueError:
            flash("Enter a future date/time and a non-negative ticket base price.", "error")
        except sqlite3.IntegrityError:
            flash("Could not add the show. Check the movie/screen or whether that screen already has a show at this time.", "error")
        return redirect(url_for("admin") + "#shows")

    @app.route("/admin/shows/<int:show_id>/cancel", methods=["POST"])
    def admin_cancel_show(show_id: int):
        db = get_db()
        show = db.execute("SELECT show_id, status FROM shows WHERE show_id = ?", (show_id,)).fetchone()
        if not show:
            flash("Show not found.", "error")
            return redirect(url_for("admin") + "#shows")
        if show["status"] == "CANCELLED":
            flash("This show is already cancelled.", "info")
            return redirect(url_for("admin") + "#shows")
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("UPDATE shows SET status = 'CANCELLED' WHERE show_id = ?", (show_id,))
            db.execute(
                "UPDATE tickets SET status = 'CANCELLED' WHERE show_id = ? AND status = 'BOOKED'", (show_id,)
            )
            db.execute("UPDATE bookings SET status = 'CANCELLED' WHERE show_id = ? AND status = 'CONFIRMED'", (show_id,))
            db.execute(
                "UPDATE payments SET payment_status = 'REFUNDED' WHERE booking_id IN (SELECT booking_id FROM bookings WHERE show_id = ?)",
                (show_id,),
            )
            db.commit()
            flash("Show cancelled. Linked bookings and simulated payments were updated in one transaction.", "success")
        except sqlite3.Error:
            db.rollback()
            flash("Show cancellation failed; no partial changes were kept.", "error")
        return redirect(url_for("admin") + "#shows")

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    print("\nReelVault Cinema is starting. Open http://127.0.0.1:5000 in your browser.\n")
    app.run(debug=True, use_reloader=False)
