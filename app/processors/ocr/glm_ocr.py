import base64

import httpx

from app.config import get_settings
from app.processors.ocr.base import OCRProvider


class GLMOCRProvider(OCRProvider):
    def __init__(self):
        self.settings = get_settings()
        if not self.settings.GLM_API_KEY:
            raise ValueError("GLM_API_KEY is required when OCR_PROVIDER=glm")
        self.endpoint = self.settings.GLM_OCR_ENDPOINT
        self.model = self.settings.GLM_OCR_MODEL

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "model": self.model,
            "file": f"data:image/png;base64,{encoded}",
        }
        headers = {
            "Authorization": self.settings.GLM_API_KEY,
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return self._parse_text(data)

    def _parse_text(self, data: dict) -> str:
        if not isinstance(data, dict):
            return ""
        parts = []
        text = data.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
        result = data.get("result")
        if isinstance(result, dict):
            markdown = result.get("markdown")
            if isinstance(markdown, str) and markdown.strip():
                parts.append(markdown.strip())
            blocks = result.get("blocks")
            if isinstance(blocks, list):
                for block in blocks:
                    if isinstance(block, dict):
                        block_text = block.get("text")
                        if isinstance(block_text, str) and block_text.strip():
                            parts.append(block_text.strip())
        layout_details = data.get("layout_details")
        if isinstance(layout_details, list):
            for page_blocks in layout_details:
                if not isinstance(page_blocks, list):
                    continue
                for block in page_blocks:
                    if not isinstance(block, dict):
                        continue
                    if block.get("label") == "image":
                        continue
                    content = block.get("content")
                    if isinstance(content, str) and content.strip():
                        parts.append(content.strip())
        return "\n".join(p for p in parts if p).strip()
