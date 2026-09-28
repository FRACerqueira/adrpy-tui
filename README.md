<img src="https://raw.githubusercontent.com/FRACerqueira/adrpy-tui/main/src/adrpy_tui/icon.png" width="160" alt="adrpy-tui icon">

# adrpy-tui

Interactive terminal UI for adrpy -- guided, human-friendly ADR management that runs every change through the adrpy CLI.

## Installation

Not on PyPI yet: adrpy-tui depends on [adrpy-ai](https://github.com/FRACerqueira/adrpy-ai), which is not on PyPI either, so adrpy-tui is not published until it is (see [ADR003V01](doc/adr/ADR003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md)). Install adrpy-ai from git first, then adrpy-tui from a clone of this repository:

```bash
pip install git+https://github.com/FRACerqueira/adrpy-ai.git@develop
pip install .
```

## Usage

```bash
adrpy-tui                 # the repository in the current folder
adrpy-tui --path <repo>   # another repository
adrpy-tui --version
```

The first run asks for the interface language, one of the eleven adrpy supports; the main menu's **Language** item changes it later. Messages that come from adrpy itself -- the explanation of a failure, the command help -- are shown as adrpy sends them, in English ([ADR005V01](doc/adr/ADR005V01R01-the-ui-is-localized-in-adrpy%27s-languages-through-json-language-packs,-chosen-on-first-run,-while-adrpy%27s-own-responses-stay-in-english.md)).

Every change runs an adrpy command, shown on a confirmation screen before it runs. See [`doc/architecture.md`](doc/architecture.md) and [`doc/forms.md`](doc/forms.md).

## Documentation

- [`doc/architecture.md`](doc/architecture.md) -- how adrpy-tui is put together and why: its boundaries, how adrpy is run, the module map, languages, testing.
- [`doc/forms.md`](doc/forms.md) -- every screen and form: the header, colors, lists, focus, keys, previews, the widget for each kind of input.
- [`doc/manual-test-checklist.md`](doc/manual-test-checklist.md) -- what to walk through in a real terminal before a release.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) -- development setup, tests, translations.
- [`CHANGELOG.md`](CHANGELOG.md) -- what changed.
- The recorded decisions, in [`doc/adr/`](doc/adr/):
  - [ADR001V01R01](doc/adr/ADR001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md) -- Every read and change goes through the adrpy CLI as a subprocess, and the TUI decides on the JSON code and data only
  - [ADR002V01R01](doc/adr/ADR002V01R01-textual-is-the-tui-framework,-a-deliberate-runtime-dependency-unlike-adrpy-ai.md) -- Textual is the TUI framework, a deliberate runtime dependency unlike adrpy-ai
  - [ADR003V01R01](doc/adr/ADR003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md) -- adrpy-ai is a declared dependency run through the TUI's own interpreter, and adrpy-tui is not published until adrpy-ai is on PyPI
  - [ADR004V01R01](doc/adr/ADR004V01R01-forms-come-from-hand-written-per-command-specs-guarded-by-drift-and-coverage-tests-against-adrpy-help.md) -- Forms come from hand-written per-command specs guarded by drift and coverage tests against adrpy help
  - [ADR005V01R01](doc/adr/ADR005V01R01-the-ui-is-localized-in-adrpy%27s-languages-through-json-language-packs,-chosen-on-first-run,-while-adrpy%27s-own-responses-stay-in-english.md) -- The UI is localized in adrpy's languages through JSON language packs, chosen on first run, while adrpy's own responses stay in English
