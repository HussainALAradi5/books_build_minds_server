"""Values shared by the account and review workflows."""
from enum import Enum


class AccountRole(str, Enum):
    READER = "reader"
    ADMIN = "admin"


class AdminDecision(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class MediaType(str, Enum):
    BOOK_COVER = "book_cover"
    BOOK_GALLERY = "book_gallery"
    PROFILE_PICTURE = "profile_picture"


class LoanStatus(str, Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"
