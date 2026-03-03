import json
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np

from app.config import get_settings
from app.services.vector.base import VectorStore


class FaissStore(VectorStore):
    def __init__(self):
        settings = get_settings()
        self.dim = settings.EMBEDDING_DIM
        self.index_path = Path(settings.FAISS_INDEX_PATH)
        self.meta_path = Path(settings.FAISS_META_PATH)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.doc_ids: List[str] = []
        self.index = faiss.IndexFlatIP(self.dim)
        self._load()

    def _load(self) -> None:
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        if self.meta_path.exists():
            self.doc_ids = json.loads(self.meta_path.read_text(encoding="utf-8"))

    def _persist(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        self.meta_path.write_text(json.dumps(self.doc_ids), encoding="utf-8")

    def _to_vector(self, vector: List[float]) -> np.ndarray:
        arr = np.array(vector, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(arr)
        return arr

    def insert(self, doc_id: str, vector: List[float]) -> None:
        if doc_id in self.doc_ids:
            self.delete(doc_id)
        arr = self._to_vector(vector)
        self.index.add(arr)
        self.doc_ids.append(doc_id)
        self._persist()

    def search(self, vector: List[float], top_k: int = 10) -> List[Tuple[str, float]]:
        if self.index.ntotal == 0:
            return []
        arr = self._to_vector(vector)
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(arr, k)
        results: List[Tuple[str, float]] = []
        for score, idx in zip(scores[0].tolist(), indices[0].tolist()):
            if idx < 0 or idx >= len(self.doc_ids):
                continue
            results.append((self.doc_ids[idx], float(score)))
        return results

    def delete(self, doc_id: str) -> None:
        if doc_id not in self.doc_ids:
            return
        idx = self.doc_ids.index(doc_id)
        self.doc_ids.pop(idx)
        if self.doc_ids:
            new_index = faiss.IndexFlatIP(self.dim)
            vectors = self.index.reconstruct_n(0, self.index.ntotal)
            filtered = np.array([v for i, v in enumerate(vectors) if i != idx], dtype=np.float32)
            if len(filtered) > 0:
                faiss.normalize_L2(filtered)
                new_index.add(filtered)
            self.index = new_index
        else:
            self.index = faiss.IndexFlatIP(self.dim)
        self._persist()
