from __future__ import annotations

from abc import ABC, abstractmethod


class RerankerModel(ABC):
    @abstractmethod
    def score_pairs(self, query: str, passages: list[str]) -> list[float]:
        raise NotImplementedError
