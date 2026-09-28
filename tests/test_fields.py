from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from adrpy_tui.core.fields import TITLE_FORBIDDEN, Field, build_flags, problem

TITLE = Field("title", "text", required=True, forbidden=TITLE_FORBIDDEN)
SCOPE = Field("scope", "text", forbidden="|")
REFDATE = Field("refdate", "date")
EMPTY = Field("empty", "switch")


@pytest.mark.parametrize("field, value, expected", [
    (TITLE, "", ("problem.required", {})),
    (TITLE, "   ", ("problem.required", {})),
    (TITLE, "Use a/b", ("problem.forbidden", {"char": "/"})),
    (TITLE, "Use PostgreSQL", None),
    (SCOPE, "", None),
    (SCOPE, "  ", ("problem.blank", {})),
    (SCOPE, "a|b", ("problem.forbidden", {"char": "|"})),
    (REFDATE, "", None),
    (REFDATE, "2026-13-01", ("problem.date_format", {})),
    (REFDATE, "2026-01-", ("problem.date_format", {})),
    (REFDATE, (date.today() + timedelta(days=1)).isoformat(), ("problem.date_future", {})),
    (REFDATE, date.today().isoformat(), None),
    (EMPTY, True, None),
])
def test_problem(field, value, expected):
    assert problem(field, value) == expected


def test_build_flags_puts_the_repository_first_and_leaves_out_empty_values():
    form = SimpleNamespace(PATH_FLAG="path", FIELDS=(TITLE, SCOPE, REFDATE, EMPTY))
    values = {"title": "Use it", "scope": "", "refdate": "2026-01-02", "empty": True}
    assert build_flags(form, "repo", values) == ["--path", "repo", "--title", "Use it", "--refdate", "2026-01-02", "--empty"]


def test_build_flags_leaves_out_an_off_switch():
    form = SimpleNamespace(PATH_FLAG=None, FIELDS=(EMPTY,))
    assert build_flags(form, "repo", {"empty": False}) == []
