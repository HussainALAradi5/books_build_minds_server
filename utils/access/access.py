"""Composable authorization expressions evaluated only on the server."""
from dataclasses import dataclass

from constants.role_permissions import permissions_for
from enums.accounts.account_role import AccountRole
from enums.accounts.permission import Permission
from models.access.AccessRole import AccessRole
from config import db


@dataclass(frozen=True)
class AllOf:
    rules: tuple["AccessRule", ...]


@dataclass(frozen=True)
class AnyOf:
    rules: tuple["AccessRule", ...]


@dataclass(frozen=True)
class Owns:
    user_id: int


@dataclass(frozen=True)
class Purchased:
    book_id: int


@dataclass(frozen=True)
class HasRole:
    role: AccountRole


AccessRule = Permission | AllOf | AnyOf | Owns | Purchased | HasRole


def permissions_for_user(user) -> frozenset[str]:
    base = db.session.get(AccessRole, user.role.value)
    if base and not base.is_deleted and not base.is_archived:
        granted = {item.key for item in base.permissions if not item.is_deleted and not item.is_archived}
    else:
        granted = {item.value for item in permissions_for(user.role)}
    if user.role == AccountRole.ADMIN:
        granted.update(item.value for item in Permission)
    roles = list(user.access_roles)
    for group in user.access_groups:
        if not group.is_deleted and not group.is_archived:
            roles.extend(group.roles)
    for role in roles:
        if not role.is_deleted and not role.is_archived:
            granted.update(item.key for item in role.permissions if not item.is_deleted and not item.is_archived)
    return frozenset(granted)


def all_of(*rules: AccessRule) -> AllOf:
    return AllOf(rules)


def any_of(*rules: AccessRule) -> AnyOf:
    return AnyOf(rules)


def owns(user_id: int) -> Owns:
    return Owns(user_id)


def purchased(book_id: int) -> Purchased:
    return Purchased(book_id)


def has_role(role: AccountRole) -> HasRole:
    return HasRole(role)


def has_access(user, rule: AccessRule) -> bool:
    if isinstance(rule, Permission):
        return rule.value in permissions_for_user(user)
    if isinstance(rule, AllOf):
        return bool(rule.rules) and all(has_access(user, item) for item in rule.rules)
    if isinstance(rule, AnyOf):
        return any(has_access(user, item) for item in rule.rules)
    if isinstance(rule, Owns):
        return user.user_id == rule.user_id
    if isinstance(rule, Purchased):
        return any(book.book_id == rule.book_id for book in user.purchased_books)
    if isinstance(rule, HasRole):
        return user.role == rule.role
    return False
