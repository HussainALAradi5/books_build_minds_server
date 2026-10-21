from flask import Blueprint

from services.catalog import author_service, country_service, publisher_service
from utils.accounts.security import require_user
from enums.accounts.permission import Permission

catalog = Blueprint("catalog", __name__)
catalog.add_url_rule("/countries", view_func=country_service.list_countries, methods=["GET"])
catalog.add_url_rule("/countries/sync", view_func=require_user(Permission.COUNTRY_SYNC)(country_service.sync_countries), methods=["POST"])
catalog.add_url_rule("/authors", view_func=author_service.list_authors, methods=["GET"])
catalog.add_url_rule("/authors", view_func=require_user(Permission.AUTHOR_WRITE)(author_service.save_author), methods=["POST"])
catalog.add_url_rule("/authors/<int:author_id>", view_func=author_service.get_author, methods=["GET"])
catalog.add_url_rule("/publishers", view_func=publisher_service.list_publishers, methods=["GET"])
catalog.add_url_rule("/publishers", view_func=require_user(Permission.PUBLISHER_WRITE)(publisher_service.save_publisher), methods=["POST"])
catalog.add_url_rule("/publishers/<int:publisher_id>", view_func=publisher_service.get_publisher, methods=["GET"])
