"""Choosing a decision: a filter by name over the repository's decisions,
each with its label, in the interface's paged list. By default only the ones the command can
take are listed; the others can be shown, disabled (adrpy's own failure
code stays the final word)."""

from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Input, Label, OptionList, Static, Switch

from adrpy_tui.core.text import visible
from adrpy_tui.core import keys
from adrpy_tui.core.decisions import state
from adrpy_tui.ui.paged import FilterInput, PagedList, row

UNKNOWN_LABEL = "?"


class AdrPicker(Vertical):
    class Chosen(Message):
        """A decision was chosen; `decision` is as explore reports it."""

        def __init__(self, decision):
            super().__init__()
            self.decision = decision

    DEFAULT_CSS = """
    AdrPicker { height: auto; }
    AdrPicker > Horizontal { height: auto; }
    AdrPicker > Horizontal > Label { padding: 1 1; }
    """

    def __init__(self, field, id):
        super().__init__(id=id)
        self._field = field
        self._decisions = []
        self._labels = {}
        self.selected = None  # the chosen decision, as explore reports it

    @property
    def value(self):
        return self.selected["path"] if self.selected else ""

    def compose(self):
        texts = self.app.texts
        yield FilterInput(f"{self.id}-options", placeholder=texts("picker.filter"), id=f"{self.id}-filter")
        with Horizontal():
            yield Switch(value=True, id=f"{self.id}-only-available")
            yield Label(texts("picker.only_available"))
        yield PagedList(list_id=f"{self.id}-options", page_id=f"{self.id}-page")
        yield Static("", id=f"{self.id}-filter-note", classes="info", markup=False)
        yield Static("", id=f"{self.id}-selected", classes="info", markup=False)

    def focus(self, scroll_visible=True):
        self.query_one(OptionList).focus(scroll_visible)
        return self

    def set_decisions(self, decisions, labels):
        self._decisions = sorted(decisions, key=lambda decision: decision["filename"])
        self._labels = labels
        self._show()

    def _show(self):
        options = self.query_one(OptionList)
        options.clear_options()
        folded = self.query_one(Input).value.casefold()
        only_available = self.query_one(Switch).value
        for index, decision in enumerate(self._decisions):
            decision_state = state(decision)
            eligible = decision_state in self._field.eligible
            if folded not in decision["filename"].casefold() or (only_available and not eligible):
                continue
            label = self._labels.get(decision_state, UNKNOWN_LABEL)
            options.add_option(row(f"{visible(decision['filename'])}  ·  {label}", id=str(index),
                                   disabled=not eligible))
        if options.option_count:
            # On the first row, so the page shown is page 1: with no row
            # highlighted, PgDn would jump to the last one.
            options.highlighted = 0
        self._show_page()

    def _show_page(self):
        paged = self.query_one(PagedList)
        paged.empty_text = self.app.texts("picker.none" if self._decisions else "picker.empty")
        paged.update_page()
        self._show_filter_note()

    def _show_filter_note(self):
        """Says what the list leaves out, and the key that shows it."""
        texts = self.app.texts
        key = keys.display(self.app.key_of("toggle"), texts)
        shown, total = self.query_one(OptionList).option_count, len(self._decisions)
        if not total:
            note = ""
        elif self.query_one(Switch).value:
            note = texts("picker.count_available", shown=shown, total=total, key=key)
        else:
            note = texts("picker.count_all", total=total, key=key)
        self.query_one(f"#{self.id}-filter-note", Static).update(note)

    def toggle_available(self):
        switch = self.query_one(Switch)
        switch.value = not switch.value

    def highlighted_path(self):
        """The path of the decision the cursor is on, for its preview."""
        options = self.query_one(OptionList)
        if options.highlighted is None or not options.option_count:
            return None
        return self._decisions[int(options.get_option_at_index(options.highlighted).id)]["path"]

    def show_failure(self, detail):
        """explore could not list the decisions: says why, in adrpy's words."""
        paged = self.query_one(PagedList)
        paged.empty_text = self.app.texts("picker.failed", detail=detail)
        paged.update_page()

    def on_input_changed(self, event):
        # The filter is not one of the form's values.
        event.stop()
        self._show()

    def on_input_submitted(self, event):
        event.stop()
        self.focus()

    def on_switch_changed(self, event):
        event.stop()
        self._show()

    def on_option_list_option_highlighted(self, event):
        event.stop()  # PagedList already showed the page

    def choose(self, path):
        """Chooses the decision at `path`, as if picked from the list (a
        decision's detail opens a form with it)."""
        for decision in self._decisions:
            if decision["path"] == path:
                self._chose(decision)
                return

    def on_option_list_option_selected(self, event):
        event.stop()
        self._chose(self._decisions[int(event.option.id)])

    def _chose(self, decision):
        self.selected = decision
        self.query_one(f"#{self.id}-selected", Static).update(
            self.app.texts("picker.selected", file=visible(self.selected["filename"]))
        )
        self.screen.query_one(f"#problem-{self._field.flag}", Static).update("")
        self.post_message(self.Chosen(self.selected))
        self.screen.focus_next()
