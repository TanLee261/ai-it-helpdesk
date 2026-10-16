from __future__ import annotations

from datetime import timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import User, utc_now
from app.db.session import get_db
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, UserRead
from app.security.audit import record_event
from app.security.auth import SESSION_COOKIE, get_session_user, issue_session, revoke_session, set_session_cookie
from app.security.passwords import hash_password, validate_new_password, verify_password
from app.security.rbac import Actor, Role


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> LoginResponse:
    identity = payload.username.strip().lower()
    user = db.scalar(select(User).where(or_(User.username == identity, User.email == identity)))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled. Please contact an administrator.")

    now = utc_now()
    locked_until = user.locked_until.replace(tzinfo=timezone.utc) if user.locked_until and user.locked_until.tzinfo is None else user.locked_until
    if locked_until and locked_until > now:
        remaining_seconds = int((locked_until - now).total_seconds())
        remaining_minutes = max(1, (remaining_seconds + 59) // 60)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is temporarily locked due to too many failed login attempts. Try again in {remaining_minutes} minutes.",
        )

    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = now + timedelta(minutes=15)
            record_event(
                db,
                Actor(user_id=user.id, actor_id=user.username, role=Role(user.role)),
                "auth.account_locked",
                "user",
                str(user.id),
                {"reason": "too_many_failed_attempts", "attempts": user.failed_login_attempts},
            )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    token = issue_session(db, user)
    set_session_cookie(response, token)
    return LoginResponse(user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_session_user)) -> User:
    return user


@router.post("/change-password", response_model=UserRead)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_session_user),
) -> User:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    try:
        validate_new_password(payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(status_code=422, detail="Choose a password different from the temporary password")
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    user.updated_at = utc_now()
    db.commit()
    db.refresh(user)
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db), user: User = Depends(get_session_user)) -> Response:
    revoke_session(request, db, user)
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="strict")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
