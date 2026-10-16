from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.retrieval.query.understanding import QueryUnderstanding


Route = Literal["retrieve", "skip"]


@dataclass(frozen=True)
class QueryRoute:
    route: Route
    reason: str


def route_query(understanding: QueryUnderstanding) -> QueryRoute:
    if understanding.intent == "chitchat":
        return QueryRoute(route="skip", reason="No incident evidence requested")
    return QueryRoute(route="retrieve", reason="Evidence retrieval required")
