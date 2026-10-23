# Demonstration and Viva Guide

## Suggested 5-7 minute live demonstration

1. **Home page:** show the original movie catalogue and future showtimes. Explain that each show is read by joining `shows`, `movies` and `screens`.
2. **Select seats:** choose any upcoming show. Point out that the seat map is loaded from `seats` and checks active ticket rows in `tickets`. Regular seats use the base price, premium seats add ₹50, and recliners add ₹120.
3. **Create a booking:** select an available seat, enter a name/email/phone and choose a simulated payment method. Submit the form. The app inserts/updates a customer, creates a booking, inserts one ticket per seat and creates a payment row.
4. **Show confirmation:** explain the booking ID, seat list, amount and transaction reference. Open the SQLite database or the Reports page to show that rows were inserted.
5. **Prevent double booking:** open the same show in another tab. The seat should display as booked. The database also has a partial unique index on `(show_id, seat_id)` for active tickets, so two requests cannot reserve the same seat.
6. **Cancel:** cancel a booking with the exact email used for it. The booking/tickets become `CANCELLED`, the demo payment becomes `REFUNDED`, and seats become available again. Historical rows remain in the database.
7. **Reports:** show revenue by film, active seat count and show occupancy. Explain that joins and aggregate functions generate these values from database rows, not hard-coded totals.
8. **Admin:** add a temporary movie, edit its description, schedule a show, then cancel the show. Try deleting a movie already used by a show to demonstrate referential integrity. Delete only an unused movie.

## SQL concepts to mention

- **DDL:** `CREATE TABLE`, `CREATE INDEX`, `CREATE TRIGGER` in `schema.sql`.
- **DML:** `INSERT`, `UPDATE` and `DELETE` through booking/admin operations.
- **Primary key:** uniquely identifies each row, such as `movie_id` or `booking_id`.
- **Foreign key:** prevents orphan records; a booking must refer to an existing customer and show.
- **UNIQUE constraint/index:** prevents duplicate customer emails, duplicate screen seats and duplicate active seat bookings.
- **JOIN:** combines booking, customer, show, movie, screen, ticket and payment details.
- **GROUP BY / aggregates:** calculate ticket sales and revenue by movie.
- **Subquery / EXISTS:** detects a booked seat and reports films without confirmed bookings.
- **Transaction:** booking creation either saves every linked record or saves none of them.
- **Normalization:** film details, screen layout, customer information, booking details, tickets and payments live in separate tables rather than being repeated in one giant table.

## Likely viva questions and answers

**Why is `tickets` separate from `bookings`?**  
One booking can contain multiple seats. A separate ticket row per seat avoids storing lists of seat numbers in a single field and allows individual seat validation and pricing.

**Why store `base_price` in `shows` and `seat_price` in `tickets`?**  
The show defines the base price, while premium/recliner seats have surcharges. The ticket stores the final price at the time of booking, so later price changes do not rewrite past transaction values.

**How is a double booking prevented?**  
The Python handler starts an immediate write transaction, rechecks selected seats, and writes the tickets. The partial unique index `uq_active_show_seat` makes `(show_id, seat_id)` unique whenever a ticket status is `BOOKED`. The database is the final guard even if two clients submit close together.

**Why not delete a cancelled booking?**  
Keeping a cancelled row preserves an audit trail. Its ticket rows are also retained with `CANCELLED` status, but the partial unique index no longer treats those seats as actively reserved.

**What does the payment table represent?**  
It stores a simulated payment result and unique transaction reference. There is no real gateway and no money moves.

**What is the limitation?**  
The admin page has no login and the payment integration is simulated. It is a DBMS academic prototype, not production cinema software.

## Evidence to capture before submission

Take your own screenshots from the running app and add them to the final report/slides if required by your faculty:

- Home page with film/show cards.
- Seat map showing available, selected and booked seats.
- Successful booking confirmation.
- Reports page with non-zero sample metrics.
- Admin movie/show operations.

Use the actual running program for evidence rather than screenshots of code or a design mockup.
