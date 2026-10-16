from __future__ import annotations

from functools import cached_property
from typing import Optional

from app.core.config import get_settings
from app.models.reranker.base import RerankerModel


class BgeReranker(RerankerModel):
    def __init__(self, model_name: Optional[str] = None, batch_size: int = 8) -> None:
        self.model_name = model_name or get_settings().reranker_model
        self.batch_size = batch_size

    @cached_property
    def tokenizer(self):
        from transformers import AutoTokenizer

        return AutoTokenizer.from_pretrained(self.model_name)

    @cached_property
    def model(self):
        import torch
        from transformers import AutoModelForSequenceClassification

        model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        model.eval()
        if torch.backends.mps.is_available():
            model.to("mps")
        return model

    def score_pairs(self, query: str, passages: list[str]) -> list[float]:
        import torch

        if not passages:
            return []
        model = self.model
        device = next(model.parameters()).device
        scores: list[float] = []
        for start in range(0, len(passages), self.batch_size):
            batch = passages[start : start + self.batch_size]
            inputs = self.tokenizer(
                [[query, passage] for passage in batch],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            inputs = {key: value.to(device) for key, value in inputs.items()}
            with torch.inference_mode():
                logits = model(**inputs).logits.reshape(-1)
            scores.extend(float(score) for score in logits.cpu().tolist())
        return scores
