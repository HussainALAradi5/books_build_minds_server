"""Rate limits use Redis in production; forwarded IP headers are not blindly trusted."""
import os
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils.responses import error

def initialize_limits(app):
    storage = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    if os.getenv("APP_ENV") == "production" and not storage.startswith(("redis://", "rediss://")):
        raise RuntimeError("Production requires shared Redis rate-limit storage")
    limiter = Limiter(get_remote_address, app=app, storage_uri=storage, default_limits=["1200 per minute"])
    limiter.exempt(app.view_functions["payments.webhook"])
    for endpoint, rule in {"account.login": "20 per minute", "account.register": "10 per minute",
                           "account.issue_code": "5 per 10 minutes", "account.confirm_code": "10 per 10 minutes",
                           "payments.checkout": "10 per minute", "payments.sync": "30 per minute",
                           "payments.cancel": "10 per minute"}.items():
        app.view_functions[endpoint] = limiter.limit(rule)(app.view_functions[endpoint])
    @app.errorhandler(429)
    def too_many_requests(_exc):
        return error("Too many requests; wait and try again", 429)
    return limiter
