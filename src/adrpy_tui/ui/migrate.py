"""`migrate`: a guided builder of the legacy naming pattern. The files to
migrate; on a sample name, the position and length of each part, each
showing what it reads; a preview of what adrpy reads from every file; then
`config --migrationpattern` and `migrate`, the second only once the first
succeeded."""

from pathlib import Path

from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, LoadingIndicator, Select, Static, Switch

from adrpy_tui.core.text import printable, visible
from adrpy_tui.core import keys
from adrpy_tui.core.decisions import listed, repository_config, setting
from adrpy_tui.core.files import inside_repository, markdown_files
from adrpy_tui.core.migration import PARTS, REQUIRED, Part, build, parse, propose, read
from adrpy_tui.ui.base import AdrpyScreen, on_top
from adrpy_tui.ui.paged import PagedList, row
from adrpy_tui.ui.preview import PREVIEW_BINDING, open_preview
from adrpy_tui.ui.running import CommandRunner


class MigrateScreen(CommandRunner, AdrpyScreen):
    HINTS = (("tab", "next"), ("enter", "choose"), ("@preview", "preview"), ("@run", "migrate"), ("escape", "back"))
    BINDINGS = [
        Binding("escape", "back", show=False),
        Binding(keys.ACTIONS["run"], "migrate", id=keys.binding_id("run"), show=False),
        PREVIEW_BINDING,
    ]
    DEFAULT_CSS = """
    MigrateScreen .part { height: auto; }
    MigrateScreen .part > Label { width: 12; padding: 1 1; }
    MigrateScreen .part > Select { width: 16; }
    MigrateScreen .part > Static { padding: 1 1; }
    """

    def __init__(self):
        super().__init__("migrate")
        self._files = []
        self._sample = ""
        self._current = ""  # the repository's own migrationpattern

    def compose_body(self):
        yield LoadingIndicator()

    def on_mount(self):
        def work(app):
            path = ("--path", str(app.repo))
            return app.client.run("config", path), app.client.run("explore", path)

        self.read(work, lambda both: self._show(*both))

    async def _show(self, config, explore):
        if not self.is_attached:
            return
        try:
            await self._mount_builder(config, explore)
        finally:
            self.focus_first()

    async def _mount_builder(self, config, explore):
        texts, body = self.app.texts, self.query_one("#body")
        await body.remove_children()
        await body.mount(Static(texts("form.migrate"), classes="title"))
        failed = next((result for result in (config, explore) if not result.success), None)
        if failed:
            await body.mount(Static(visible(failed.detail or failed.code or ""), classes="error", markup=False))
            return
        settings = repository_config(config.data)
        self._current = setting(settings, "migrationpattern", "")
        folder = self.app.repo / setting(settings, "folderadr", "doc/adr")
        if not inside_repository(self.app.repo, folder):
            await body.mount(Static(texts("preview.outside", path=visible(setting(settings, "folderadr", ""))),
                                    classes="error", markup=False))
            return
        with_header = {d["path"] for d in listed(explore.data) if d["header"]["is_valid"]}
        # INDEX.md is the page adrpy generates in the decisions folder (adrpy-ai ADR0013V01R01).
        self._files = [p for p in markdown_files(folder, recursive=False)
                       if str(p) not in with_header and p.name != "INDEX.md"]
        if not self._files:
            await body.mount(Static(texts("migrate.none", folder=visible(str(folder))), classes="info", markup=False))
            return
        await body.mount(Static(texts("migrate.files"), classes="title"))
        await body.mount(PagedList(*(row(visible(p.name), id=str(i)) for i, p in enumerate(self._files)),
                                   list_id="files"))
        await body.mount(Static("", id="sample", classes="info", markup=False))
        await body.mount_all(self._part_rows())
        await body.mount(Static("", id="pattern", classes="summary", markup=False))
        await body.mount(Button(texts("migrate.preview"), id="preview"))
        await body.mount(Vertical(id="preview-area"))
        await body.mount(Button(texts("migrate.run"), id="migrate", variant="primary"))
        self._use_sample(printable(self._files[0].stem), parse(self._current))

    def _part_rows(self):
        texts = self.app.texts
        for name in PARTS:
            widgets = [Label(texts(f"migrate.part.{name}"))]
            if name not in REQUIRED:
                widgets.append(Switch(id=f"use-{name}"))
            # A first option until the sample name gives them all (a Select
            # that cannot be blank cannot be empty either).
            widgets.append(Select([("00", 0)], prompt=texts("migrate.start"), allow_blank=False, id=f"start-{name}"))
            if name != "T":
                widgets.append(Select([("01", 1)], prompt=texts("migrate.length"), allow_blank=False,
                                      id=f"length-{name}"))
            widgets.append(Static("", id=f"reads-{name}", markup=False))
            yield Horizontal(*widgets, classes="part", id=f"part-{name}")

    def _use_sample(self, stem, parts=None):
        """Offers every position of `stem`, and starts from `parts` (the
        repository's own pattern) or a proposal read from the name."""
        self._sample = stem
        self.query_one("#sample", Static).update(self.app.texts("migrate.sample", name=visible(stem)))
        parts = parts or propose(stem)
        positions = [(f"{i:02}", i) for i in range(len(stem))] or [("00", 0)]
        lengths = [(f"{i:02}", i) for i in range(1, len(stem) + 1)] or [("01", 1)]
        self._updating = True
        for name in PARTS:
            part = parts.get(name)
            if name not in REQUIRED:
                self.query_one(f"#use-{name}", Switch).value = part is not None
            start = self.query_one(f"#start-{name}", Select)
            start.set_options(positions)
            start.value = min(part.start, len(stem) - 1) if part else 0
            if name != "T":
                length = self.query_one(f"#length-{name}", Select)
                length.set_options(lengths)
                length.value = min(part.length, len(stem)) if part else 1
        self._updating = False
        self._refresh()

    def _parts(self):
        parts = {}
        for name in PARTS:
            if name not in REQUIRED and not self.query_one(f"#use-{name}", Switch).value:
                continue
            start = self.query_one(f"#start-{name}", Select).value
            length = None if name == "T" else self.query_one(f"#length-{name}", Select).value
            parts[name] = Part(start, length)
        return parts

    def pattern(self):
        return build(self._parts())

    def _refresh(self):
        if not self.is_open():  # a change delivered after the screen was left
            return
        parts = self._parts()
        for name in PARTS:
            text = self.app.texts("migrate.reads", text=read(self._sample, parts[name])) if name in parts else ""
            self.query_one(f"#reads-{name}", Static).update(visible(text))
        self.query_one("#pattern", Static).update(self.app.texts("migrate.pattern", pattern=self.pattern()))
        self.query_one("#preview-area").remove_children()

    def on_select_changed(self, event):
        if not getattr(self, "_updating", False):
            self._refresh()

    def on_switch_changed(self, event):
        if not getattr(self, "_updating", False):
            self._refresh()

    def on_option_list_option_selected(self, event):
        if not on_top(self):
            return
        if event.option_list.id != "files":  # a row of the preview, not a file
            return
        self._use_sample(printable(self._files[int(event.option.id)].stem), self._parts())

    def on_button_pressed(self, event):
        if not on_top(self):
            return
        if event.button.id == "preview":
            pattern = self.pattern()
            self.read(lambda app: (pattern, app.client.run(
                "explore", ("--path", str(app.repo), "--migrationpattern", pattern))), lambda both: self._show_preview(*both))
        elif event.button.id == "migrate":
            self.action_migrate()

    async def _show_preview(self, pattern, result):
        if pattern != self.pattern():  # changed while adrpy read it: this preview is not of it
            return
        area = self.query_one("#preview-area")
        await area.remove_children()
        if not result.success:
            await area.mount(Static(visible(result.detail or result.code or ""), classes="error", markup=False))
            return
        rows = result.data.get("migrationpattern_preview") or []
        await area.mount(PagedList(*(row(self._preview_row(entry), id=str(i)) for i, entry in enumerate(rows)),
                                   list_id="preview-options"))
        for warning in result.warnings:
            await area.mount(Static(visible(str(warning)), classes="warning", markup=False))

    @staticmethod
    def _preview_row(entry):
        name = Path(str(entry.get("file", "")).replace("\\", "/")).name
        return visible(f"{name}  ·  N {entry.get('number')}  ·  V {entry.get('version')}  ·  {entry.get('title')}")

    def _commands(self):
        path = ("--path", str(self.app.repo))
        pattern = self.pattern()
        commands = [] if pattern == self._current else [("config", (*path, "--migrationpattern", pattern))]
        return commands + [("migrate", path)]

    def action_migrate(self):
        if not self._files:
            return
        # Stops at the first that fails: migrate never runs on a pattern
        # that was not saved.
        self.confirm_and_run(self._commands())

    def action_preview(self):
        if self.command_running:
            return
        files = self.query("#files")
        if files and files.first().highlighted is not None:
            options = files.first()
            open_preview(self.app, self._files[int(options.get_option_at_index(options.highlighted).id)])

    def action_back(self):
        if not self.command_running:
            self.app.pop_screen()
