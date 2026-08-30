import logging
import re
from dataclasses import dataclass

# Patterns that indicate an attempt to hijack the LLM's instructions.
# Case-insensitive, matched against raw scraped web content before it
# ever reaches an extraction prompt.
_INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?previous instructions", re.IGNORECASE),
    re.compile(r"ignore the (above|prior) (instructions|prompt)", re.IGNORECASE),
    re.compile(r"you are now (a |an )?[\w\s]+ with no restrictions", re.IGNORECASE),
    re.compile(r"disregard (your|all|the) (system )?(prompt|instructions)", re.IGNORECASE),
    re.compile(r"reveal your (system )?prompt", re.IGNORECASE),
    re.compile(r"act as (if you are|a) [\w\s]+ (with|without) (no )?restrictions", re.IGNORECASE),
]

_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

logger = logging.getLogger(__name__)


@dataclass
class SanitizationEvent:
    pattern_matched: str
    original_snippet: str


def sanitize_content(raw_text: str) -> str:
    """Strip prompt-injection patterns and HTML tags from scraped content.

    This runs BEFORE any LLM sees the content, so injected instructions
    never make it into a prompt in the first place. Every match is logged
    as a SanitizationEvent for audit purposes (spec FR6: "Log sanitization
    events").
    """
    cleaned = _HTML_TAG_PATTERN.sub("", raw_text)

    for pattern in _INJECTION_PATTERNS:
        for match in pattern.finditer(cleaned):
            event = SanitizationEvent(
                pattern_matched=pattern.pattern, original_snippet=match.group(0)
            )
            logger.warning(
                "Sanitization event: pattern=%r snippet=%r",
                event.pattern_matched,
                event.original_snippet,
            )
        cleaned = pattern.sub("[removed]", cleaned)

    # Collapse whitespace left behind by removals
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned
