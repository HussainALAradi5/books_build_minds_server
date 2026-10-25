# Books Builds Minds — server repository

This is the **server** repository for Books Builds Minds. The matching [client repository](https://github.com/HussainALAradi5/books_build_minds_client_side/blob/main/README.md) is a Next.js and Chakra UI application. The separate [documentation repository](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/README.md) maps service signatures, business rules, endpoints, and errors. The [Flutter mobile repository](https://github.com/HussainALAradi5/books_build_minds_mobile/blob/main/README.md) uses this API directly. The related repository links point to the published GitHub repositories.

## Related repositories

| Repository | GitHub link | What it contains |
| --- | --- | --- |
| Server | This repository | Flask API, models, migrations, services, and tests |
| Client | [Open client repository](https://github.com/HussainALAradi5/books_build_minds_client_side/blob/main/README.md) | Next.js application and workflow screenshots |
| Mobile | [Open Flutter repository](https://github.com/HussainALAradi5/books_build_minds_mobile/blob/main/README.md) | Mobile reader workflows and Android build |
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

The idempotent demo seed contains 18 books, including 12 clearly fictional test titles with varied conditions, prices, and copy counts. Their author and publisher profiles share books so the creator dialogs show multiple works. Re-run `flask --app app seed-demo` to add missing catalog records without resetting existing account passwords.

## Structure and behavior

| Path | Purpose |
| --- | --- |
| `controllers` | Domain-grouped `/api` route registration and access guards |
| `services` | Domain-grouped library business logic and database operations |
| `models` and `migrations` | Domain-grouped SQLAlchemy entities (accounts, catalog, library, media, reviews, payments, receipts, access) and ordered Alembic revisions |
| `dto` | API request and response shapes |
| `enums`, `constants`, `utils` | Domain-grouped states, permission defaults, validation, pagination, response helpers, and access expressions |
| `tests` | Logic and API tests |

The API supports books, authors, publishers, countries, media, purchases and receipts, borrow/rent/return workflows, and purchase-gated reviews. Reviews use Socket.IO updates. Mutations use archive or soft delete where applicable. `BaseEntity` carries creator, updater, timestamps, `is_archived`, and `is_deleted`. List endpoints use server-side filters, sorting, and pagination.

Access rules use persistent permission keys, roles, and groups. `all_of`, `any_of`, ownership, and purchase checks are evaluated by the server. Registration defaults to the `client` account role; demo seeding also creates admin, employee, and inactive visitor records. Built-in roles and permissions are seeded by migration `c9f1d82b0008`. Only authorized administrators can manage access records. The admin UI is at `/admin/access` in the client.

Country records can be synced through `POST /api/countries/sync` from [countries.dev](https://countries.dev/docs/api/countries). Admin inventory endpoints provide import, export to PDF/XLSX/CSV, and bulk actions.

## Login and password recovery

Login requires a password and accepts email, username, or an optional international mobile number such as `+97312345678`. Registration accepts that mobile number but does not require it. Existing author and publisher profiles reference the locally cached country table; sync countries before selecting one in the admin form.

For local recovery testing, set `PASSWORD_RESET_DELIVERY=console` in `.env` and restart Flask. Request a code at `POST /api/password-reset/request` with `{"identifier":"demo_client"}`. The six-digit code appears in the Flask terminal and expires after 10 minutes. Submit `{"identifier":"demo_client","code":"123456","new_password":"Newpass123"}` to `POST /api/password-reset/confirm`, replacing the example code with the generated one. This changes the account password, so reseed test passwords before continuing demo walkthroughs.

For email delivery, set `RESEND_API_KEY` and `RESEND_FROM_EMAIL` in the server's `.env` using a verified sender. Codes go to the account's saved email even when a mobile number identifies it. No SMS provider is integrated. See the [external API inventory](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/integrations/external-apis.md).

## Verify

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\flask.exe --app app db check
```

See [ordered migrations](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/database/migrations.md), [feature endpoint tables](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/README.md), and the [client screenshots](https://github.com/HussainALAradi5/books_build_minds_client_side/blob/main/docs/screenshots/README.md).

## Security

Book changes require the administrator account role as well as an action permission. Reviews may be changed only by their author or an administrator with the required permission. Delegated permissions cannot bypass those restrictions. Read the [security controls, test coverage, and deployment requirements](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/security/README.md) before exposing a live service.

## Book printing

Public `GET /api/book/<slug>/print` downloads a book record with QR and Code 128 codes. `GET /api/book/<slug>/codes` returns the generated code images. Configure `PUBLIC_CLIENT_URL` to the browser-facing client URL before printing labels. Catalog search accepts the printed `BBM-` identifier. See [printing documentation](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/features/books/printing/README.md).

## Guided borrowing and BHD sandbox payments

Borrowing now requires a server quote, accepted library terms and final confirmation. Purchases and rentals use Tap's BHD sandbox with persisted transactions and immutable PDF receipts. Delete/bulk changes use confirmation dialogs; failed changes remain visible for retry.

See [payment setup, services, endpoint contracts and release limits](https://github.com/HussainALAradi5/books_build_minds_documentation/blob/main/features/payments/README.md). Configure `TAP_SECRET_KEY` and the public HTTPS `TAP_WEBHOOK_URL` on the server. Live keys are rejected. Real sandbox verification still requires your own provider account and webhook. No secrets belong in the client repository.
