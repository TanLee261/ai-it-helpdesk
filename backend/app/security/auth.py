from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AuthSession, User, utc_now
from app.db.session import get_db


SESSION_COOKIE = "helpdesk_session"
SESSION_HOURS = 12


def issue_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(user_id=user.id, token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=utc_now() + timedelta(hours=SESSION_HOURS)))
    db.commit()
    return token


def get_session_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash))
    expires_at = session.expires_at.replace(tzinfo=timezone.utc) if session is not None and session.expires_at.tzinfo is None else (session.expires_at if session is not None else None)
    if session is None or session.revoked_at is not None or expires_at <= utc_now():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired; log in again")
    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive")
    return user


def revoke_session(request: Request, db: Session, user: User) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        session = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash, AuthSession.user_id == user.id))
        if session is not None:
            session.revoked_at = utc_now()
            db.commit()


def get_current_user(user: User = Depends(get_session_user)) -> User:
    if user.must_change_password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Change your temporary password before continuing")
    return user


def set_session_cookie(response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE, token, max_age=SESSION_HOURS * 3600, httponly=True,
        secure=get_settings().env.lower() in {"prod", "production"}, samesite="strict", path="/",
    )
