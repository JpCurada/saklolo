"""Clean the raw text and keep phone numbers out of model prompts."""

import re
import unicodedata

from saklolo.agents.state import PipelineState

# PH mobile numbers as people type them: 09170000000, 0917 123 4567,
# 0917-123-4567, +63 917 123 4567, 639170000000.
PHONE = re.compile(r"(?<!\d)(?:\+?63|0)[\s-]?9\d{2}[\s-]?\d{3}[\s-]?\d{4}(?!\d)")
PHONE_MASK = "[phone]"


def clean(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def mask_phones(text: str) -> str:
    return PHONE.sub(PHONE_MASK, text)


def normalize(state: PipelineState) -> None:
    state.clean_text = clean(state.message.text)
    state.phones = PHONE.findall(state.clean_text)
    state.model_text = mask_phones(state.clean_text)
