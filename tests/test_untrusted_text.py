"""Text the TUI did not write -- file and folder names, a decision's links,
what adrpy returns -- is shown as it is: never read as markup, no control
character reaching the terminal, and a character that changes how the
rest of a line reads (bidirectional, invisible) shown as <U+XXXX>
(ADR006V01's audit, SECURITY.md). Every screen that shows such text is
driven here with hostile names, and everything it draws is read back."""

import asyncio

from textual.widgets import Select
from textual.widgets._markdown import MarkdownParagraph

from adrpy_tui.ui.app import AdrpyTui
from adrpy_tui.ui.preview import PreviewScreen

from conftest import FakeClient, settle
from test_ui import REPO_CONFIG, _decision, _drawn_segments, _walk

ESC = chr(27)
RLO = chr(0x202E)  # right-to-left override: "abc" + RLO + "dm.txt" reads as "abctxt.md"
SHOWN_RLO = "<U+202E>"


def _drawn(app):
    return "".join(text for text, _, _ in _drawn_segments(app))


def _assert_safe(app, *pieces):
    drawn = _drawn(app)
    assert ESC not in drawn
    assert RLO not in drawn
    missing = [piece for piece in pieces if piece not in drawn]
    assert missing == [], drawn[:2000]


def _run(app, scenario, notifications=False):
    async def main():
        async with app.run_test(size=(140, 60), notifications=notifications) as pilot:
            await settle(pilot)
            await scenario(pilot)

    asyncio.run(main())


def _repo_client(tmp_path, decisions=(), **answers):
    for decision in decisions:
        decision["path"] = str(tmp_path / "doc" / "adr" / decision.pop("folder", "") / decision["filename"])
    return FakeClient(answers={
        "config": {"success": True, "data": {"config": REPO_CONFIG, "warnings": []}},
        "explore": {"success": True, "data": {"decisions": list(decisions), "warnings": []}},
        **answers})


def test_explore_shows_a_hostile_folder_and_name_as_they_are(tmp_path, user_state):
    """A folder named "[/x]" crashed the folder filter (a closing tag with
    nothing to close) and one named "[@click=app.quit]" became an action."""
    decision = _decision(f"ADR001V01-[b]a{RLO}b.md", update="Accepted", updated="2026-02-01")
    decision["folder"] = "[/x]"
    app = AdrpyTui(tmp_path, client=_repo_client(tmp_path, [decision]), user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["explore", "explore.explore"])
        _assert_safe(app, "ADR001V01-[b]a", SHOWN_RLO, "[/x]")
        select = app.screen.query(Select).first()
        select.focus()
        await pilot.press("enter")
        await settle(pilot)
        _assert_safe(app, "[/x]")
        await pilot.press("escape")
        await _walk(app, pilot, [":detail"])
        _assert_safe(app, "ADR001V01-[b]a", SHOWN_RLO)

    _run(app, scenario)


def test_the_picker_and_the_confirmation_show_a_hostile_name_as_it_is(tmp_path, user_state):
    app = AdrpyTui(tmp_path, client=_repo_client(tmp_path, [_decision(f"ADR001V01-[b]a{RLO}b.md")]),
                   user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["decisions", "decisions.approve"])
        _assert_safe(app, "ADR001V01-[b]a", SHOWN_RLO)
        app.screen.query_one("#field-file-options").focus()
        await pilot.press("enter")
        await pilot.press("ctrl+r")
        await settle(pilot)
        _assert_safe(app, "adrpy", "approve", "ADR001V01-[b]a", SHOWN_RLO)

    _run(app, scenario)


def test_check_shows_a_hostile_file_name_as_it_is(tmp_path, user_state):
    errors = [{"code": "no-header", "file": f"C:/r/[b]x{RLO}.md", "hint": "[b]Run migrate."}]
    app = AdrpyTui(tmp_path, client=_repo_client(tmp_path, check={
        "success": False, "code": "repository-inconsistent", "detail": "x", "warnings": [],
        "data": {"errors": errors}}), user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["explore", "explore.check"])
        _assert_safe(app, "[b]x", SHOWN_RLO, "[b]Run")

    _run(app, scenario)


def test_the_log_browser_shows_a_hostile_entry_name_as_it_is(tmp_path, user_state):
    log = tmp_path / "doc" / "decision-log"
    log.mkdir(parents=True)
    (log / f"2026-01-01--[b]aud{RLO}it--scope--slug.md").write_text("# x\n", encoding="utf-8")
    app = AdrpyTui(tmp_path, client=_repo_client(tmp_path), user_state=user_state)

    async def scenario(pilot):
        await _walk(app, pilot, ["log", "log.browse"])
        _assert_safe(app, "[b]aud", SHOWN_RLO)
        app.screen.query(Select).first().focus()
        await pilot.press("enter")
        await settle(pilot)
        _assert_safe(app, "[b]aud", SHOWN_RLO)

    _run(app, scenario)


def test_the_header_shows_a_hostile_repository_path_as_it_is(tmp_path, user_state):
    repo = tmp_path / f"[b]re{RLO}po"
    repo.mkdir()
    app = AdrpyTui(repo, client=_repo_client(repo), user_state=user_state)

    async def scenario(pilot):
        _assert_safe(app, "[b]re", SHOWN_RLO)

    _run(app, scenario)


def test_a_hostile_link_in_a_decision_is_only_named(tmp_path, user_state):
    """A link "[t](<foo[/]>)" crashed the app from its notification (markup
    on), and "%1b" in one reached the terminal as ESC: Textual unquotes a
    link before handing it over."""
    page = tmp_path / "ADR001V01-a.md"
    links = ["<foo[/]>", "<[@click=app.quit]x>", "%1b[2Jgone.md", "<[/x]missing.md>"]
    page.write_text("# A\n\n" + "\n\n".join(f"see [t{i}]({link})" for i, link in enumerate(links)) + "\n",
                    encoding="utf-8")
    app = AdrpyTui(tmp_path, client=_repo_client(tmp_path), user_state=user_state)

    async def scenario(pilot):
        app.push_screen(PreviewScreen(page))
        await settle(pilot)
        for paragraph in app.screen.query(MarkdownParagraph):
            for span in paragraph._content.spans:
                if "link(" in str(span.style):
                    href = str(span.style).split("link(", 1)[1].rsplit(")", 1)[0].strip("'\"")
                    await paragraph.action_link(href)
                    await settle(pilot)
        assert isinstance(app.screen, PreviewScreen)
        messages = [notification.message for notification in app._notifications]
        assert len(messages) == 4
        assert all(ESC not in message for message in messages)
        assert any(message.endswith("missing.md") for message in messages)  # a long path wraps when drawn
        _assert_safe(app, "foo[/]", "[@click=app.quit]x")

    _run(app, scenario, notifications=True)
