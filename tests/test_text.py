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
