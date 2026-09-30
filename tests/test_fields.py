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


APPROVE_DATE = Field("refdate", "date", not_before=("date_create",))
LAST_CHANGE_DATE = Field("refdate", "date", not_before=("date_update", "date_create"))


@pytest.mark.parametrize("header, earliest", [
    ({"date_create": "2026-01-10", "date_update": "2026-02-01"}, "2026-02-01"),  # updated: its last update
    ({"date_create": "2026-01-10", "date_update": None}, "2026-01-10"),          # never updated: its creation
])
def test_a_date_cannot_be_before_the_first_date_the_decision_has_of_a_list(header, earliest):
    day_before = (date.fromisoformat(earliest) - timedelta(days=1)).isoformat()
    assert problem(LAST_CHANGE_DATE, day_before, {"header": header}) == ("problem.date_before", {"date": earliest})
    assert problem(LAST_CHANGE_DATE, earliest, {"header": header}) is None
CREATED = {"header": {"date_create": "2026-01-10"}}


@pytest.mark.parametrize("value, decision, expected", [
    ("2026-01-09", CREATED, ("problem.date_before", {"date": "2026-01-10"})),
    ("2026-01-10", CREATED, None),
    ("2026-01-09", None, None),  # no decision chosen yet: adrpy decides
    ("2026-01-09", {"header": {"date_create": None}}, None),  # a migrated placeholder
    ("", CREATED, None),
])
def test_a_date_cannot_be_before_the_chosen_decision_s_own_date(value, decision, expected):
    assert problem(APPROVE_DATE, value, decision) == expected


def test_a_decision_is_required_like_any_other_value():
    assert problem(Field("file", "decision", required=True), "") == ("problem.required", {})


SOURCE = Field("source", "choice", choices=("language", "seed"), local=True)
LANGUAGE = Field("language", "language", shown_when=("source", "language"))
SEED = Field("seed", "file", shown_when=("source", "seed"), required_if_shown=True)


def test_a_local_field_and_a_hidden_one_are_never_sent():
    form = SimpleNamespace(PATH_FLAG="path", FIELDS=(SOURCE, LANGUAGE, SEED))
    assert build_flags(form, "repo", {"source": "language", "language": "pt-br", "seed": "x.json"}) == [
        "--path", "repo", "--language", "pt-br"]
    assert build_flags(form, "repo", {"source": "seed", "language": "pt-br", "seed": "x.json"}) == [
        "--path", "repo", "--seed", "x.json"]


def test_a_file_must_exist_and_is_required_while_shown(tmp_path):
    existing = tmp_path / "seed.json"
    existing.write_text("{}", encoding="utf-8")
    assert problem(SEED, "") == ("problem.required", {})
    assert problem(SEED, str(tmp_path / "nope.json")) == ("problem.file_missing", {"path": str(tmp_path / "nope.json")})
    assert problem(SEED, str(existing)) is None


def test_build_flags_puts_the_repository_first_and_leaves_out_empty_values():
    form = SimpleNamespace(PATH_FLAG="path", FIELDS=(TITLE, SCOPE, REFDATE, EMPTY))
    values = {"title": "Use it", "scope": "", "refdate": "2026-01-02", "empty": True}
    assert build_flags(form, "repo", values) == ["--path", "repo", "--title", "Use it", "--refdate", "2026-01-02", "--empty"]


def test_build_flags_leaves_out_an_off_switch():
    form = SimpleNamespace(PATH_FLAG=None, FIELDS=(EMPTY,))
    assert build_flags(form, "repo", {"empty": False}) == []
