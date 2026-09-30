from adrpy_tui.core.suggest import prefix_suggestion, similar

CANDIDATES = ["app-security", "backend", "security", "Security Team"]


def test_prefix_suggestion_continues_what_was_typed_case_insensitively():
    assert prefix_suggestion("SEC", CANDIDATES) == "security"


def test_prefix_suggestion_never_suggests_what_was_already_typed_or_a_non_continuation():
    assert prefix_suggestion("backend", CANDIDATES) is None
    assert prefix_suggestion("curity", CANDIDATES) is None
    assert prefix_suggestion("", CANDIDATES) is None


def test_similar_lists_containing_values_first_then_close_ones():
    # All three contain "security"; then by similarity: 1.0, 0.8, 0.76.
    assert similar("security", CANDIDATES) == ["security", "app-security", "Security Team"]
    assert similar("secruity", CANDIDATES)[0] == "security"


def test_similar_with_nothing_typed_lists_every_value():
    assert similar(" ", CANDIDATES) == CANDIDATES
