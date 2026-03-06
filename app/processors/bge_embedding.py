from typing import List
from app.processors.embedding_processor import EmbeddingProvider


class BGEEmbedding(EmbeddingProvider):
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        import os
        from FlagEmbedding import BGEM3FlagModel
        if os.path.exists(model_name):
            model_name = os.path.abspath(model_name)
        self.model = BGEM3FlagModel(model_name, use_fp16=True)
        self._dimension = 1024

    def prepare_document_text(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return ""
        max_chars = 24000
        if len(text) <= max_chars:
            return text

        head_chars = 8000
        sample_chars = 2500
        sample_count = 6

        head = text[:head_chars]
        body = text[head_chars:]
        body_len = len(body)
        if body_len <= sample_chars:
            return (head + "\n\n" + body)[:max_chars]

        segments: List[str] = [head]
        step = max(1, body_len // sample_count)
        for idx in range(sample_count):
            start = min(idx * step, max(0, body_len - sample_chars))
            end = start + sample_chars
            segments.append(body[start:end])
        merged = "\n\n".join(seg.strip() for seg in segments if seg.strip())
        return merged[:max_chars]

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            max_length=8192
        )['dense_vecs']
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self._dimension
