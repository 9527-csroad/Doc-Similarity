from typing import List, Optional

import numpy as np

from app.processors.pseudo_pages import build_fingerprint_segments


def compute_merged_vector(
    text: str,
    embed_fn,
    chars_per_page: int = 2000,
    title: Optional[str] = None,
    prepare_fn=None,
) -> List[float]:
    _, segments, _ = build_fingerprint_segments(text, chars_per_page, title)
    if not segments:
        return []
    merged = "\n\n".join(segments)
    if prepare_fn and callable(prepare_fn):
        merged = prepare_fn(merged)
    vecs = embed_fn([merged])
    return vecs[0] if vecs else []


def compute_pooled_vector(
    text: str,
    embed_fn,
    chars_per_page: int = 2000,
    title: Optional[str] = None,
    title_weight: float = 1.5,
) -> List[float]:
    resolved_title, segments, _ = build_fingerprint_segments(text, chars_per_page, title)
    if not segments:
        return []
    vecs = embed_fn(segments)
    if not vecs:
        return []
    arr = np.array(vecs, dtype=np.float32)
    weights = np.ones(len(vecs), dtype=np.float32)
    if segments and segments[0] == resolved_title and len(weights) > 0:
        weights[0] = title_weight
    arr = arr * weights[:, np.newaxis]
    mean_vec = np.mean(arr, axis=0).astype(np.float32)
    norm = np.linalg.norm(mean_vec)
    if norm > 1e-9:
        mean_vec = mean_vec / norm
    return mean_vec.tolist()
