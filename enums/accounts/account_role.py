from enum import StrEnum


class AccountRole(StrEnum):
    VISITOR = "visitor"
    CLIENT = "client"
    EMPLOYEE = "employee"
    ADMIN = "admin"
