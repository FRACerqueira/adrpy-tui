import pathlib

from adrpy_tui.core.state import UserState


def test_language_and_menu_items_survive_a_new_session(tmp_path):
    path = tmp_path / "adrpy-tui" / "state.json"
    state = UserState(path)
    state.set_language("pt-br")
    state.set_appearance("light")
    state.set_color("tui-banner", "#FFA500")
    state.remember("main", "decisions")

    again = UserState(path)
    assert again.language == "pt-br"
    assert again.appearance == "light"
    assert again.colors == {"tui-banner": "#FFA500"}
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


def test_a_state_file_saved_with_a_bom_is_read(tmp_path):
    """Notepad saves UTF-8 with a BOM: json.loads refused it, the person's
    language, colors and keys were ignored, then overwritten on the next save."""
    path = tmp_path / "state.json"
    path.write_bytes(b"\xef\xbb\xbf" + b'{"language": "pt-br", "keys": {"run": "f5"}}')
    state = UserState(path)
    assert (state.language, state.keys) == ("pt-br", {"run": "f5"})


def test_a_save_that_fails_half_way_leaves_the_file_as_it_was(tmp_path, monkeypatch):
    """The state was written in place: a full disk or a crash half-way left
    a truncated file, and the next run lost every setting."""
    path = tmp_path / "state.json"
    state = UserState(path)
    state.set_language("pt-br")
    before = path.read_text(encoding="utf-8")
    original = pathlib.Path.write_text

    def half_then_fail(self, text, *args, **kwargs):
        original(self, text[:5], *args, **kwargs)
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(pathlib.Path, "write_text", half_then_fail)
    state.set_language("en-us")
    monkeypatch.undo()
    assert path.read_text(encoding="utf-8") == before



def test_the_state_path_does_not_need_a_home_folder(monkeypatch):
    """Path.home() raises when no home can be determined (a service account,
    a stripped environment): the TUI did not start."""
    from adrpy_tui.core import state

    def no_home():
        raise RuntimeError("Could not determine home directory.")

    monkeypatch.setattr(state.Path, "home", staticmethod(no_home))
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    assert state.default_state_path().name == "state.json"



def test_a_state_file_nested_too_deep_to_read_starts_empty(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("[" * 100000, encoding="utf-8")
    assert UserState(path).language is None


def test_the_update_check_is_on_and_pre_releases_off_until_changed(tmp_path):
    path = tmp_path / "state.json"
    state = UserState(path)
    assert state.update_check is True and state.prereleases is False
    state.set_update_check(False)
    state.set_prereleases(True)

    again = UserState(path)
    assert again.update_check is False and again.prereleases is True


def test_an_update_setting_that_is_not_a_boolean_is_its_default(tmp_path):
    path = tmp_path / "state.json"
    path.write_text('{"update_check": "no", "prereleases": 1}', encoding="utf-8")
    state = UserState(path)
    assert state.update_check is True and state.prereleases is False
