"""core/files.py: what the TUI reads or lists from a repository, and the
paths a person gives it -- checked, bounded, and never a crash."""

import os
import subprocess

import pytest

from adrpy_tui.core import files


def _link_folder(link, target):
    """A folder link: a junction on Windows (no admin needed), else a symlink."""
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)
    else:
        os.symlink(target, link, target_is_directory=True)


def test_a_folder_that_cannot_be_looked_at_is_not_inside(tmp_path, monkeypatch):
    """Every OSError from lstat read as "not there", so a folder denied to the
    person passed the check, and the listing that followed raised
    PermissionError and ended the app."""
    denied = tmp_path / "doc" / "decision-log"
    denied.mkdir(parents=True)
    real = os.lstat

    def lstat(path, *args, **kwargs):
        if os.path.normpath(str(path)) == os.path.normpath(str(denied)):
            raise PermissionError(13, "Access is denied", str(path))
        return real(path, *args, **kwargs)

    monkeypatch.setattr(files.os, "lstat", lstat)
    assert files.inside_repository(tmp_path, denied / "x.md") is False
    assert files.inside_repository(tmp_path, tmp_path / "doc" / "not-yet" / "x.md") is True  # missing: nothing to follow


def test_asking_about_a_path_that_cannot_be_looked_at_is_a_no(tmp_path, monkeypatch):
    """Path.is_dir raises PermissionError on a denied folder (Python 3.12):
    typed in Change repository, it ended the app."""
    class Denied(type(tmp_path)):
        def is_dir(self, **_):
            raise PermissionError(13, "Access is denied")

        is_file = is_dir

    monkeypatch.setattr(files, "Path", Denied)
    assert files.is_dir(tmp_path) is False
    assert files.is_file(tmp_path / "x.md") is False


def test_a_listing_never_follows_a_folder_link(tmp_path):
    """rglob followed a junction below the log folder: it listed files outside
    the repository, and a junction to a parent never ended."""
    log, outside = tmp_path / "log", tmp_path / "outside"
    (log / "2026").mkdir(parents=True)
    outside.mkdir()
    (log / "2026" / "inside.md").write_text("x", encoding="utf-8")
    (outside / "outside.md").write_text("x", encoding="utf-8")
    _link_folder(log / "out", outside)
    _link_folder(log / "2026" / "loop", log)
    assert [path.name for path in files.markdown_files(log)] == ["inside.md"]


def test_a_listing_of_a_folder_that_cannot_be_read_is_empty(tmp_path):
    assert files.markdown_files(tmp_path / "missing") == []


@pytest.mark.parametrize("lines, width", [(3000, 10), (10, 60_000), (3000, 400)])
def test_read_start_reads_only_what_is_shown_and_counts_the_whole_file(tmp_path, lines, width):
    """The preview read the whole file, then cut it: a 500 MB file would take
    a minute and gigabytes. Only the start is kept; the totals are the file's
    -- they were the cut content's when both limits were passed."""
    page = tmp_path / "big.md"
    text = "\n".join("x" * width for _ in range(lines))
    page.write_bytes(text.encode("utf-8"))  # as written, no line-ending translation
    start, total_lines, total_characters = files.read_start(page, 500, 100_000)
    assert (total_lines, total_characters) == (lines, len(text))
    assert len(start) <= 100_000 and len(start.splitlines()) <= 500
    assert text.startswith(start)



def test_a_file_field_that_cannot_be_looked_at_is_missing_not_fatal(monkeypatch):
    """installconfig's --seed was checked with a bare Path.is_file: a file
    the system refuses to look at (access denied) raised out of the run key
    and ended the app."""
    from pathlib import Path

    from adrpy_tui.core.fields import Field, problem

    def refused(self):
        raise PermissionError(5, "Access is denied")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "is_file", refused)
        found = problem(Field("seed", "file"), "C:/denied/seed.json")
    assert found == ("problem.file_missing", {"path": "C:/denied/seed.json"})


class _Status:
    def __init__(self, tag):
        self.st_mode = 0o100644
        self.st_file_attributes = files.stat.FILE_ATTRIBUTE_REPARSE_POINT
        self.st_reparse_tag = tag


@pytest.mark.parametrize("tag, is_link", [
    (0xA000000C, True),   # symlink
    (0xA0000003, True),   # junction (mount point)
    (0xA000001D, True),   # WSL symlink
    (0x8000001B, False),  # app execution alias
    (0x9000701A, False),  # OneDrive placeholder
    (0x80000013, False),  # deduplicated file
])
def test_only_a_reparse_point_that_leads_elsewhere_is_a_link(tag, is_link):
    """Every reparse point was taken for a folder link: a repository under a
    OneDrive folder, whose files are cloud placeholders, was all "outside the
    repository". A symlink, a junction and a WSL symlink lead elsewhere; the
    other tags are the file itself."""
    assert files._is_link(_Status(tag)) is is_link


@pytest.mark.parametrize("content, lines, characters", [
    (b"line\r" * 5000, 5000, 25000),
    ("a\u2028".encode() * 700, 700, 1400),
    (b"x" * ((1 << 20) - 1) + b"\r\n" + b"y", 2, (1 << 20) + 2),  # CRLF across two chunks
    (b"", 0, 0),
    (b"ab\xe2\x82", 1, 3),  # a truncated UTF-8 sequence at the very end
], ids=["cr", "line-separator", "crlf-across-chunks", "empty", "truncated-utf8"])
def test_read_start_counts_lines_as_they_are_cut(tmp_path, content, lines, characters):
    """Lines were counted by LF only but cut by splitlines: a file of CR line
    ends showed 500 lines and said it had 1, so no note said it was cut."""
    path = tmp_path / "a.md"
    path.write_bytes(content)
    start, total_lines, total_characters = files.read_start(path, 500, 100_000)
    assert (total_lines, total_characters) == (lines, characters)
    assert len(start.splitlines()) == min(lines, 500) or characters > 100_000
    if content == b"ab\xe2\x82":
        assert start == "ab\ufffd"


def test_markdown_files_lists_in_order_any_case_and_only_the_top_when_asked(tmp_path):
    for name in ("b.md", "A.MD", "c.txt", "sub/d.md", "z.md"):
        (tmp_path / name).parent.mkdir(exist_ok=True)
        (tmp_path / name).write_text("x", encoding="utf-8")
    assert [p.relative_to(tmp_path).as_posix() for p in files.markdown_files(tmp_path)] == [
        "A.MD", "b.md", "sub/d.md", "z.md"]  # os.walk gives z.md before the subfolder's files
    assert [p.name for p in files.markdown_files(tmp_path, recursive=False)] == ["A.MD", "b.md", "z.md"]


def test_the_path_option_refuses_a_folder_that_cannot_be_looked_at(monkeypatch, capsys):
    """--path was checked with a bare Path.is_dir: a folder the system refuses
    to look at raised instead of a usage error."""
    from pathlib import Path

    from adrpy_tui import __main__

    def refused(self):
        raise PermissionError(5, "Access is denied")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "is_dir", refused)
        with pytest.raises(SystemExit) as ended:
            __main__.main(["--path", "C:/denied"])
    assert ended.value.code == 2
    assert "--path is not a directory" in capsys.readouterr().err
