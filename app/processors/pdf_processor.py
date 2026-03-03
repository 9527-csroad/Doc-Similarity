import fitz  # PyMuPDF
from typing import Tuple, List
from pathlib import Path


class PDFProcessor:
    """PDF 文档解析器"""

    def extract_text(self, pdf_path: str) -> Tuple[str, int]:
        """提取 PDF 文本内容"""
        doc = fitz.open(pdf_path)
        text_parts = []

        for page in doc:
            text_parts.append(page.get_text())

        page_count = len(doc)
        doc.close()

        return "\n".join(text_parts), page_count

    def extract_images(self, pdf_path: str) -> List[bytes]:
        """提取 PDF 中的图片"""
        doc = fitz.open(pdf_path)
        images = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                images.append(base_image["image"])

        doc.close()
        return images
