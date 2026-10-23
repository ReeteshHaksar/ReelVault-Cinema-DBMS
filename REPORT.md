# REELVAULT CINEMA
## Cinema Hall Movie Ticket Booking System
**DBMS Mini Project Report**

**Group Members:** [Enter names and roll numbers]  
**Faculty:** [Enter faculty name]  
**Class / Division:** [Enter class and division]  
**Academic Year:** 2026-2027

## Abstract

ReelVault Cinema is a database-driven web application for managing a cinema hall's movie catalogue, screens, seats, show schedules, customer details, ticket bookings and simulated payments. The prototype uses Python and Flask for the application layer and SQLite as its relational database. It supports seat selection, ticket confirmation, booking lookup, cancellation, catalogue administration and management reports. The main DBMS objective is to keep related information normalized while enforcing referential integrity and preventing two active bookings for the same seat and show.

## 1. Problem Definition

Manual ticket booking can produce duplicate seat allocations, inconsistent booking totals, repeated customer information and slow reporting. A cinema needs one reliable source of truth for movies, screens, seats, scheduled shows, customers, reservations, tickets and payments. The project addresses these issues by implementing a relational database and an interactive web interface. A selected seat is considered unavailable only when an active ticket exists for that specific show and seat.

## 2. Objectives

- Design a normalized relational database for cinema ticket booking.
- Model entity relationships using an ER diagram and primary/foreign keys.
- Implement insertion, retrieval, update, cancellation and deletion operations.
- Display showtime-based seat availability and calculate seat prices by seat type.
- Prevent duplicate active seat bookings using transactions and a unique database index.
- Demonstrate joins, aggregate queries, subqueries, constraints, indexes and triggers.
- Produce reports for booking volume, seats sold, ticket revenue and screen occupancy.

## 3. Scope and Assumptions

The project uses fictional sample films and sample customer records. It provides three screens, 48 seats per screen and fourteen days of generated showtimes on first launch. UPI, card and cash choices simulate a payment outcome; no real payment gateway or charge is performed. The admin page is intended for local classroom demonstration and does not provide login or production-grade security.

## 4. Database Design

The database contains eight core tables:

| Table | Purpose | Key constraints |
|---|---|---|
| `movies` | Movie metadata | `movie_id` primary key; positive duration |
| `screens` | Screens and capacity | `screen_id` primary key; unique screen name |
| `seats` | Individual seats | `seat_id` primary key; screen foreign key; unique seat number per screen |
| `shows` | Screening schedule | movie and screen foreign keys; unique screen/date/time; non-negative base price |
| `customers` | Customer information | `customer_id` primary key; unique email |
| `bookings` | One customer's reservation for one show | customer and show foreign keys; status and non-negative amount checks |
| `tickets` | One record per seat in a booking | booking, show and seat foreign keys; stored seat price and status |
| `payments` | One simulated payment per booking | unique booking foreign key and transaction reference |

Film metadata is stored once in `movies`, screen layout in `screens` and `seats`, and show-specific data in `shows`. Customer data is separated from bookings. A booking can have multiple ticket rows, one per selected seat. Payment data is stored separately and linked one-to-one to a booking. This avoids packing multiple seat numbers into one text field and reduces update anomalies.

## 5. ER Diagram

The ER diagram is provided at `docs/erd.png` and `docs/erd.svg`. It shows the one-to-many and one-to-one relationships among all eight tables. Primary keys are marked `PK`, foreign keys are marked `FK`, and constraints such as unique customer email and active seat booking are documented in the schema.

## 6. Tables and Relationships

- **Movies to Shows (1:N):** one movie can have many scheduled shows; each show refers to one movie.
- **Screens to Shows (1:N):** one screen hosts many shows at different times; a unique constraint prevents overlapping starts for the same screen.
- **Screens to Seats (1:N):** a screen contains its own seat inventory; seat identifiers are unique within each screen.
- **Customers to Bookings (1:N):** one customer can create multiple bookings; each booking belongs to one customer.
- **Shows to Bookings (1:N):** a show can receive multiple bookings; each booking targets one show.
- **Bookings to Tickets (1:N):** a booking can include several seats, stored as separate ticket rows.
- **Seats to Tickets and Shows to Tickets:** ticket records identify the seat and show combination. A trigger verifies that the seat belongs to the screen hosting the show.
- **Bookings to Payments (1:1):** each booking has at most one payment record, enforced by a unique foreign key.

A partial unique index applies only when `tickets.status = 'BOOKED'`. It prevents two active tickets for the same `(show_id, seat_id)` but allows a cancelled seat to be booked again while preserving the cancelled ticket as history.

## 7. SQL Queries

The file `sql_queries.sql` includes a query demonstration set:

