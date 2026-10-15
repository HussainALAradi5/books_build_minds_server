"""Application configuration and shared SQLAlchemy instance."""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", f"sqlite:///{BASE_DIR / 'books.db'}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(48)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
app.config["PUBLIC_CLIENT_URL"] = os.getenv("PUBLIC_CLIENT_URL", "http://localhost:3000")

app.config["TAP_SECRET_KEY"] = os.getenv("TAP_SECRET_KEY", "")
app.config["TAP_WEBHOOK_URL"] = os.getenv("TAP_WEBHOOK_URL", "")

if os.getenv("APP_ENV") == "production":
    if len(os.getenv("JWT_SECRET_KEY", "")) < 32:
        raise RuntimeError("Production requires a persistent JWT secret of at least 32 characters")
    if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql"):
        raise RuntimeError("Production workflows require PostgreSQL row locking")
    if not app.config["PUBLIC_CLIENT_URL"].startswith("https://"):
        raise RuntimeError("Production requires an HTTPS public client URL")
db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(
    app,
    async_mode="threading",
    cors_allowed_origins=os.getenv("CLIENT_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
)
