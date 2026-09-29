from adrpy_tui.core.text import printable


def test_escape_sequences_and_other_control_characters_are_dropped():
    assert printable("# Title\x1b[2J\x1b]0;owned\x07 end\x9b") == "# Title[2J]0;owned end"


def test_a_log_entry_s_name_gives_its_date_classification_scope_and_slug():
    from adrpy_tui.ui.logs import entry_parts

    assert entry_parts("2026-02-05--audit-finding--security--no-expiry.md") == (
        "2026-02-05", "audit-finding", "security", "no-expiry")
    assert entry_parts("notes.md") == ("", "", "", "notes")


def test_text_layout_is_kept():
    assert printable("a\tb\r\nc\n") == "a\tb\nc\n"


def test_explore_s_columns_are_aligned_by_terminal_cells_and_only_the_last_is_never_cut():
    from adrpy_tui.ui.explore import _cells

    assert _cells(["ab", "cd", "observabilidade"], widths=(4, 4, 4)) == "ab  cd  observabilidade"
    assert _cells(["abcdef", "x", "y"], widths=(4, 4, 4)) == "abc x   y"
    assert _cells(["提案済み", "x"], widths=(6, 4)) == "提案  x"  # two cells a character


def test_safe_keeps_crlf_and_drops_a_lone_carriage_return():
    from adrpy_tui.core.text import safe

    assert safe("a\r\nb\rc\x1bd\te") == "a\r\nbcd\te"


def test_a_folder_s_name_in_the_tree_is_plain_text_without_control_characters():
    """Windows forbids control characters in a name, Linux and macOS do not;
    and Textual's tree reads a label as markup."""
    from adrpy_tui.ui.repository import FoldersTree

    label = FoldersTree.process_label(None, "[red]x\x1b]0;owned\x07")
    assert (label.plain, label.spans) == ("[red]x]0;owned", [])


def test_visible_writes_out_every_character_that_hides_itself():
    """Bidirectional, zero-width and separator characters (Cf, Zl, Zp) and a
    lone surrogate (Cs) are written out; what only decorates a letter stays."""
    from adrpy_tui.core.text import visible

    for char in ("\u202e", "\u200b", "\ufeff", "\u2066", "\u2028", "\u2029", "\ud800"):
        assert visible(f"a{char}b") == f"a<U+{ord(char):04X}>b"
    assert visible("e\u0301\tx\ny\x1b") == "e\u0301\tx\ny"


def test_a_lone_surrogate_never_reaches_the_terminal():
    """A file name may hold one (NTFS allows it; a non-UTF-8 byte decodes to
    one on Linux); written to the terminal it killed Textual's writer thread
    and froze the screen for the rest of the session."""
    shown = printable("0001-le\ud800gacy")
    assert shown == "0001-le\ufffdgacy"
    shown.encode("utf-8")



def test_a_field_keeps_only_printable_text():
    """Free text in a field -- typed, pasted, or filled from a file -- never
    carries a control, a lone surrogate or a character that hides itself
    (Cf, Zl, Zp): what is confirmed is then what runs, and what is drawn can
    be encoded. A multi-line field keeps its line breaks (CRLF too) and tabs."""
    from adrpy_tui.core.text import field_text

    dirty = "a\x1bb\x7fc\td\ne\r\nf\rg\ud800h\u202ei\u200bj\u2028k"
    assert field_text(dirty) == "abcdefghijk"
    assert field_text(dirty, multiline=True) == "abc\td\ne\r\nfghijk"
    assert field_text("Decisão · 決定 🙂") == "Decisão · 決定 🙂"
