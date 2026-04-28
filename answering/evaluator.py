from rapidfuzz import fuzz

THRESHOLD = 78
KEYWORD_THRESHOLD = 85


def evaluate(expected: str, given: str, keywords: list[str]) -> bool:
    e = expected.lower().strip()
    g = given.lower().strip()
    if not g:
        return False
    if fuzz.token_sort_ratio(e, g) >= THRESHOLD:
        return True
    return any(fuzz.partial_ratio(kw.lower(), g) >= KEYWORD_THRESHOLD for kw in keywords)
