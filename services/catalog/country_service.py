"""Country cache populated from the countries.dev API."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import jsonify, request

from config import db
from models.catalog.Country import Country
from utils.shared.pagination import page_options, paginate, order_query
from utils.shared.responses import error, success
from utils.shared.validation import clean_text

COUNTRIES_API_URL = "https://countries.dev/countries?fields=name,alpha2Code,flags&sort=name"


def list_countries():
    try:
        options = page_options()
        query = Country.query.filter_by(is_deleted=False, is_archived=False)
        term = clean_text(request.args.get("q"), 120)
        if term:
            query = query.filter(Country.name.ilike(f"%{term}%"))
        return jsonify(paginate(order_query(query, Country.name, options), lambda item: item.to_dict(), options))
    except ValueError as exc:
        return error(str(exc))


def sync_countries():
    try:
        with urlopen(Request(COUNTRIES_API_URL, headers={"User-Agent": "BooksBuildsMinds/1.0"}), timeout=10) as response:
            records = json.load(response)
        if not isinstance(records, list) or not records:
            return error("Country provider returned an invalid response", 502)
        count = 0
        for record in records:
            if not isinstance(record, dict):
                continue
            code = record.get("alpha2Code")
            name = record.get("name")
            if not isinstance(code, str) or len(code) != 2 or not isinstance(name, str) or not name:
                continue
            country = db.session.get(Country, code.upper()) or Country(code=code.upper())
            country.name = name[:120]
            flags = record.get("flags")
            country.flag_url = flags.get("svg") if isinstance(flags, dict) else None
            country.is_deleted = False
            country.is_archived = False
            db.session.add(country)
            count += 1
        if not count:
            return error("Country provider returned no usable countries", 502)
        db.session.commit()
        return success("Countries synchronized", count=count)
    except (HTTPError, URLError, TimeoutError, ValueError, TypeError):
        db.session.rollback()
        return error("Country provider unavailable", 502)
