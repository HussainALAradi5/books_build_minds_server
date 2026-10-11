from flask import Blueprint

from services.receipts import receipt_service
from utils.security import require_user

receipts = Blueprint("receipts", __name__)
receipts.add_url_rule(
    "/book/<string:slug>/receipt",
    view_func=require_user()(receipt_service.download_receipt),
    methods=["GET"],
)
