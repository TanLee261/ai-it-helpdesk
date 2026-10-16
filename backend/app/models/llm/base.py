from __future__ import annotations

from typing import Protocol

from app.analysis.schema import RcaDraft


class RcaGenerator(Protocol):
    model: str

    def generate(self, system_prompt: str, user_prompt: str) -> RcaDraft: ...
