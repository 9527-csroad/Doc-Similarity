import re
import unicodedata
from collections import Counter
from typing import Dict, List, Tuple


class TextCleaner:
    def __init__(self, min_valid_chars: int = 200):
        self.min_valid_chars = min_valid_chars

    def clean(self, text: str) -> Tuple[str, Dict[str, int]]:
        normalized = self._normalize_text(text)
        lines = normalized.splitlines()
        duplicate_lines = self._detect_repeated_short_lines(lines)

        cleaned_lines: List[str] = []
        removed_duplicate = 0
        removed_noise = 0
        for raw in lines:
            line = raw.strip()
            if not line:
                cleaned_lines.append("")
                continue
            if line in duplicate_lines:
                removed_duplicate += 1
                continue
            if self._is_noise_line(line):
                removed_noise += 1
                continue
            cleaned_lines.append(line)

        cleaned_text = self._collapse_blank_lines("\n".join(cleaned_lines)).strip()
        valid_chars = self._effective_char_count(cleaned_text)
        stats = {
            "original_chars": len(text or ""),
            "cleaned_chars": len(cleaned_text),
            "valid_chars": valid_chars,
            "removed_duplicate_lines": removed_duplicate,
            "removed_noise_lines": removed_noise,
        }
        return cleaned_text, stats

    def is_low_quality(self, cleaned_text: str) -> bool:
        return self._effective_char_count(cleaned_text) < self.min_valid_chars

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text or "")
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
        normalized = normalized.replace("\x00", "")
        return normalized

    def _collapse_blank_lines(self, text: str) -> str:
        return re.sub(r"\n\s*\n+", "\n\n", text)

    def _detect_repeated_short_lines(self, lines: List[str]) -> set[str]:
        trimmed = [line.strip() for line in lines if line and line.strip()]
        short_lines = [line for line in trimmed if len(line) <= 60]
        counts = Counter(short_lines)
        return {line for line, c in counts.items() if c >= 3}

    def _is_noise_line(self, line: str) -> bool:
        if len(line) <= 1:
            return True
        if len(line) <= 20:
            total = len(line)
            junk = 0
            for ch in line:
                if not (self._is_chinese(ch) or ch.isalpha() or ch.isdigit()):
                    junk += 1
            if total > 0 and (junk / total) > 0.5:
                return True
        return False

    def _effective_char_count(self, text: str) -> int:
        return len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", text or ""))

    def _is_chinese(self, ch: str) -> bool:
        return "\u4e00" <= ch <= "\u9fff"
