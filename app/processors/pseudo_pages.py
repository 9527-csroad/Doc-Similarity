from typing import List, Optional, Tuple

TITLE_MAX_CHARS = 200


def split_pseudo_pages(text: str, chars_per_page: int) -> List[str]:
    txt = (text or "").strip()
    if not txt:
        return []
    pages: List[str] = []
    start = 0
    while start < len(txt):
        chunk = txt[start : start + chars_per_page]
        if chunk.strip():
            pages.append(chunk.strip())
        start += chars_per_page
    return pages


def extract_title(text: str) -> str:
    txt = (text or "").strip()
    if not txt:
        return ""
    first_line = txt.split("\n")[0].strip()
    return first_line[:TITLE_MAX_CHARS] if first_line else ""


def build_fingerprint_segments(
    text: str,
    chars_per_page: int = 2000,
    title: Optional[str] = None,
) -> Tuple[str, List[str], int]:
    """Return (title, segments, pseudo_page_count). segments for merged/pooled."""
    txt = (text or "").strip()
    if not txt:
        return "", [], 0

    pages = split_pseudo_pages(txt, chars_per_page)
    count = len(pages)

    if count < 8:
        return txt[:TITLE_MAX_CHARS], [txt], count

    resolved_title = (title or "").strip() or extract_title(txt)
    first3 = pages[:3]
    mid_start = max(0, (count // 2) - 1)
    middle3 = pages[mid_start : mid_start + 3]
    last2 = pages[-2:]

    segments = [resolved_title] + first3 + middle3 + last2
    return resolved_title, [s for s in segments if s], count
