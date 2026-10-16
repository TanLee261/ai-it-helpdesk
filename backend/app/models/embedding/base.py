from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingModel(ABC):
    model_name: str
    dimension: int

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
