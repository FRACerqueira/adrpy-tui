from adrpy_tui.core.state import UserState


def test_language_and_menu_items_survive_a_new_session(tmp_path):
    path = tmp_path / "adrpy-tui" / "state.json"
    state = UserState(path)
    state.set_language("pt-br")
    state.remember("main", "decisions")

    again = UserState(path)
    assert again.language == "pt-br"
    assert again.last("main") == "decisions"


def test_an_unreadable_or_malformed_file_starts_empty(tmp_path):
    path = tmp_path / "state.json"
    for content in ("not json", "[]", '{"language": 3, "last_menu_item": {"main": 4}}'):
        path.write_text(content, encoding="utf-8")
        state = UserState(path)
        assert state.language is None and state.last("main") is None


def test_a_file_that_cannot_be_written_is_skipped(tmp_path):
    blocker = tmp_path / "not-a-folder"
    blocker.write_text("", encoding="utf-8")
    state = UserState(blocker / "state.json")
    state.set_language("en-us")  # must not raise
    assert state.language == "en-us"
