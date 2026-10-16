from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ApprovalStatus = Literal["pending", "approved", "rejected"]


class ApprovalCreate(BaseModel):
    ticket_id: str = Field(min_length=3, max_length=32)
    action: str = Field(min_length=3, max_length=1000)
    rationale: str = Field(min_length=3, max_length=3000)


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    note: str = Field(min_length=3, max_length=1000)


class ApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    approval_id: str
    ticket_id: str
    action: str
    rationale: str
    status: ApprovalStatus
    requested_by: str
    decided_by: str | None
    decision_note: str | None
    created_at: datetime
    decided_at: datetime | None


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    actor_id: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: str
    metadata_json: dict
    created_at: datetime
