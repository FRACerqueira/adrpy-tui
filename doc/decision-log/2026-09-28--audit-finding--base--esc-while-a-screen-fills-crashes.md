# Leaving config, migrate or the skills list while it was being filled crashed the TUI

**Front:** Async event ordering in one session (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 1

The async handlers checked `is_attached` once, then queried widgets of a screen being removed (NoMatches). Fixed: AdrpyScreen.read ignores a failure of a screen no longer open, PagedList.update_page and migrate's refresh return when detached. Reproduced (config every time); covered by tests/test_async_screens.py::test_leaving_a_screen_while_it_is_being_filled_is_harmless.
