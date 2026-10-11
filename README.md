# Books Builds Minds API

Flask API for accounts, books, purchases, reviews, loans, and media. Python 3.12 is recommended.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
flask --app app init-db
flask --app app db stamp head
flask --app app seed-demo
flask --app app run --port 5000
```

For an existing database created by the previous app, back it up and run `flask --app app db upgrade` instead of `init-db` and `db stamp head`. The migration adds copy counts, loans, and typed media. Check for duplicate reviews or receipts before upgrading because the migration adds unique constraints.

Set a persistent `JWT_SECRET_KEY` and `DATABASE_URL` in `.env` for deployed environments. SQLite is the local default; PostgreSQL is supported through `DATABASE_URL`. Uploads are stored in `static/media`, capped at 5 MB per image and 10 book images per request, with a 25 MB request limit.

Run tests with `python -m unittest discover -s tests -v`.

API pagination returns `{ "items": [...], "pagination": { "page", "per_page", "total", "pages", "has_next", "has_previous" } }`. Book list accepts `q`, `publisher`, `min_price`, `max_price`, and `sort`; loan list accepts `status`. Authentication is required for borrowing, returning, purchases, profile media, and account data. Book media upload requires an admin account.
