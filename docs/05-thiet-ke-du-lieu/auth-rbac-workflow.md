# Authentication and RBAC Workflow

## Roles & Responsibilities

| Role | Permissions & Responsibilities |
| --- | --- |
| **Admin** | Create technician and employee accounts; manage/lock/unlock accounts; reset passwords; access all tickets, RCA, knowledge base, approval reviews, and security audit logs. Cannot allow technicians to grant admin roles. |
| **Technician** | View ticket queue; assign/claim tickets; update statuses (`new`, `assigned`, `in_progress`, `waiting_for_employee`, `resolved`, `closed`); run hybrid retrieval & AI RCA analysis; view evidence citations; add technical notes / request info from employee; review and publish official employee response; create employee accounts; reset employee passwords; lock/unlock employee accounts. |
| **Employee** | Sign in with temporary password and enforced initial password change; create incident tickets; view and add supplementary information / comments to their own tickets only; receive technician's reviewed response; confirm resolution & close ticket. |

The initial administrator is created out-of-band via `scripts/create_admin.py`. The script prompts for credentials and refuses to bootstrap another admin once an admin exists. Technicians and employees created within the application receive a random one-time temporary password and must change it on first sign-in before accessing any application features.

## Account Security & Lifecycle

1. **One-Time Temporary Passwords**: Generated randomly using secure cryptography (`secrets.token_urlsafe`), never stored in plaintext (hashed with bcrypt/pbkdf2), and marked with `must_change_password = True`.
2. **Forced First-Login Password Change**: Until the password is changed via `POST /api/auth/change-password`, all other API endpoints return `403 Forbidden`.
3. **Account Lockout on Failed Logins**: 5 consecutive failed login attempts automatically trigger a 15-minute account lockout, logged as `auth.account_locked` in the audit event log.
4. **Password Reset Workflow**: Administrators (for technicians and employees) and Technicians (for employees only) can trigger a password reset (`POST /api/users/{user_id}/reset-password`), which invalidates all active sessions, clears lockouts, generates a new temporary password, and logs a `user.password_reset` audit event.
5. **Account Deactivation / Lock**: Accounts can be locked/unlocked via `PATCH /api/users/{user_id}/active`. Deactivation immediately revokes active sessions.

## Incident Processing Workflow

```
[Employee creates ticket] (status: new)
       │
       ▼
[Technician claims ticket] (status: assigned)
       │
       ▼
[Technician runs hybrid retrieval & AI RCA analysis] (status: in_progress)
       │
       ├─► Evidence missing / contradictory?
       │   Set status: waiting_for_employee ──► [Technician adds question in discussion]
       │                                                 │
       │                                                 ▼
       │   [Employee provides supplementary info] ◄──────┘
       │   (Status automatically returns to in_progress)
       │
       ▼
[Technician verifies evidence & writes official response]
       │
       ▼
[Technician publishes response] (PATCH /api/tickets/{id}/response, status: resolved)
       │
       ▼
[Employee reviews response & confirms resolution]
       │
       ▼
[Employee confirms resolution & closes ticket] (status: closed)
```

## Ticket Privacy & Internal RCA Isolation

- `POST /api/ai/analyze` returns an advisory RCA draft only to authenticated technician/admin sessions. It is never directly exposed to employees.
- Technicians review the AI findings, citations, and runbooks, then draft and publish an official human-verified response via `PATCH /api/tickets/{ticket_id}/response`.
- Employees can only query tickets where `created_by_user_id == user.id`. Internal root cause fields, internal team assignments, and raw resolution logs are stripped from employee API responses.
- Historical seeded tickets remain ownerless and visible only to IT technicians/admins.

## Local Setup

Upgrade the database schema and initialize the bootstrap admin:

```bash
cd backend
alembic upgrade head
python ../scripts/create_admin.py
```

