"""Formatting and sanitization helpers for grammar feature."""

from __future__ import annotations

import html
from html.parser import HTMLParser
import unicodedata

from features.grammar.texts import normalize_language


CALLBACK_POPUP_MAX_LEN = 180
_ALLOWED_DYNAMIC_HTML_TAGS = {
    "b",
    "strong",
    "i",
    "em",
    "u",
    "ins",
    "s",
    "strike",
    "del",
    "code",
    "pre",
    "a",
}


class _TelegramDynamicHtmlSanitizer(HTMLParser):
    """Sanitize dynamic content for Telegram HTML parse mode."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._parts: list[str] = []
        self._open_tags: list[str] = []

    def _append_escaped(self, raw_value: str) -> None:
        self._parts.append(html.escape(raw_value, quote=False))

    def _append_start_tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href_value: str | None = None
            for key, value in attrs:
                if key.lower() == "href" and value:
                    href_value = value
                    break
            if href_value:
                escaped_href = html.escape(href_value, quote=True)
                self._parts.append(f'<a href="{escaped_href}">')
                self._open_tags.append("a")
                return
            self._append_escaped(self.get_starttag_text() or "<a>")
            return

        self._parts.append(f"<{tag}>")
        self._open_tags.append(tag)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if normalized == "br":
            self._parts.append("\n")
            return
        if normalized == "p":
            if self._parts and not self._parts[-1].endswith("\n\n"):
                self._parts.append("\n\n")
            return
        if normalized not in _ALLOWED_DYNAMIC_HTML_TAGS:
            self._append_escaped(self.get_starttag_text() or f"<{tag}>")
            return
        self._append_start_tag(normalized, attrs)

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized in {"br", "p"}:
            if self._parts and not self._parts[-1].endswith("\n"):
                self._parts.append("\n")
            return
        if normalized not in _ALLOWED_DYNAMIC_HTML_TAGS:
            self._append_escaped(f"</{tag}>")
            return
        if normalized not in self._open_tags:
            self._append_escaped(f"</{tag}>")
            return

        while self._open_tags:
            opened = self._open_tags.pop()
            self._parts.append(f"</{opened}>")
            if opened == normalized:
                break

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        if normalized in {"br", "p"}:
            self._parts.append("\n")
            return
        self._append_escaped(self.get_starttag_text() or f"<{tag}/>")

    def handle_data(self, data: str) -> None:
        self._parts.append(html.escape(data, quote=False))

    def handle_entityref(self, name: str) -> None:
        self._parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._parts.append(f"&#{name};")

    def get_sanitized_html(self) -> str:
        while self._open_tags:
            self._parts.append(f"</{self._open_tags.pop()}>")
        return "".join(self._parts)


def _localized_value(
    language: str,
    *,
    ru_value: str | None,
    en_value: str | None,
    default_value: str,
) -> str:
    lang = normalize_language(language)
    ru = (ru_value or "").strip()
    en = (en_value or "").strip()
    if lang == "ru":
        return ru or en or default_value
    return en or ru or default_value


def _is_leading_icon_char(char: str) -> bool:
    code_point = ord(char)
    if char in {"\u200d", "\ufe0f", "\u20e3"}:
        return True
    if 0x1F1E6 <= code_point <= 0x1F1FF:  # regional indicator symbols (flags)
        return True
    if 0x2600 <= code_point <= 0x27BF:  # misc symbols/dingbats
        return True
    if 0x1F300 <= code_point <= 0x1FAFF:  # emoji blocks
        return True
    return unicodedata.category(char) in {"So", "Sk"}


def _strip_leading_icon(title: str) -> str:
    text = title.lstrip()
    if not text:
        return title

    index = 0
    while index < len(text) and _is_leading_icon_char(text[index]):
        index += 1

    if index == 0:
        return text

    while index < len(text) and text[index].isspace():
        index += 1

    stripped = text[index:]
    return stripped or text


def _strip_leading_details_prefix(value: str) -> str:
    stripped = value.lstrip()
    if not stripped:
        return value

    prefixes = (
        "Подробное описание:",
        "Подробное объяснение:",
        "Detailed explanation:",
    )
    lowered = stripped.casefold()
    for prefix in prefixes:
        if lowered.startswith(prefix.casefold()):
            cleaned = stripped[len(prefix) :].lstrip()
            return cleaned or stripped
    return stripped


def _sanitize_dynamic_html(value: str) -> str:
    sanitizer = _TelegramDynamicHtmlSanitizer()
    sanitizer.feed(value)
    sanitizer.close()
    return sanitizer.get_sanitized_html()


def _truncate_popup_text(text: str) -> str:
    cleaned = text.strip()
    if len(cleaned) <= CALLBACK_POPUP_MAX_LEN:
        return cleaned
    return f"{cleaned[:CALLBACK_POPUP_MAX_LEN - 1].rstrip()}…"
