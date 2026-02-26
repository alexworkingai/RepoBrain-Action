from __future__ import annotations

import hashlib
import re

TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)
PATH_SPLIT_RE = re.compile(r"[\/.\-_]+")
NON_ALNUM_RE = re.compile(r"[^0-9a-z]+")

STOP_WORDS = {
    # EN
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "where",
    "with",
    # RU
    "а",
    "в",
    "во",
    "где",
    "для",
    "и",
    "из",
    "как",
    "к",
    "ли",
    "на",
    "но",
    "о",
    "по",
    "с",
    "со",
    "у",
    "что",
    "это",
    "эта",
    "этот",
}


def tokenize_text(value: str) -> list[str]:
    """Unicode-friendly tokenization with a small RU/EN stop-list."""
    tokens = [token.lower() for token in TOKEN_RE.findall(value or "")]
    return [token for token in tokens if token and token not in STOP_WORDS]


def tokenize_pathish(value: str) -> list[str]:
    """Tokenize file paths / ids and add collapsed variants for snake-case identifiers."""
    tokens = tokenize_text(value)
    extras: list[str] = []

    for segment in PATH_SPLIT_RE.split((value or "").lower()):
        if not segment:
            continue
        parts = [part for part in segment.split("_") if part]
        if len(parts) > 1:
            extras.extend(parts)
            collapsed = "".join(parts)
            if collapsed:
                extras.append(collapsed)

    merged = tokens + [token for token in extras if token not in STOP_WORDS]
    # Preserve order while deduplicating.
    return list(dict.fromkeys(merged))


def hash_token32(token: str) -> int:
    """Hash a token into a stable 32-bit integer using blake2s."""
    digest = hashlib.blake2s(token.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "little")


def build_signature_from_tokens(tokens: list[str], max_items: int = 128) -> list[int]:
    """Build a sorted unique signature list of hashed tokens."""
    values = sorted({hash_token32(token) for token in tokens})
    return values[:max_items]


def build_chunk_signature(
    *,
    file_path: str,
    chunk_id: str,
    text: str | None = None,
    include_text: bool = False,
    text_chars: int = 256,
    max_items: int = 128,
) -> list[int]:
    """Build a hashed token signature for a chunk without storing raw text."""
    tokens = tokenize_pathish(file_path) + tokenize_pathish(chunk_id)
    if include_text and text:
        tokens.extend(tokenize_text(text[:text_chars]))
    return build_signature_from_tokens(tokens, max_items=max_items)


def build_query_signature(question: str, max_items: int = 128) -> list[int]:
    """Build a hashed token signature for a user query."""
    return build_signature_from_tokens(tokenize_text(question), max_items=max_items)


def compact_ascii(value: str) -> str:
    """ASCII-only compact normalization used by heuristic boosts."""
    return NON_ALNUM_RE.sub("", (value or "").lower())


def extract_latin_identifiers(value: str) -> list[str]:
    """Extract Latin identifiers and helpful subparts for boost heuristics."""
    raw = re.findall(r"[A-Za-z][A-Za-z0-9_]*", value or "")
    identifiers: list[str] = []
    for item in raw:
        lowered = item.lower()
        identifiers.append(lowered)
        if "_" in lowered:
            identifiers.extend(part for part in lowered.split("_") if part)
            identifiers.append(lowered.replace("_", ""))
        else:
            # Split coarse alpha/num runs (useful for mixed identifiers)
            identifiers.extend(re.findall(r"[a-z]+|\d+", lowered))
    return [token for token in dict.fromkeys(identifiers) if token]
