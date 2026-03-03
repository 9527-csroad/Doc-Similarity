from typing import List

from app.processors.ocr import get_ocr_provider


class OCRProcessor:
    def __init__(self):
        self.provider = get_ocr_provider()

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        if self.provider is None:
            return ""
        return self.provider.extract_text_from_image(image_bytes)

    def batch_extract(self, images: List[bytes]) -> str:
        if self.provider is None:
            return ""
        return self.provider.batch_extract(images)
