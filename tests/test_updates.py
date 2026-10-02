import http.client
import io
import json
import time

import pytest
from packaging.version import Version

from adrpy_tui.core import updates, versions

# The real one: conftest's no_pypi replaces updates.published in every test,
# and these tests replace only what it opens.
published = updates.published

_ORDERED = [
    "0.1.dev0", "0.1.0a1", "0.1.0b2", "0.1.0rc1", "0.1.0", "0.1.0.post1", "0.1.1.dev3", "0.1.1",
    "0.2.0.dev1", "0.2.0a1.dev2", "0.2.0a1", "0.2.0rc1", "0.2", "0.2.0.post1.dev1", "0.2.1", "0.10.0", "1.0.0",
]


@pytest.mark.parametrize("first", _ORDERED)
@pytest.mark.parametrize("second", _ORDERED)
def test_the_order_of_versions_agrees_with_pep_440(first, second):
    ours = (versions.order(first) > versions.order(second)) - (versions.order(first) < versions.order(second))
    theirs = (Version(first) > Version(second)) - (Version(first) < Version(second))
    assert ours == theirs


def test_a_local_part_does_not_change_the_order():
    assert versions.order("0.2.1.dev3+g6e69e7573") == versions.order("0.2.1.dev3")


@pytest.mark.parametrize("text", ["", "abc", "1.0-beta", "1.0.0rc", "v1.0", None])
def test_a_version_that_is_not_pep_440_is_refused(text):
    with pytest.raises(ValueError):
        versions.order(text)


@pytest.mark.parametrize("installed, published, prereleases, expected", [
    ("0.2.0", ["0.1.0", "0.2.0"], False, None),
    ("0.2.0", ["0.1.0", "0.2.0", "0.2.1", "0.3.0"], False, "0.3.0"),
    ("0.2.0", ["0.3.0rc1"], False, None),
    ("0.2.0", ["0.3.0rc1"], True, "0.3.0rc1"),
    ("0.2.0", ["0.2.1", "0.3.0rc1"], False, "0.2.1"),
    ("0.2.0", ["0.2.1", "0.3.0rc1"], True, "0.3.0rc1"),
    ("0.3.0rc1", ["0.3.0"], False, "0.3.0"),  # a release candidate's final release is newer
    ("0.2.0", ["0.3.0.dev1"], True, None),  # development builds are never announced
    ("0.2.1.dev3+g6e69e7573", ["0.2.0"], False, None),  # a development install ahead of PyPI
    ("0.2.1.dev3+g6e69e7573", ["0.2.1"], False, "0.2.1"),
    ("0.2.0", ["0.2.0.post1"], False, "0.2.0.post1"),
    ("0.2.0", ["not a version", "0.2.1"], False, "0.2.1"),
    ("unknown (not installed)", ["0.3.0"], False, None),
])
def test_newer_is_the_newest_published_version_above_the_installed_one(installed, published, prereleases, expected):
    assert updates.newer(installed, published, prereleases) == expected


def test_a_newer_version_from_pypi_is_said_without_terminal_controls():
    assert updates.newer("0.2.0", ["0.3.0"], False) == "0.3.0"
    assert "\x1b" not in (updates.newer("0.2.0", ["0.3.0+\x1b[2J"], False) or "")


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _answer(payload):
    raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return lambda url, timeout: _Response(raw)


def _file(yanked=False):
    return {"filename": "x.whl", "yanked": yanked}


def test_published_lists_the_versions_with_a_file_not_yanked(monkeypatch):
    monkeypatch.setattr(updates, "_open", _answer({"releases": {
        "0.1.0": [_file(), _file()],
        "0.2.0": [_file(yanked=True), _file()],
        "0.2.1": [_file(yanked=True)],
        "0.3.0": [],
    }}))
    assert sorted(published()) == ["0.1.0", "0.2.0"]


def test_published_asks_pypi_for_adrpy_tui_with_a_timeout(monkeypatch):
    asked = []

    def opened(url, timeout):
        asked.append((url, timeout))
        return _Response(b'{"releases": {}}')

    monkeypatch.setattr(updates, "_open", opened)
    published()
    assert asked == [("https://pypi.org/pypi/adrpy-tui/json", updates.TIMEOUT)]


@pytest.mark.parametrize("payload", [
    b"not json", b"\xff\xfe", b"[]", b'{"releases": []}', b'{"releases": {"0.1.0": "x"}}',
    b'{"releases": {"0.1.0": ["x"]}}', b"[" * 100_000,
], ids=["text", "not-utf-8", "a-list", "releases-a-list", "files-a-string", "files-not-objects", "nested-too-deep"])
def test_an_answer_that_cannot_be_read_is_an_error_the_check_can_catch(monkeypatch, payload):
    monkeypatch.setattr(updates, "_open", _answer(payload))
    with pytest.raises(updates.CHECK_ERRORS):
        published()


def test_an_answer_too_large_is_refused(monkeypatch):
    """Valid JSON, so only the size refuses it."""
    monkeypatch.setattr(updates, "_open", _answer(b'{"releases": {}}' + b" " * updates.LIMIT))
    with pytest.raises(ValueError):
        published()


@pytest.mark.parametrize("error", [http.client.IncompleteRead(b""), http.client.BadStatusLine("garbage"),
                                   http.client.LineTooLong("header line")], ids=type)
def test_an_http_answer_broken_off_or_not_http_is_an_error_the_check_can_catch(monkeypatch, error):
    """A captive portal, a proxy or a connection reset mid-answer: http.client
    raises these, which are neither OSError nor ValueError."""

    class Broken(_Response):
        def read1(self, size=-1):
            raise error

        read = read1

    monkeypatch.setattr(updates, "_open", lambda url, timeout: Broken(b""))
    with pytest.raises(updates.CHECK_ERRORS):
        published()


def test_an_answer_that_trickles_in_is_given_up_at_the_deadline(monkeypatch):
    """TIMEOUT bounds each read of the socket, not the whole answer: a byte
    every so often would hold the check for the whole run."""

    class Trickle:
        def __init__(self):
            self.started = time.monotonic()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

        def read1(self, size=-1):  # ends after 3 seconds, so a check with no deadline fails rather than hangs
            time.sleep(0.02)
            return b" " if time.monotonic() - self.started < 3 else b""

        def read(self, size=-1):  # as http.client's: until `size` bytes have come
            data = b""
            while len(data) < size and time.monotonic() - self.started < 3:
                data += self.read1(size)
            return data

    monkeypatch.setattr(updates, "DEADLINE", 0.3, raising=False)
    monkeypatch.setattr(updates, "TIMEOUT", 0.2)
    monkeypatch.setattr(updates, "_open", lambda url, timeout: Trickle())
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        published()
    assert time.monotonic() - started < 1.5


@pytest.mark.parametrize("text", ["٣.0", "1.٠", "1" * 65 + ".0", "1." + "0" * 70])
def test_a_version_with_digits_other_than_ascii_or_too_long_is_refused(text):
    with pytest.raises(ValueError):
        versions.order(text)


def test_a_version_from_pypi_with_other_digits_is_never_offered():
    assert updates.newer("0.2.0", ["0.2.1", "٣.0", "9" * 4000 + ".0"], False) == "0.2.1"
