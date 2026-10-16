from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


TicketStatus = Literal["new", "assigned", "in_progress", "waiting_for_employee", "resolved", "closed"]
TicketCategory = Literal["network", "server_api", "database", "account", "other"]
TicketPriority = Literal["p1", "p2", "p3", "p4"]
ImpactUrgency = Literal["low", "medium", "high"]


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=3)
    service: str = Field(min_length=2, max_length=80)
    category: TicketCategory
    priority: TicketPriority
    impact: ImpactUrgency
    urgency: ImpactUrgency
    assigned_team: Optional[str] = Field(default=None, max_length=120)
    raw_category: Optional[str] = Field(default=None, max_length=80)
    sub_category: Optional[str] = Field(default=None, max_length=120)


class TicketUpdateStatus(BaseModel):
    status: TicketStatus


class TechnicianResponseUpdate(BaseModel):
    response: str = Field(min_length=10, max_length=5000)


class TicketCommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    comment_type: Optional[str] = Field(default="comment", max_length=32)


class TicketCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: str
    user_id: int
    user_name: str
    user_role: str
    comment_type: str
    content: str
    created_at: datetime


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: str
    source_ticket_id: Optional[str]
    title: str
    description: str
    service: str
    category: str
    raw_category: Optional[str]
    sub_category: Optional[str]
    priority: str
    impact: str
    urgency: str
    assigned_team: Optional[str]
    auto_resolve: bool
    status: str
    requester_email_redacted: Optional[str]
    verified_root_cause: Optional[str]
    resolution: Optional[str]
    technician_response: Optional[str] = None
    response_sent_at: Optional[datetime] = None
    created_by_user_id: Optional[int] = None
    source: Optional[str]
    created_at: datetime
    updated_at: datetime


class TicketListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TicketRead]
