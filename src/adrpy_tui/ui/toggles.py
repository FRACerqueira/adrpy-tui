"""The interface's choices: a mark says which are chosen -- [x] or [ ],
(●) or ( ) -- where Textual's draw the same X or ● either way and only
its colour changes (WCAG 1.4.1). The mark is drawn in the text's own
colour: Textual's green read below 3:1 on the highlighted row and on Light.

Both replace a private part of Textual's drawing (`render_line`'s button,
`_button`): tests/test_ui.py checks the marks, so a Textual that draws
them otherwise fails there."""

from rich.segment import Segment
from rich.style import Style
from textual.content import Content
from textual.strip import Strip
from textual.widgets import OptionList, RadioButton, SelectionList
from textual.widgets.option_list import OptionDoesNotExist


class CheckList(SelectionList):
    def _get_left_gutter_width(self):
        return len("[x] ")

    def render_line(self, y):
        line = OptionList.render_line(self, y)
        index = self.scroll_offset.y + y
        try:
            selection = self.get_option_at_index(index)
        except OptionDoesNotExist:
            return line
        # The option's index, as Textual's own button carries it: a click on the mark toggles that option.
        style = (next(iter(line)).style or self.rich_style) + Style(meta={"option": index})
        return Strip([Segment("[x] " if selection.value in self.selected else "[ ] ", style), *line])


class ChoiceButton(RadioButton):
    @property
    def _button(self):
        return Content("(●)" if self.value else "( )")
