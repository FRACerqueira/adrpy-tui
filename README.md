<img src="https://raw.githubusercontent.com/FRACerqueira/adrpy-tui/main/src/adrpy_tui/icon.png" width="160" alt="adrpy-tui icon">

# adrpy-tui

[![CI](https://github.com/FRACerqueira/adrpy-tui/actions/workflows/ci.yml/badge.svg)](https://github.com/FRACerqueira/adrpy-tui/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/FRACerqueira/adrpy-tui/blob/main/LICENSE)

**A rich terminal interface for [adrpy-ai](https://github.com/FRACerqueira/adrpy-ai): guided, human-friendly management of Architecture Decision Records.**

adrpy-tui puts menus, forms, lists and previews on top of adrpy-ai, the JSON-only ADR lifecycle CLI. Installing adrpy-tui installs adrpy-ai with it (the 0.1 series), so one install gives you both: the screens to work in, and the `adrpy` command they drive. Every change still goes through adrpy -- the interface shows you the exact command before it runs, and adrpy's rules are the only ones that apply.

## Table of Contents

- [adrpy-ai and adrpy-tui](#adrpy-ai-and-adrpy-tui)
- [Versions and compatibility](#versions-and-compatibility)
- [Installation](#installation)
- [Quick start](#quick-start)
- [What you can do](#what-you-can-do)
- [Keys](#keys)
- [Appearance and accessibility](#appearance-and-accessibility)
- [Where adrpy-tui keeps its settings](#where-adrpy-tui-keeps-its-settings)
- [Documentation](#documentation)
- [Contributing, security and license](#contributing-security-and-license)

## adrpy-ai and adrpy-tui

They are two packages by the same author, with one clear split:

| | adrpy-ai | adrpy-tui |
|---|---|---|
| What it is | The ADR lifecycle CLI: `adrpy` and `adrpy-skills` | A terminal UI built with [Textual](https://textual.textualize.io/) |
| Who it is for | Scripts, CI and AI coding agents -- flags in, JSON out, no prompts | People who would rather choose from a list than type flags |
| The rules (numbering, statuses, headers, supersede chains) | Defines and enforces them | Never reimplements one; it asks adrpy |
| Writes decision, config and decision-log files | Yes | Never -- it runs an `adrpy` command, shown to you first ([ADR001V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md)) |
| Runtime dependencies | None | adrpy-ai and Textual |

adrpy-tui runs the adrpy installed next to it, through its own Python interpreter (`python -m adrpy`), never whichever `adrpy` comes first on `PATH` ([ADR003V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md)). A repository managed with adrpy-tui is an ordinary adrpy repository: you can switch between the two, or use both, at any time.

## Versions and compatibility

Each adrpy-tui is validated against one series of adrpy-ai, and requires it:

| adrpy-tui | adrpy-ai it requires |
|---|---|
| current (`develop`, not released yet) | `>=0.1.dev0,<0.2` -- the 0.1 series, development builds included |

- **At install time**, pip installs an adrpy-ai in that range, or refuses one outside it.
- **If adrpy-ai is upgraded or downgraded later, on its own** (`pip install -U adrpy-ai`), pip installs it anyway: it prints a dependency conflict ("ERROR: pip's dependency resolver ... adrpy-tui requires adrpy-ai<0.2,>=0.1.dev0, but you have adrpy-ai 0.2.0") and still finishes successfully. adrpy-tui notices at start-up: the main menu names the adrpy-ai found and the range expected. It keeps working, but a command whose flags changed may be refused by adrpy, and that refusal is shown as adrpy gives it. Install an adrpy-ai in the range again (`pip install "adrpy-ai>=0.1.dev0,<0.2"`), or an adrpy-tui validated with the newer series.
- **The header** shows both versions, and `adrpy-tui --version` prints them.

The range moves one series at a time, when adrpy-tui is validated against the next adrpy-ai: its forms are checked against adrpy's own `help` by the tests ([ADR004V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR004V01R01-forms-come-from-hand-written-per-command-specs-guarded-by-drift-and-coverage-tests-against-adrpy-help.md)).

## Installation

Requires Python 3.11 or later, on Windows, macOS or Linux.

**Not on PyPI yet.** adrpy-ai is not on PyPI either, and adrpy-tui is not published until it is (ADR003V01). Until then, install adrpy-ai from git, then adrpy-tui from a clone of this repository:

```bash
pip install git+https://github.com/FRACerqueira/adrpy-ai.git@develop
git clone https://github.com/FRACerqueira/adrpy-tui.git
pip install ./adrpy-tui
```

Once both are published, `pip install adrpy-tui` will be the only step.

## Quick start

```bash
adrpy-tui                 # the repository in the current folder
adrpy-tui --path <repo>   # another repository
adrpy-tui --version       # the installed adrpy-tui and adrpy-ai
```

1. **The first run asks for the interface language** -- one of the eleven adrpy supports, your system's preselected. The main menu's **Language** changes it later. Messages that come from adrpy itself (why a command failed, a command's help) are shown as adrpy sends them, in English ([ADR005V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR005V01R01-the-ui-is-localized-in-adrpy%27s-languages-through-json-language-packs,-chosen-on-first-run,-while-adrpy%27s-own-responses-stay-in-english.md)).
2. **The main menu** lists everything by use. In a folder that is not an ADR repository yet, choose **Repository → Initialize**; the other groups come alive once it is.
3. **A form** asks only for what its command needs, suggests values the repository already uses, and checks what it can before running. **Ctrl+R** runs it: a confirmation shows the exact `adrpy` command line; nothing runs until you confirm.
4. **The result** shows what adrpy did, its warnings, or why it refused -- with a hint to repair it when adrpy gives one.

## What you can do

```
Main menu
├─ Decisions             New decision · Approve · Reject · Undo status · New version · New revision · Supersede
├─ Explore and validate  Explore (every decision → its detail and the actions its state allows) · Check
├─ Decision log          New entry · Browse the entries
├─ Repository            Initialize · Configuration · Migrate (a guided builder for hand-written files)
├─ Install config        the per-user default configuration
├─ AI skills             List · Install · Remove (adrpy-skills)
├─ Command help          the full contract of every adrpy and adrpy-skills command
├─ Change repository
├─ Language · Appearance · Keys
└─ Exit
```

- **Choosing a decision** is picking it from a list, filtered by name, showing only the ones the command can take (F2 shows them all).
- **Every list** shows eight rows a page, with where you are when there are more.
- **Any decision or log entry** can be read rendered from any list of them (F3), following its links to other decisions.

Every screen, form and component is described in [Screens and forms](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/forms.md).

## Keys

| Key | Does |
|---|---|
| ↑ ↓, PgUp PgDn, Home End | Move in a list (also from its filter) |
| Enter | Choose |
| Tab / Shift+Tab | Next / previous field |
| → | Accept a suggestion in a field |
| Esc | Back one level; on the main menu, leave |
| **Ctrl+R** | Run the screen's action: a form, saving a configuration, migrate, using a folder |
| **F3** | Preview the decision or log entry under the cursor |
| **F2** | In the decision picker, show every decision or only the available ones |

The three in bold can be changed in the main menu's **Keys**. The line at the bottom of every screen always names the keys that work there.

## Appearance and accessibility

- **Three presets**, in the main menu's **Appearance**: Default (dark), Light and High contrast, previewed as you move through them. Any color can be customized on top of the chosen preset.
- **Every text meets WCAG AA contrast** (4.5:1), and every state indicator and the focus border WCAG's 3:1, in every preset -- measured by the tests on everything each screen draws.
- **Keyboard first**: every screen opens with the keys acting where they should -- a list's arrows, a form's first field. The mouse works too.
- `NO_COLOR` is honored.

## Where adrpy-tui keeps its settings

adrpy-tui writes one file of its own, never in your repositories: the language, the appearance and customized colors, the changed keys and the last item chosen in each menu.

| System | File |
|---|---|
| Windows | `%APPDATA%\adrpy-tui\state.json` |
| macOS, Linux | `$XDG_STATE_HOME/adrpy-tui/state.json`, or `~/.local/state/adrpy-tui/state.json` |

Deleting it starts again from the language choice.

## Documentation

| Page | For | What it covers |
|---|---|---|
| [Screens and forms](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/forms.md) | Everyone | The header, menus, lists, focus, keys, previews, colors, and every command's form |
| [Architecture](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/architecture.md) | Contributors | Why it exists, its boundaries, how adrpy is run and version-checked, the module map, testing |
| [Manual test checklist](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/manual-test-checklist.md) | Maintainers | What to walk through in a real terminal before a release |
| [Architecture decisions](https://github.com/FRACerqueira/adrpy-tui/tree/main/doc/adr/) | Contributors | The recorded decisions, written with adrpy itself (list below) |
| [Contributing](https://github.com/FRACerqueira/adrpy-tui/blob/main/CONTRIBUTING.md) | Contributors | Development setup, tests, translations, pull requests |
| [Changelog](https://github.com/FRACerqueira/adrpy-tui/blob/main/CHANGELOG.md) | Everyone | What changed |

The decisions:

- [ADR001V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md) -- Every read and change goes through the adrpy CLI as a subprocess, and the TUI decides on the JSON code and data only
- [ADR002V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR002V01R01-textual-is-the-tui-framework,-a-deliberate-runtime-dependency-unlike-adrpy-ai.md) -- Textual is the TUI framework, a deliberate runtime dependency unlike adrpy-ai
- [ADR003V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md) -- adrpy-ai is a declared dependency run through the TUI's own interpreter, and adrpy-tui is not published until adrpy-ai is on PyPI
- [ADR004V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR004V01R01-forms-come-from-hand-written-per-command-specs-guarded-by-drift-and-coverage-tests-against-adrpy-help.md) -- Forms come from hand-written per-command specs guarded by drift and coverage tests against adrpy help
- [ADR005V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR005V01R01-the-ui-is-localized-in-adrpy%27s-languages-through-json-language-packs,-chosen-on-first-run,-while-adrpy%27s-own-responses-stay-in-english.md) -- The UI is localized in adrpy's languages through JSON language packs, chosen on first run, while adrpy's own responses stay in English

## Contributing, security and license

- Contributions are welcome -- read [CONTRIBUTING.md](https://github.com/FRACerqueira/adrpy-tui/blob/main/CONTRIBUTING.md) first. The interface's translations beyond English have not been reviewed by native speakers yet; reviews are very welcome.
- Report a vulnerability privately, as [SECURITY.md](https://github.com/FRACerqueira/adrpy-tui/blob/main/SECURITY.md) explains. Vulnerabilities in adrpy itself belong to [adrpy-ai](https://github.com/FRACerqueira/adrpy-ai/security).
- This project follows its [Code of Conduct](https://github.com/FRACerqueira/adrpy-tui/blob/main/CODE_OF_CONDUCT.md).
- MIT licensed -- see [LICENSE](https://github.com/FRACerqueira/adrpy-tui/blob/main/LICENSE).
