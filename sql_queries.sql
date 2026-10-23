-- Cinema Hall Ticket Booking System: query demonstration set
-- Run against cinema.db after starting the Flask app once, or execute the
-- schema and application seed process first. All destructive examples are
-- commented out so that demonstrating queries does not erase project data.

-- Q1. READ: Browse upcoming showtimes with movie and screen details.
SELECT sh.show_id, m.title, m.language, m.duration_minutes,
       sh.show_date, sh.start_time, sc.screen_name, sh.base_price
FROM shows AS sh
JOIN movies AS m ON m.movie_id = sh.movie_id
JOIN screens AS sc ON sc.screen_id = sh.screen_id
WHERE sh.status = 'SCHEDULED'
ORDER BY sh.show_date, sh.start_time, m.title;

-- Q2. READ: Show the seat map with current booking status for one show.
-- Replace 1 with a valid show_id.
SELECT s.seat_number, s.seat_type,
       CASE WHEN EXISTS (
           SELECT 1 FROM tickets t
           WHERE t.show_id = 1 AND t.seat_id = s.seat_id AND t.status = 'BOOKED'
       ) THEN 'BOOKED' ELSE 'AVAILABLE' END AS seat_status
FROM seats s
JOIN shows sh ON sh.screen_id = s.screen_id
WHERE sh.show_id = 1
ORDER BY s.seat_number;

-- Q3. CREATE: Insert a movie. Change the values to avoid duplicate demo data.
-- INSERT INTO movies (title, genre, language, duration_minutes, certificate, release_date, description)
-- VALUES ('Example Film', 'Drama', 'Hindi', 124, 'UA', '2026-01-01', 'Demonstration record.');

-- Q4. UPDATE: Change a movie's description.
-- UPDATE movies SET description = 'Updated synopsis.' WHERE movie_id = 1;

-- Q5. DELETE: Delete only a movie that has no shows/bookings referencing it.
-- DELETE FROM movies WHERE movie_id = <unused_movie_id>;

-- Q6. JOIN: Detailed booking receipt (customer + film + show + screen + tickets + payment).
SELECT b.booking_id, c.full_name, c.email, m.title, sh.show_date, sh.start_time,
       sc.screen_name, GROUP_CONCAT(s.seat_number, ', ') AS seats,
       b.total_amount, b.status AS booking_status,
       p.payment_method, p.payment_status, p.transaction_ref
FROM bookings b
JOIN customers c ON c.customer_id = b.customer_id
JOIN shows sh ON sh.show_id = b.show_id
JOIN movies m ON m.movie_id = sh.movie_id
JOIN screens sc ON sc.screen_id = sh.screen_id
LEFT JOIN tickets t ON t.booking_id = b.booking_id
LEFT JOIN seats s ON s.seat_id = t.seat_id
LEFT JOIN payments p ON p.booking_id = b.booking_id
GROUP BY b.booking_id
ORDER BY b.booking_time DESC;

-- Q7. AGGREGATION: Revenue and tickets sold per movie (confirmed bookings only).
SELECT m.title,
       COUNT(DISTINCT b.booking_id) AS confirmed_bookings,
       COUNT(t.ticket_id) AS seats_sold,
       ROUND(COALESCE(SUM(t.seat_price), 0), 2) AS ticket_revenue
FROM movies m
LEFT JOIN shows sh ON sh.movie_id = m.movie_id
LEFT JOIN bookings b ON b.show_id = sh.show_id AND b.status = 'CONFIRMED'
LEFT JOIN tickets t ON t.booking_id = b.booking_id AND t.status = 'BOOKED'
GROUP BY m.movie_id, m.title
ORDER BY ticket_revenue DESC, seats_sold DESC;

-- Q8. SHOW OCCUPANCY: Booked seats versus total capacity for every scheduled show.
SELECT sh.show_id, m.title, sh.show_date, sh.start_time, sc.screen_name,
       sc.total_seats,
       COUNT(t.ticket_id) AS booked_seats,
       sc.total_seats - COUNT(t.ticket_id) AS available_seats,
       ROUND(100.0 * COUNT(t.ticket_id) / NULLIF(sc.total_seats, 0), 1) AS occupancy_pct
FROM shows sh
JOIN movies m ON m.movie_id = sh.movie_id
JOIN screens sc ON sc.screen_id = sh.screen_id
LEFT JOIN tickets t ON t.show_id = sh.show_id AND t.status = 'BOOKED'
WHERE sh.status = 'SCHEDULED'
GROUP BY sh.show_id, m.title, sh.show_date, sh.start_time, sc.screen_name, sc.total_seats
ORDER BY sh.show_date, sh.start_time;

-- Q9. SUBQUERY: Identify films that have never received a confirmed booking.
SELECT m.movie_id, m.title
FROM movies m
WHERE NOT EXISTS (
    SELECT 1
    FROM shows sh
    JOIN bookings b ON b.show_id = sh.show_id
    WHERE sh.movie_id = m.movie_id AND b.status = 'CONFIRMED'
);

-- Q10. TRANSACTION example (the application does this atomically in Python).
-- Capture the booking_id returned by the first INSERT and bind that same ID to
-- every ticket and payment INSERT; do not call last_insert_rowid() after the
-- ticket INSERT because it then returns a ticket_id, not the booking_id.
-- BEGIN IMMEDIATE;
-- INSERT INTO bookings (customer_id, show_id, total_amount) VALUES (1, 1, 360.00);
-- Assume the returned booking_id is 42 for this illustrative example:
-- INSERT INTO tickets (booking_id, show_id, seat_id, seat_price) VALUES (42, 1, 1, 180.00);
-- INSERT INTO tickets (booking_id, show_id, seat_id, seat_price) VALUES (42, 1, 2, 180.00);
-- INSERT INTO payments (booking_id, amount, payment_method, payment_status, transaction_ref)
-- VALUES (42, 360.00, 'UPI', 'PAID', 'DEMO-TRANSACTION-001');
-- COMMIT;
-- If any step fails, use ROLLBACK. The app implements rollback on errors.

-- Q11. DATA INSERTION: Inspect the sample records created on first launch.
SELECT 'movies' AS table_name, COUNT(*) AS row_count FROM movies
UNION ALL SELECT 'screens', COUNT(*) FROM screens
UNION ALL SELECT 'seats', COUNT(*) FROM seats
UNION ALL SELECT 'shows', COUNT(*) FROM shows
UNION ALL SELECT 'customers', COUNT(*) FROM customers
UNION ALL SELECT 'bookings', COUNT(*) FROM bookings
UNION ALL SELECT 'tickets', COUNT(*) FROM tickets
UNION ALL SELECT 'payments', COUNT(*) FROM payments;
