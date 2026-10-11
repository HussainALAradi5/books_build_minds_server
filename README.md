# Books Builds Minds — server repository

This is the **server** repository for Books Builds Minds. The matching [client repository](../client/README.md) is a Next.js and Chakra UI application. The separate [documentation repository](../documentation/README.md) maps service signatures, business rules, endpoints, and errors. These links work when the repositories are sibling folders.

## Setup with PostgreSQL and pgAdmin

Create a PostgreSQL database named `books_builds_minds` in pgAdmin. Copy `.env.example` to `.env` and configure `DATABASE_URL`, a long `JWT_SECRET_KEY`, and `CLIENT_ORIGINS`. Keep `.env` out of Git.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\flask.exe --app app db upgrade
.\.venv\Scripts\flask.exe --app app seed-demo
.\.venv\Scripts\python.exe app.py
```

Use the migration command on a new or existing database; back up an existing database first. `seed-demo` creates the sample catalog and demo accounts, generating account passwords in the command output. `seed-demo --reset-passwords` regenerates them. The client reads all demo data from this API.

## Structure and behavior

| Path | Purpose |
| --- | --- |
| `controllers` | `/api` route registration and access guards |
| `services` | Library business logic and database operations |
| `models` and `migrations` | SQLAlchemy entities and ordered Alembic revisions |
| `dto` | API request and response shapes |
| `enums`, `constants`, `utils` | Shared states, permission defaults, validation, pagination, response helpers, and access expressions |
| `tests` | Logic and API tests |

The API supports books, authors, publishers, countries, media, purchases and receipts, borrow/rent/return workflows, and purchase-gated reviews. Reviews use Socket.IO updates. Mutations use archive or soft delete where applicable. `BaseEntity` carries creator, updater, timestamps, `is_archived`, and `is_deleted`. List endpoints use server-side filters, sorting, and pagination.

Access rules use persistent permission keys, roles, and groups. `all_of`, `any_of`, ownership, and purchase checks are evaluated by the server. Registration defaults to the `client` account role; demo seeding also creates admin, employee, and inactive visitor records. Built-in roles and permissions are seeded by migration `c9f1d82b0008`. Only authorized administrators can manage access records. The admin UI is at `/admin/access` in the client.

Country records can be synced through `POST /api/countries/sync` from [countries.dev](https://countries.dev/docs/api/countries). Admin inventory endpoints provide import, export to PDF/XLSX/CSV, and bulk actions.

## Verify

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\flask.exe --app app db check
```

See [ordered migrations](../documentation/database/migrations.md), [feature endpoint tables](../documentation/README.md), and the [client screenshots](../client/docs/screenshots/README.md). No GitHub remote is configured yet; add one after creating the server GitHub repository.
