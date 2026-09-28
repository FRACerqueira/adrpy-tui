import pytest

from adrpy_tui.core.migration import Part, build, parse, propose, read


def test_build_and_parse_are_each_other_s_inverse():
    parts = {"N": Part(0, 4), "T": Part(5), "V": Part(10, 2), "P": Part(20, 3)}
    assert build(parts) == "N00:04T05V10:02P20:03"
    assert parse("N00:04T05V10:02P20:03") == parts


@pytest.mark.parametrize("pattern", ["", "N0:4T5", "T05N00:04", "N00:04", "N00:04T05X01:01", None])
def test_a_malformed_pattern_is_not_parsed(pattern):
    assert parse(pattern) is None


def test_read_shows_what_a_part_reads_from_a_name():
    assert read("0001-use-postgres", Part(0, 4)) == "0001"
    assert read("0001-use-postgres", Part(5)) == "use-postgres"


@pytest.mark.parametrize("stem, expected", [
    ("0001-use-postgres", "N00:04T05"),
    ("0001Title", "N00:04T04"),
    ("12_drop-soap", "N00:02T03"),
    ("decision", "N00:01T01"),  # no digits: a start to edit
])
def test_propose_reads_the_leading_digits_as_the_number(stem, expected):
    assert build(propose(stem)) == expected
