from rapidfuzz import fuzz

THRESHOLD = 78
KEYWORD_THRESHOLD = 85


def evaluate(expected: str, given: str, keywords: list[str]) -> bool:
    e = expected.lower().strip()
    g = given.lower().strip()
    if len(g) < 2:
        return False
    if fuzz.token_sort_ratio(e, g) >= THRESHOLD:
        return True
    # partial_ratio aligns the shorter string against any substring of the longer one,
    # so a 1-2 char answer trivially matches any keyword containing those chars.
    # Require g to be at least 60% the length of the keyword before checking.
    return any(
        len(g) * 5 >= len(kw) * 3 and
        fuzz.partial_ratio(kw.lower(), g) >= KEYWORD_THRESHOLD
        for kw in keywords
    )
