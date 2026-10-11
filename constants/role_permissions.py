from enums.accounts.account_role import AccountRole
from enums.accounts.permission import Permission

MEMBER_PERMISSIONS = frozenset({
    Permission.PROFILE_READ_OWN, Permission.PROFILE_EDIT_OWN,
    Permission.ACTIVITY_READ_OWN, Permission.PURCHASE_READ_OWN,
    Permission.PURCHASE_WRITE_ONE, Permission.LOAN_READ_OWN,
    Permission.LOAN_WRITE_ONE, Permission.RECEIPT_READ_OWN,
    Permission.REVIEW_READ_OWN, Permission.REVIEW_WRITE_ONE,
    Permission.REVIEW_EDIT_OWN, Permission.REVIEW_DELETE_OWN,
    Permission.PROFILE_MEDIA_WRITE_OWN, Permission.ADMIN_REQUEST_WRITE_ONE,
})

ROLE_PERMISSIONS: dict[AccountRole, frozenset[Permission]] = {
    AccountRole.VISITOR: frozenset(),
    AccountRole.CLIENT: MEMBER_PERMISSIONS,
    AccountRole.EMPLOYEE: MEMBER_PERMISSIONS,
    AccountRole.ADMIN: frozenset(Permission),
}


def permissions_for(role: AccountRole | str) -> frozenset[Permission]:
    try:
        return ROLE_PERMISSIONS[AccountRole(role)]
    except (ValueError, KeyError):
        return frozenset()
