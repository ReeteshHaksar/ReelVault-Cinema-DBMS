# ReelVault Cinema - DBMS Mini Project

A runnable cinema-hall movie ticket booking system built with **Python, Flask, SQLite, HTML, CSS and JavaScript**. The database is real and persistent; this is not a static screen mockup.

## What is implemented

- Movie catalogue with language, genre, certificate, duration and synopsis.
- 3 cinema screens, 144 individual seats and 14 days of generated showtimes on first launch.
- Seat-map selection with regular, premium and recliner pricing.
- Booking flow that stores a customer, booking, one ticket row per seat and a payment record.
- Atomic booking transaction (`BEGIN IMMEDIATE`, `COMMIT`/`ROLLBACK`) and a partial unique index that prevents two active tickets for the same seat and show.
- Ticket confirmation page with booking ID, selected seats and payment reference.
- Booking lookup using booking ID plus email.
- Cancellation that marks the booking/tickets cancelled, updates the simulated payment to `REFUNDED`, and frees seats for rebooking while preserving history.
- Admin operations to insert/update/delete eligible movie records, schedule shows and cancel shows. Foreign keys protect records that are still referenced.
- SQL reports for booking count, ticket sales, payment collection, per-film revenue and screen occupancy.
- Original sample films and three clearly labelled demo bookings so reports have meaningful output immediately.
- ER diagram, schema, example SQL queries, report and demonstration guide.

## Requirements

- Python 3.10 or later (Python 3.11+ recommended).
- Internet is needed only if `pip` must download Flask for the first time. The app itself uses a local SQLite database and does not call external APIs.

## Run on Windows

1. Extract the project ZIP into a normal folder.
2. Open that folder in VS Code, or open a terminal in that folder.
3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat`, or skip activation and use `.venv\Scripts\python.exe` directly.

4. Install Flask:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Start the application:

   ```powershell
   python app.py
   ```

6. Open **http://127.0.0.1:5000** in a browser. Keep the terminal open while demonstrating the project.

## Run on macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Then visit `http://127.0.0.1:5000`.

## First launch and database

The app creates `instance/cinema.db` automatically, applies `schema.sql`, and seeds data only when the movie table is empty. The default seed contains:

- 6 original fictional movie records.
- 3 screens and 48 seats per screen (144 seats total).
- 14 days of showtimes across three daily slots.
- 3 sample bookings, with corresponding ticket and simulated payment records.

Sample lookup IDs on a fresh database are **1, 2 and 3**. These are demo records, not real customer data:

| Booking ID | Email |
|---:|---|
| 1 | `demo.one@example.com` |
| 2 | `demo.two@example.com` |
| 3 | `demo.three@example.com` |

The booking page simulates UPI/card/cash selection. It does **not** connect to a payment gateway or charge real money.

## Reset to a clean seed

1. Stop the server with `Ctrl+C`.
2. Delete `instance/cinema.db` (and `instance/cinema.db-shm` / `instance/cinema.db-wal` if present).
3. Run `python app.py` again. A fresh database and seed records are recreated.

Do not delete the file while the application is running.

## Project structure

```text
cinema_dbms_project/
├── app.py                  # Flask routes and booking/business logic
├── schema.sql              # 8 normalized tables, indexes and triggers
├── sql_queries.sql         # joins, CRUD examples, aggregates and subquery
├── requirements.txt
├── templates/              # Jinja HTML templates
├── static/style.css        # responsive UI styling
├── docs/erd.png            # ER diagram for report/presentation
├── docs/erd.svg            # scalable ER diagram
├── docs/erd.dot            # Graphviz source of the diagram
├── tests/test_database.py  # standard-library SQLite integrity tests
├── REPORT.md               # editable report source
├── REPORT.docx             # formatted report for submission editing
├── DEMO_GUIDE.md           # demonstration / viva notes
├── PROJECT_SELECTION_ENTRY.md # text for the faculty Google Sheet
└── start_windows.bat       # optional Windows launcher
```

## Database design at a glance

| Table | Purpose |
|---|---|
| `movies` | Film metadata |
| `screens` | Cinema halls/screens and seat capacity |
| `seats` | Individual screen seats and seat type |
| `shows` | Movie, screen, date, time, price and status |
| `customers` | Customer identity and unique email |
| `bookings` | Customer reservation for one show and total amount |
| `tickets` | One row per reserved seat, with seat price and ticket status |
| `payments` | One simulated payment record per booking |

The complete field definitions, keys, triggers and indexes are in `schema.sql`. The diagram is in `docs/erd.png`.

## Run database integrity tests

The automated tests use only Python's built-in `sqlite3` and `unittest` modules, so they do not require Flask:

```powershell
python -m unittest discover -s tests -v
```

These tests verify foreign keys, show scheduling uniqueness, active-seat uniqueness, cancellation/rebooking and the rule that a ticket's seat must belong to the screen hosting the show.

## Security / academic limitation

This is a local academic prototype. The admin panel has no authentication, customer data is not encrypted, and payment processing is simulated. Do not publish it on a public server without adding login/roles, CSRF protection, input hardening, HTTPS, privacy controls and a real payment integration. The project intentionally focuses on DBMS design and working database operations.
