from __future__ import annotations

from app.security.rbac import Actor, Role


def can_read_scope(actor: Actor, access_scope: str) -> bool:
    if access_scope == "public":
        return True
    if actor.role == Role.ADMIN:
        return True
    if access_scope == "it_internal":
        return actor.role == Role.TECHNICIAN
    return False