1. Upcoming showtimes using joins among shows, movies and screens.
2. Seat availability using `EXISTS`.
3. Insert, update and delete examples for CRUD.
4. A detailed booking receipt assembled using joins and `GROUP_CONCAT`.
5. Revenue and seats sold grouped by movie.
6. Show occupancy using `LEFT JOIN`, `COUNT`, arithmetic and `GROUP BY`.
7. A `NOT EXISTS` subquery to identify films with no confirmed booking.
8. A transaction example corresponding to the application's atomic booking flow.

The queries use parameterized statements in the application where user input is involved. Destructive examples in the SQL file are commented out to protect data during demonstrations.

## 8. Data Insertion and Retrieval

On first launch the application inserts six fictional movie records, three screens, 144 seats, 14 days of scheduled shows and three sample bookings. Sample bookings generate customer, booking, ticket and payment rows. Users can add more movies and shows through the admin page and can create bookings from the movie/show catalogue. All data persists in `instance/cinema.db`.

Retrieval operations include the home-page movie catalogue, upcoming showtimes, a live seat map, ticket confirmation, booking lookup and reports. The report page uses aggregate queries on the database; the totals are recalculated after a booking or cancellation.

## 9. Required Database Operations

| Operation | Where it is demonstrated |
|---|---|
| Create / insert | Add a movie, schedule a show, create customer, booking, tickets and payment |
| Read / select | Catalogue, showtime list, seat map, ticket view, booking lookup and reports |
| Update | Edit movie details; update booking/ticket/payment statuses during cancellation |
| Delete | Delete an unused movie; foreign keys reject deletion of referenced films |
| Join | Ticket receipt and recent-bookings report |
| Aggregate | Revenue by movie, booking counts, tickets sold and show occupancy |
| Transaction | Booking and cancellation are committed together or rolled back on failure |
| Integrity constraints | Primary keys, foreign keys, `UNIQUE`, `CHECK`, triggers and indexes |

## 10. Implementation

- **Frontend:** HTML templates, responsive CSS and small JavaScript interactions for filtering movies and calculating the selected-seat total.
- **Backend:** Python with Flask route handlers for show browsing, booking, lookup, cancellation, reporting and admin operations.
- **Database:** SQLite with foreign key enforcement enabled for each connection.
- **Persistence:** database file stored in the project's `instance/` directory.

For booking, the backend starts an immediate write transaction, checks seat availability again, inserts the customer or updates the existing customer by email, inserts the booking and ticket rows, inserts the payment row, then commits. If a seat has been reserved in the meantime or a database constraint fails, the transaction is rolled back. The front-end seat map is informative, but the database index is the final protection against a duplicate active reservation.

## 11. Output / Demonstration

Demonstration sequence:

1. Open the home page and show movie cards and scheduled times.
2. Open an upcoming show, select a few seats and show the automatically updated total.
3. Confirm a booking and point out the booking ID, seat numbers, payment method and transaction reference.
4. Open the same show again and show that the booked seats are unavailable.
5. Open Reports and show confirmed bookings, active seats, gross simulated collection, per-film revenue and show occupancy.
6. Cancel a booking using the booking email and show the cancelled history and released seats.
7. Use Admin to edit a movie, schedule a screening and cancel a screening.
8. Attempt to delete a movie with existing show references to demonstrate foreign-key protection.

Before submission, capture screenshots from the live local application for the home page, seat map, booking confirmation, reports and admin operations if the faculty requires visual output evidence.

## 12. Testing and Validation

The project includes `tests/test_database.py`, which uses the Python standard library to verify database constraints without needing Flask. The tests cover foreign keys, show-schedule uniqueness, active seat uniqueness, released seats after cancellation, and the trigger that ensures a selected seat belongs to the correct screen. Run them with `python -m unittest discover -s tests -v`.

Additional manual acceptance checks are listed in `DEMO_GUIDE.md`. A clean-install test should include creating a booking, trying to book the same seat twice, cancelling, confirming that the seat becomes available, checking that reports update, and attempting a deletion blocked by a foreign key.

## 13. Limitations and Future Scope

The admin panel has no authentication, payment is simulated, and the prototype has not been designed for production traffic. Future development could add administrator roles, CSRF protection, password hashing, OTP/email notifications, real payment gateway integration, refundable payment workflows, promotions, customer feedback, seat locking with expiry, automated database backups and a production SQL server.

## 14. Conclusion

ReelVault Cinema demonstrates how a real-world ticketing problem can be modeled with a relational database and a functional web interface. It applies normalization, keys, relationships, constraints, indexes, triggers, transactions, CRUD operations, joins, aggregate queries and subqueries. The result is a working academic prototype that maintains consistent booking data, avoids double-booking active seats and provides useful operational reports.
