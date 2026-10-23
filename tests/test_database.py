"""SQLite-only integrity tests. Run: python -m unittest discover -s tests -v"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (PROJECT_ROOT / "schema.sql").read_text(encoding="utf-8")


class CinemaDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_cinema.db"
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA)
        self.movie_id = self.db.execute(
            "INSERT INTO movies (title, genre, language, duration_minutes) VALUES ('Test Film', 'Drama', 'Hindi', 120)"
        ).lastrowid
        self.screen_1 = self.db.execute(
            "INSERT INTO screens (screen_name, total_seats) VALUES ('Test Screen 1', 2)"
        ).lastrowid
        self.screen_2 = self.db.execute(
            "INSERT INTO screens (screen_name, total_seats) VALUES ('Test Screen 2', 1)"
        ).lastrowid
        self.seat_1 = self.db.execute(
            "INSERT INTO seats (screen_id, seat_number, seat_type) VALUES (?, 'A01', 'REGULAR')", (self.screen_1,)
        ).lastrowid
        self.seat_2 = self.db.execute(
            "INSERT INTO seats (screen_id, seat_number, seat_type) VALUES (?, 'A02', 'PREMIUM')", (self.screen_1,)
        ).lastrowid
        self.other_screen_seat = self.db.execute(
            "INSERT INTO seats (screen_id, seat_number, seat_type) VALUES (?, 'A01', 'REGULAR')", (self.screen_2,)
        ).lastrowid
        self.show_id = self.db.execute(
            "INSERT INTO shows (movie_id, screen_id, show_date, start_time, base_price) VALUES (?, ?, '2099-01-01', '10:30', 180)",
            (self.movie_id, self.screen_1),
        ).lastrowid
        self.customer_id = self.db.execute(
            "INSERT INTO customers (full_name, email, phone) VALUES ('Test Customer', 'test@example.com', '9000000000')"
        ).lastrowid
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def make_booking(self, amount=180):
        cursor = self.db.execute(
            "INSERT INTO bookings (customer_id, show_id, total_amount) VALUES (?, ?, ?)",
            (self.customer_id, self.show_id, amount),
        )
        return cursor.lastrowid

    def test_core_tables_exist_and_foreign_keys_are_enabled(self):
        expected = {"movies", "screens", "seats", "shows", "customers", "bookings", "tickets", "payments"}
        found = {row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue(expected.issubset(found))
        self.assertEqual(self.db.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_same_screen_cannot_have_two_shows_with_same_start(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO shows (movie_id, screen_id, show_date, start_time, base_price) VALUES (?, ?, '2099-01-01', '10:30', 200)",
                (self.movie_id, self.screen_1),
            )

    def test_same_active_seat_cannot_be_booked_twice_for_show(self):
        booking_one = self.make_booking()
        self.db.execute(
            "INSERT INTO tickets (booking_id, show_id, seat_id, seat_price) VALUES (?, ?, ?, 180)",
            (booking_one, self.show_id, self.seat_1),
        )
        booking_two = self.make_booking()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO tickets (booking_id, show_id, seat_id, seat_price) VALUES (?, ?, ?, 180)",
                (booking_two, self.show_id, self.seat_1),
            )

    def test_cancelled_ticket_releases_seat_but_keeps_history(self):
        booking_one = self.make_booking()
        ticket_id = self.db.execute(
            "INSERT INTO tickets (booking_id, show_id, seat_id, seat_price) VALUES (?, ?, ?, 180)",
            (booking_one, self.show_id, self.seat_1),
        ).lastrowid
        self.db.execute("UPDATE tickets SET status = 'CANCELLED' WHERE ticket_id = ?", (ticket_id,))
        booking_two = self.make_booking()
        self.db.execute(
            "INSERT INTO tickets (booking_id, show_id, seat_id, seat_price) VALUES (?, ?, ?, 180)",
            (booking_two, self.show_id, self.seat_1),
        )
        history = self.db.execute(
            "SELECT COUNT(*) FROM tickets WHERE show_id = ? AND seat_id = ?", (self.show_id, self.seat_1)
        ).fetchone()[0]
        self.assertEqual(history, 2)

    def test_trigger_rejects_seat_from_different_screen(self):
        booking = self.make_booking()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO tickets (booking_id, show_id, seat_id, seat_price) VALUES (?, ?, ?, 180)",
                (booking, self.show_id, self.other_screen_seat),
            )

    def test_foreign_key_blocks_deleting_referenced_movie(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM movies WHERE movie_id = ?", (self.movie_id,))

    def test_duplicate_customer_email_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO customers (full_name, email, phone) VALUES ('Another', 'TEST@example.com', '9111111111')"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
