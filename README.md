# Books Builds Minds — server repository

This is the **server** repository for Books Builds Minds. The matching [client repository](https://github.com/HussainALAradi5/books_build_minds_client_side/blob/main/README.md) is a Next.js and Chakra UI application. The separate [documentation repository](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/README.md) maps service signatures, business rules, endpoints, and errors. The related repository links point to the published GitHub repositories.

## Related repositories

| Repository | GitHub link | What it contains |
| --- | --- | --- |
| Server | This repository | Flask API, models, migrations, services, and tests |
| Client | [Open client repository](https://github.com/HussainALAradi5/books_build_minds_client_side/blob/main/README.md) | Next.js application and workflow screenshots |
| Documentation | [Open documentation repository](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/README.md) | Architecture, setup, service signatures, endpoints, and errors |

The related repository links point to the published GitHub repositories.

## Setup with PostgreSQL and pgAdmin

1. Create a PostgreSQL database named `books_builds_minds` in pgAdmin.
2. Copy `.env.example` to `.env`; configure `DATABASE_URL`, a long `JWT_SECRET_KEY`, and `CLIENT_ORIGINS`. Keep `.env` out of Git.
3. Install Python dependencies, migrate, create the documented local test accounts, and start the API:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m flask --app app db upgrade
   .\.venv\Scripts\python.exe -m flask --app app seed-demo --test-accounts
   .\.venv\Scripts\python.exe app.py
   ```

4. Follow the [client setup](https://github.com/HussainALAradi5/books_build_minds_client_side/blob/main/README.md) to point Next.js at this API and sign in.

Use the migration command on a new or existing database; back up an existing database first. `seed-demo --test-accounts` creates or updates the three active demo logins below, while `seed-demo` alone generates random passwords for new users. `seed-demo --reset-passwords` regenerates random passwords. Demo seeding is refused when `APP_ENV=production`. The client reads all demo data from this API.

| Role | Username | Password | Default access |
| --- | --- | --- | --- |
| Administrator | `demo_admin` | `LibraryAdmin2026!` | All management operations and member workflows |
| Employee | `demo_employee` | `LibraryStaff2026!` | Member workflows; no admin page by default |
| Client | `demo_client` | `LibraryReader2026!` | Own profile, borrow/rent/return, purchase/receipt, and purchased-book reviews |

`demo_visitor` is an inactive record; an anonymous visitor can browse and register. Employee and client start with the same member permissions. An administrator may assign extra access roles and groups; the access management page and API still require the administrator account role.

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

See [ordered migrations](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/database/migrations.md), [feature endpoint tables](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/README.md), and the [client screenshots](https://github.com/HussainALAradi5/books_build_minds_client_side/blob/main/docs/screenshots/README.md). No GitHub remote is configured yet; add one after creating the server GitHub repository.

## Security

Book changes require the administrator account role as well as an action permission. Reviews may be changed only by their author or an administrator with the required permission. Delegated permissions cannot bypass those restrictions. Read the [security controls, test coverage, and deployment requirements](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/security/README.md) before exposing a live service.
