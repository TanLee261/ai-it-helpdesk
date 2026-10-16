from __future__ import annotations

from functools import cached_property
from typing import Optional

from app.core.config import get_settings
from app.models.embedding.base import EmbeddingModel


class BgeM3EmbeddingModel(EmbeddingModel):
    def __init__(self, model_name: Optional[str] = None, dimension: Optional[int] = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.dimension = dimension or settings.embedding_dimension

    @cached_property
    def tokenizer(self):
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "transformers is required for BGE-M3 embeddings. "
                "Install backend dependencies with: python3 -m pip install -e 'backend[dev]'"
            ) from exc
        return AutoTokenizer.from_pretrained(self.model_name)

    @cached_property
    def model(self):
        try:
            import torch
            from transformers import AutoModel
        except ImportError as exc:
            raise RuntimeError(
                "torch and transformers are required for BGE-M3 embeddings. "
                "Install backend dependencies with: python3 -m pip install -e 'backend[dev]'"
            ) from exc
        model = AutoModel.from_pretrained(self.model_name)
        model.eval()
        if torch.backends.mps.is_available():
            model.to("mps")
        return model

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        import torch
        import torch.nn.functional as functional

        device = next(self.model.parameters()).device
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        inputs = {key: value.to(device) for key, value in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
            token_embeddings = outputs.last_hidden_state
            attention_mask = inputs["attention_mask"].unsqueeze(-1)
            masked_embeddings = token_embeddings * attention_mask
            summed = masked_embeddings.sum(dim=1)
            counts = attention_mask.sum(dim=1).clamp(min=1)
            embeddings = summed / counts
            embeddings = functional.normalize(embeddings, p=2, dim=1)
        vectors = embeddings.cpu().tolist()
        if vectors and len(vectors[0]) != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.dimension}, got {len(vectors[0])}"
            )
        return vectors
