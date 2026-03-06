import argparse
import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

import fitz

from app.processors import OCRProcessor, TextCleaner


def valid_chars_count(text: str) -> int:
    count = 0
    for ch in text or "":
        if ch.isalnum() or ("\u4e00" <= ch <= "\u9fff"):
            count += 1
    return count


def page_to_png(pdf_path: Path, page_no: int) -> bytes:
    doc = fitz.open(str(pdf_path))
    try:
        page = doc[page_no]
        pix = page.get_pixmap(alpha=False)
        return pix.tobytes("png")
    finally:
        doc.close()


def ocr_one_page(ocr: OCRProcessor, pdf_path: Path, page_no: int) -> Tuple[int, str, str]:
    try:
        image_bytes = page_to_png(pdf_path, page_no)
        text = ocr.extract_text_from_image(image_bytes) or ""
        return page_no, text, ""
    except Exception as e:
        return page_no, "", str(e)


def collect_repeated_short_lines(
    page_texts: List[str], max_len: int = 60, min_repeat: int = 30
) -> set[str]:
    lines = []
    for text in page_texts:
        for line in (text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            if len(line) <= max_len:
                lines.append(line)
    counter = Counter(lines)
    return {line for line, cnt in counter.items() if cnt >= min_repeat}


def drop_repeated_lines(text: str, repeated_lines: set[str]) -> Tuple[str, int]:
    if not repeated_lines:
        return (text or "").strip(), 0
    kept = []
    removed = 0
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped and stripped in repeated_lines:
            removed += 1
            continue
        if stripped:
            kept.append(stripped)
    return "\n".join(kept).strip(), removed


def extract_book(
    pdf_path: Path,
    output_dir: Path,
    max_workers: int,
    page_text_min_chars: int,
    book_min_valid_chars: int,
    force: bool,
) -> Dict:
    txt_path = output_dir / f"{pdf_path.stem}.txt"
    meta_path = output_dir / f"{pdf_path.stem}.meta.json"
    if txt_path.exists() and meta_path.exists() and not force:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("status") == "done":
                return meta
        except Exception:
            pass

    started = time.time()
    page_info: List[Dict] = []
    raw_chars = 0
    text_pages = 0
    ocr_targets: List[int] = []
    final_page_text: Dict[int, str] = {}

    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    page_raw_texts: List[str] = []
    for page_no in range(total_pages):
        page_text = (doc[page_no].get_text() or "").strip()
        page_raw_texts.append(page_text)
        raw_chars += len(page_text)
    doc.close()

    repeated_lines = collect_repeated_short_lines(page_raw_texts)
    for page_no, raw_text in enumerate(page_raw_texts):
        raw_valid = valid_chars_count(raw_text)
        effective_text, removed_repeated_lines = drop_repeated_lines(raw_text, repeated_lines)
        effective_valid = valid_chars_count(effective_text)
        need_ocr = effective_valid < page_text_min_chars
        if need_ocr:
            ocr_targets.append(page_no)
        else:
            final_page_text[page_no] = effective_text
            text_pages += 1
        page_info.append(
            {
                "page_no": page_no + 1,
                "raw_chars": len(raw_text),
                "raw_valid_chars": raw_valid,
                "effective_valid_chars": effective_valid,
                "removed_repeated_lines": removed_repeated_lines,
                "need_ocr": need_ocr,
                "source": "text" if not need_ocr else "pending_ocr",
            }
        )

    failed_ocr_pages: List[int] = []
    ocr_pages = 0
    if ocr_targets:
        ocr = OCRProcessor()
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(ocr_one_page, ocr, pdf_path, page_no) for page_no in ocr_targets]
            for future in as_completed(futures):
                page_no, text, err = future.result()
                idx = page_no
                if err:
                    failed_ocr_pages.append(page_no + 1)
                    page_info[idx]["source"] = "empty"
                    final_page_text[page_no] = ""
                    continue
                ocr_text = (text or "").strip()
                final_page_text[page_no] = ocr_text
                if ocr_text:
                    ocr_pages += 1
                    page_info[idx]["source"] = "ocr"
                else:
                    page_info[idx]["source"] = "empty"

    ordered_text = [final_page_text.get(i, "").strip() for i in range(total_pages)]
    merged = "\n\n".join(t for t in ordered_text if t)
    cleaner = TextCleaner(min_valid_chars=book_min_valid_chars)
    cleaned_text, clean_stats = cleaner.clean(merged)
    cleaned_chars = len(cleaned_text)
    valid_chars = clean_stats.get("valid_chars", valid_chars_count(cleaned_text))
    status = "done" if valid_chars >= book_min_valid_chars else "low_quality"

    txt_path.write_text(cleaned_text, encoding="utf-8")
    empty_pages = total_pages - text_pages - ocr_pages
    meta = {
        "file_name": pdf_path.name,
        "total_pages": total_pages,
        "text_pages": text_pages,
        "ocr_pages": ocr_pages,
        "empty_pages": max(0, empty_pages),
        "raw_chars": raw_chars,
        "cleaned_chars": cleaned_chars,
        "valid_chars": valid_chars,
        "status": status,
        "page_text_min_chars": page_text_min_chars,
        "book_min_valid_chars": book_min_valid_chars,
        "repeated_short_lines_count": len(repeated_lines),
        "failed_ocr_pages": failed_ocr_pages,
        "elapsed_sec": round(time.time() - started, 3),
        "clean_stats": clean_stats,
        "pages": page_info,
        "output_text_path": str(txt_path),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-dir",
        default="data/test_dataset2/相似度测试集",
        help="PDF目录",
    )
    parser.add_argument(
        "--output-dir",
        default="data/test_dataset2/texts",
        help="文本输出目录",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="OCR并发数",
    )
    parser.add_argument(
        "--page-text-min-chars",
        type=int,
        default=20,
        help="页文本阈值",
    )
    parser.add_argument(
        "--book-min-valid-chars",
        type=int,
        default=200,
        help="书级有效字符阈值",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖",
    )
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted([p for p in dataset_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"])
    results = []
    for pdf_path in pdf_files:
        meta = extract_book(
            pdf_path=pdf_path,
            output_dir=output_dir,
            max_workers=args.max_workers,
            page_text_min_chars=args.page_text_min_chars,
            book_min_valid_chars=args.book_min_valid_chars,
            force=args.force,
        )
        results.append(meta)

    index_path = output_dir / "index.json"
    index_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
