from abc import ABC, abstractmethod
from typing import List


class OCRProvider(ABC):
    @abstractmethod
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        pass

    def batch_extract(self, images: List[bytes]) -> str:
        all_texts = []
        for img in images:
            text = self.extract_text_from_image(img)
            if text:
                all_texts.append(text)
        return "\n".join(all_texts)
