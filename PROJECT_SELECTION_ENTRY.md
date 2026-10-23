# Topic Selection Sheet Entry

Use the following details in the faculty's Google Sheet. Add actual group member names/roll numbers before submitting.

**Group members:** [Name + roll number, maximum 3 students; or write Individual Project]

**Project title:** Cinema Hall Movie Ticket Booking and Seat Management System

**Problem / Use Case:** A cinema hall needs a centralized database to manage movies, screens, individual seats, show schedules, customer details, bookings, tickets and payment statuses. The system lets a customer select seats and book tickets while preventing duplicate active reservations for the same seat and show. It also supports booking cancellation, admin-side movie/show management and reports for revenue and screen occupancy.

**Database technologies / concepts used:** Python Flask web application; SQLite relational database; ER modelling; normalized tables; primary keys and foreign keys; UNIQUE and CHECK constraints; indexes and triggers; CRUD operations; SQL joins; aggregate functions with GROUP BY; subqueries and EXISTS; transactions with COMMIT/ROLLBACK; referential integrity; data insertion and retrieval.

**Distinctive implementation detail:** A partial unique index prevents duplicate active tickets for a `(show_id, seat_id)` pair, while cancelled ticket history is preserved and the seat can be booked again.
