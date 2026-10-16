from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from fastapi import Depends, HTTPException, status

from app.db.models import User
from app.security.auth import get_current_user


class Role(str, Enum):
    TECHNICIAN = "technician"
    EMPLOYEE = "employee"
    ADMIN = "admin"


@dataclass(frozen=True)
class Actor:
    actor_id: str
    role: Role
    user_id: int = 0


def get_actor(user: User = Depends(get_current_user)) -> Actor:
    try:
        role = Role(user.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown account role") from exc
    return Actor(actor_id=user.username[:120], role=role, user_id=user.id)


def require_roles(*roles: Role):
    def dependency(actor: Actor = Depends(get_actor)) -> Actor:
        if actor.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return actor

    return dependency
