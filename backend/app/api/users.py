from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import AuthSession, User, utc_now
from app.db.session import get_db
from app.schemas.auth import PasswordResetResponse, UserActiveUpdate, UserCreate, UserCreated, UserRead
from app.security.audit import record_event
from app.security.passwords import hash_password, temporary_password
from app.security.rbac import Actor, Role, require_roles
from sqlalchemy import select, update


router = APIRouter(prefix="/users", tags=["user-management"])


@router.get("", response_model=list[UserRead])
def list_users(
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles(Role.TECHNICIAN, Role.ADMIN)),
) -> list[User]:
    query = select(User).order_by(User.created_at.desc()).limit(limit)
    if actor.role == Role.TECHNICIAN:
        query = query.where(User.role == Role.EMPLOYEE.value)
    return list(db.scalars(query))


@router.post("", response_model=UserCreated, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles(Role.TECHNICIAN, Role.ADMIN)),
) -> UserCreated:
    if actor.role == Role.TECHNICIAN and payload.role != Role.EMPLOYEE.value:
        raise HTTPException(status_code=403, detail="Technicians can only create employee accounts")
    if payload.role == Role.TECHNICIAN.value and actor.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only an administrator can create technician accounts")
    identity = payload.username.strip().lower()
    email = payload.email.strip().lower()
    if db.scalar(select(User.id).where((User.username == identity) | (User.email == email))) is not None:
        raise HTTPException(status_code=409, detail="Username or email already exists")
    password = temporary_password()
    user = User(
        username=identity, email=email, full_name=payload.full_name.strip(),
        role=payload.role, password_hash=hash_password(password), is_active=True,
        must_change_password=True, created_by_user_id=actor.user_id,
    )
    db.add(user)
    try:
        db.flush()
        record_event(db, actor, "user.created", "user", identity, {"role": payload.role})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username or email already exists") from exc
    db.refresh(user)
    return UserCreated(**UserRead.model_validate(user).model_dump(), temporary_password=password)


@router.patch("/{user_id}/active", response_model=UserRead)
def set_user_active(
    user_id: int,
    payload: UserActiveUpdate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles(Role.TECHNICIAN, Role.ADMIN)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == actor.user_id:
        raise HTTPException(status_code=409, detail="You cannot deactivate your own account")
    if actor.role == Role.TECHNICIAN and user.role != Role.EMPLOYEE.value:
        raise HTTPException(status_code=403, detail="Technicians can only manage employee accounts")
    user.is_active = payload.is_active
    if payload.is_active:
        user.locked_until = None
        user.failed_login_attempts = 0
    else:
        # Revoke active sessions when disabled
        db.execute(update(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None)).values(revoked_at=utc_now()))
    user.updated_at = utc_now()
    db.flush()
    record_event(db, actor, "user.activated" if user.is_active else "user.deactivated", "user", str(user.id), {"username": user.username})
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/reset-password", response_model=PasswordResetResponse)
def reset_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_roles(Role.TECHNICIAN, Role.ADMIN)),
) -> PasswordResetResponse:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if actor.role == Role.TECHNICIAN and user.role != Role.EMPLOYEE.value:
        raise HTTPException(status_code=403, detail="Technicians can only reset employee passwords")
    if user.id == actor.user_id and actor.role != Role.ADMIN:
        raise HTTPException(status_code=409, detail="You cannot reset your own password via this endpoint")

    password = temporary_password()
    user.password_hash = hash_password(password)
    user.must_change_password = True
    user.failed_login_attempts = 0
    user.locked_until = None
    user.updated_at = utc_now()

    # Invalidate all active sessions for this user so they must sign in again with the new temporary password
    db.execute(update(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None)).values(revoked_at=utc_now()))
    db.flush()
    record_event(db, actor, "user.password_reset", "user", str(user.id), {"username": user.username, "reset_by": actor.actor_id})
    db.commit()
    db.refresh(user)
    return PasswordResetResponse(temporary_password=password, user=UserRead.model_validate(user))

