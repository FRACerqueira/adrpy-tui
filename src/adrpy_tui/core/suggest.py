"""Suggestions from values a repository already uses (scope, domain).

Textual shows an inline suggestion only as a continuation of what was
typed, so the inline one is a prefix match; values that merely contain the
text or look like it are listed separately.
"""

from difflib import SequenceMatcher

SIMILARITY_THRESHOLD = 0.8


def prefix_suggestion(value, candidates):
    """The first candidate that continues `value` (case-insensitively), or
    None."""
    if not value:
        return None
    folded = value.casefold()
    for candidate in candidates:
        if len(candidate) > len(value) and candidate.casefold().startswith(folded):
            return candidate
    return None


def similar(value, candidates):
    """Candidates containing `value` first, then those similar to it, best
    first; every candidate when nothing is typed."""
    if not value.strip():
        return list(candidates)
    folded = value.casefold()
    scored = []
    for candidate in candidates:
        other = candidate.casefold()
        contains = folded in other
        ratio = SequenceMatcher(None, folded, other).ratio()
        if contains or ratio >= SIMILARITY_THRESHOLD:
            scored.append((not contains, -ratio, candidate))
    return [candidate for *_, candidate in sorted(scored)]
