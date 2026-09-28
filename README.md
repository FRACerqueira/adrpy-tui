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
