# Books Builds Minds API

Flask API for the library catalog, accounts, media, reviews, loans, rentals, purchases, and administrative inventory actions.

## PostgreSQL and pgAdmin

Create a PostgreSQL database named `books_builds_minds` in pgAdmin, then set `DATABASE_URL` in `.env` using your PostgreSQL account:

```text
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/books_builds_minds
JWT_SECRET_KEY=replace-with-a-long-random-secret
CLIENT_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

The local database is already created and populated with six server-side seed books. Open pgAdmin and register the local server (`localhost`, port `5432`) to browse it. Never commit `.env`.

For a fresh database, install dependencies and initialize the schema:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\flask.exe --app app init-db
.\.venv\Scripts\flask.exe --app app db stamp head
.\.venv\Scripts\flask.exe --app app seed-demo
.\.venv\Scripts\python.exe app.py
```

Use `flask --app app db upgrade` for an existing database. Back it up first. To inspect or apply each migration individually, run these revisions in order:

```powershell
flask --app app db upgrade 4280997db745
flask --app app db upgrade b47f19d54a13
flask --app app db upgrade c8ad12e960b0
flask --app app db upgrade 3d636ddd36b6
flask --app app db upgrade 5a24f7c7e001
flask --app app db upgrade 6b35f8d8e002
flask --app app db upgrade 7c46a9e9f003
flask --app app db upgrade 8d57bafa0004
flask --app app db upgrade 9e68cb0b0005
flask --app app db upgrade af79dc1c0006
flask --app app db upgrade b8e0c71a0007
```

The later revisions add shared archive/delete state, the former separate comments and ratings, author/publisher/country records, rental workflow, consolidated purchase-gated reviews, shared audit fields, and canonical user roles. The review migration preserves standalone legacy entries as archived review history. The existing SQLite copy was backed up and upgraded one revision at a time; the catalog data was also moved to PostgreSQL.

## API behavior

List endpoints use the shared pagination and sort utilities. Responses have `items` and `pagination`; clients may send `page`, `per_page`, `sort_direction`, and endpoint-specific filters. The client converts these wire names to camelCase. Admin inventory endpoints provide server-generated PDF, XLSX, and CSV exports, CSV/XLSX import, and bulk archive/unarchive/soft-delete. Purchasers may write one active review per book with rating, comment, and optional description. Its author or an admin may edit or soft-delete it. Book edits require an admin. Review updates are broadcast through Socket.IO book rooms. All model DTOs include shared creator, updater, timestamp, archive, and delete fields.

Uploads are stored in `static/media`; image and request-size limits are enforced by the server. Authentication is required for private actions. `seed-demo` is the single source of sample catalog data.

Registration creates a `client` account. Demo seeding creates admin, employee, and client accounts with generated passwords, plus an inactive visitor record. Anonymous visitors browse the public catalog; employees have standard account permissions until employee-specific workflows are introduced. Only admins can edit books and manage inventory.

Administrators can sync country names, ISO codes, and flag URLs from the [countries.dev API](https://countries.dev/docs/api/countries) through `POST /api/countries/sync`. The client reads the locally stored country table.

Run tests with `python -m unittest discover -s tests -v` and check schema drift with `flask --app app db check`.
