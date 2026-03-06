import re
from typing import Dict, List, Tuple

import fitz  # PyMuPDF


class PDFProcessor:
    """PDF 文档解析器"""

    def extract_text(self, pdf_path: str) -> Tuple[str, int, List[bytes]]:
        """提取 PDF 文本内容，并返回扫描页图片"""
        doc = fitz.open(pdf_path)
        text_parts: List[str] = []
        scan_page_images: List[bytes] = []

        for page in doc:
            page_text = page.get_text() or ""
            if self._effective_char_count(page_text) < 50:
                pix = page.get_pixmap(alpha=False)
                scan_page_images.append(pix.tobytes("png"))
            text_parts.append(page_text)

        page_count = len(doc)
        doc.close()
        return "\n".join(text_parts), page_count, scan_page_images

    def extract_images(self, pdf_path: str) -> List[bytes]:
        """提取 PDF 中的图片，过滤小图"""
        doc = fitz.open(pdf_path)
        images = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)
                if width < 100 and height < 100:
                    continue
                images.append(base_image["image"])

        doc.close()
        return images

    def extract_metadata(self, pdf_path: str) -> Dict[str, str]:
        doc = fitz.open(pdf_path)
        max_pages = min(5, len(doc))
        head_text = []
        for idx in range(max_pages):
            head_text.append(doc[idx].get_text() or "")
        doc.close()

        raw = "\n".join(head_text)
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        title = lines[0] if lines else ""
        author = self._extract_by_patterns(
            raw,
            [r"(?:作者|Author)[:：]\s*([^\n]{1,80})", r"([^\n]{2,40})\s*(?:著|编著)"],
        )
        publisher = self._extract_by_patterns(
            raw,
            [r"(?:出版社|Publisher)[:：]?\s*([^\n]{2,80})"],
        )
        isbn = self._extract_by_patterns(
            raw,
            [r"ISBN(?:-13|-10)?[:：\s]*([0-9Xx\-]{10,20})"],
        )
        edition = self._extract_by_patterns(
            raw,
            [r"(第[一二三四五六七八九十0-9]+版)"],
        )
        metadata = {
            "title": title,
            "author": author,
            "publisher": publisher,
            "isbn": self._normalize_isbn(isbn),
            "edition": edition,
        }
        return {k: v for k, v in metadata.items() if v}

    def _extract_by_patterns(self, text: str, patterns: List[str]) -> str:
        for pattern in patterns:
            matched = re.search(pattern, text, flags=re.IGNORECASE)
            if matched:
                return matched.group(1).strip()
        return ""

    def _normalize_isbn(self, isbn: str) -> str:
        return re.sub(r"[^0-9Xx\-]", "", isbn or "")

    def _effective_char_count(self, text: str) -> int:
        return len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", text or ""))
