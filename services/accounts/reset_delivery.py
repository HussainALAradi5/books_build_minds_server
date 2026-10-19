"""Password reset email delivery. No reset code is returned to the browser."""
import json
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app

LOGGER = logging.getLogger(__name__)
RESEND_URL = "https://api.resend.com/emails"


def delivery_ready():
    if os.getenv("PASSWORD_RESET_DELIVERY") == "console":
        return os.getenv("APP_ENV") != "production"
    return bool(os.getenv("RESEND_API_KEY") and os.getenv("RESEND_FROM_EMAIL"))


def send_reset_code(email, code):
    if os.getenv("PASSWORD_RESET_DELIVERY") == "console":
        if os.getenv("APP_ENV") == "production":
            raise RuntimeError("Console reset delivery is forbidden in production")
        LOGGER.warning("Development password reset code for %s: %s", email, code)
        return
    key, sender = os.getenv("RESEND_API_KEY"), os.getenv("RESEND_FROM_EMAIL")
    if not key or not sender:
        raise RuntimeError("Password reset email delivery is not configured")
    payload = json.dumps({
        "from": sender, "to": [email], "subject": "Books Builds Minds password reset code",
        "text": f"Your password reset code is {code}. It expires in 10 minutes. If you did not request it, ignore this email.",
    }).encode("utf-8")
    request = Request(RESEND_URL, data=payload, method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json",
    })
    try:
        with urlopen(request, timeout=8) as response:
            if response.status >= 300:
                raise RuntimeError("Email provider rejected the reset message")
    except (HTTPError, URLError, TimeoutError) as exc:
        current_app.logger.warning("Password reset email delivery failed: %s", type(exc).__name__)
        raise RuntimeError("Email provider unavailable") from exc
