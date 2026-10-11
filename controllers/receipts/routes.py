from flask import Blueprint

from services.receipts import receipt_service
from utils.security import require_user
from enums.accounts.permission import Permission

receipts = Blueprint("receipts", __name__)
receipts.add_url_rule(
    "/book/<string:slug>/receipt",
    view_func=require_user(Permission.RECEIPT_READ_OWN)(receipt_service.download_receipt),
    methods=["GET"],
)
