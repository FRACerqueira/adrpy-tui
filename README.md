<img src="https://raw.githubusercontent.com/FRACerqueira/adrpy-tui/main/src/adrpy_tui/icon.png" width="160" alt="adrpy-tui icon">

# adrpy-tui

[![CI](https://github.com/FRACerqueira/adrpy-tui/actions/workflows/ci.yml/badge.svg)](https://github.com/FRACerqueira/adrpy-tui/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/adrpy-tui)](https://pypi.org/project/adrpy-tui/)
[![Downloads](https://static.pepy.tech/badge/adrpy-tui)](https://pepy.tech/projects/adrpy-tui)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/FRACerqueira/adrpy-tui/blob/main/LICENSE)

**A rich terminal interface for [adrpy-ai](https://github.com/FRACerqueira/adrpy-ai): guided, human-friendly management of Architecture Decision Records.**

adrpy-tui puts menus, forms, lists and previews on top of adrpy-ai, the JSON-only ADR lifecycle CLI. Installing adrpy-tui with pip installs adrpy-ai with it (the 0.1 series), so one install gives you both: the screens to work in, and the `adrpy` command they drive. Every change still goes through adrpy -- the interface shows you the exact command before it runs, and adrpy's rules are the only ones that apply.

![A first run of adrpy-tui: choosing the language, initializing a repository, creating a decision, approving it and opening it in Explore](https://raw.githubusercontent.com/FRACerqueira/adrpy-tui/main/doc/images/adrpy-tui-first-run.gif)

*A first run: the language, Repository → Initialize, a new decision, Approve, then Explore.*

## Table of Contents

- [Motivation and Benefits](#motivation-and-benefits)
- [adrpy-ai and adrpy-tui](#adrpy-ai-and-adrpy-tui)
- [Versions and compatibility](#versions-and-compatibility)
- [Installation](#installation)
- [Terminal requirements](#terminal-requirements)
- [Quick start](#quick-start)
- [Features](#features)
- [Keys](#keys)
- [Appearance and accessibility](#appearance-and-accessibility)
- [Where adrpy-tui keeps its settings](#where-adrpy-tui-keeps-its-settings)
- [Documentation](#documentation)
- [Contributing, security and license](#contributing-security-and-license)

## Motivation and Benefits

- **The whole ADR lifecycle without memorizing a flag.** Every adrpy and adrpy-skills command has its screen: menus by use, forms that ask only for what the command needs, and a decision picked from a list.
- **Nothing runs behind your back.** The confirmation shows the exact `adrpy` command line before it runs, and adrpy's own rules are the only ones that apply -- the interface never writes a file itself.
- **Mistakes caught before running.** A form checks what it can, suggests the values the repository already uses, and offers a decision only to the commands its state allows.
- **Read before you decide.** Any decision or log entry opens rendered, from every list of them, following its links to the others.
- **Accessible and in your language.** Every screen meets WCAG contrast in the Default, Light and High contrast presets, keys can be changed, and the interface speaks the eleven languages adrpy supports.

## adrpy-ai and adrpy-tui

They are two packages by the same author, with one clear split:

| | adrpy-ai | adrpy-tui |
|---|---|---|
| What it is | The ADR lifecycle CLI: `adrpy` and `adrpy-skills` | A terminal UI built with [Textual](https://textual.textualize.io/) |
| Who it is for | Scripts, CI and AI coding agents -- flags in, JSON out, no prompts | People who would rather choose from a list than type flags |
| The rules (numbering, statuses, headers, supersede chains) | Defines and enforces them | Never reimplements one; it asks adrpy |
| Writes decision, config and decision-log files | Yes | Never -- it runs an `adrpy` command, shown to you first ([ADR0001V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR0001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md)) |
| Runtime dependencies | None | adrpy-ai and Textual |

adrpy-tui runs the adrpy installed next to it, through its own Python interpreter (`python -m adrpy`), never whichever `adrpy` comes first on `PATH` ([ADR0003V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR0003V01R02-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md)). A repository managed with adrpy-tui is an ordinary adrpy repository: you can switch between the two, or use both, at any time.

## Versions and compatibility

Each adrpy-tui is validated against one series of adrpy-ai, and requires it:

| adrpy-tui | adrpy-ai it requires |
|---|---|
| 0.1.x | `>=0.1.dev0,<0.2` -- the 0.1 series, development builds included |

- **At install time**, pip installs an adrpy-ai in that range, or refuses one outside it.
- **If adrpy-ai is upgraded or downgraded later, on its own** (`pip install -U adrpy-ai`), pip installs it anyway: it prints a dependency conflict ("ERROR: pip's dependency resolver ... adrpy-tui requires adrpy-ai<0.2,>=0.1.dev0, but you have adrpy-ai 0.2.0") and still finishes successfully. adrpy-tui notices at start-up: the main menu names the adrpy-ai found and the range expected. It keeps working, but a command whose flags changed may be refused by adrpy, and that refusal is shown as adrpy gives it. Install an adrpy-ai in the range again (`pip install "adrpy-ai>=0.1.dev0,<0.2"`), or an adrpy-tui validated with the newer series.
- **The header** shows both versions, and `adrpy-tui --version` prints them.

The range moves one series at a time, when adrpy-tui is validated against the next adrpy-ai: its forms are checked against adrpy's own `help` by the tests ([ADR0004V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR0004V01R01-forms-come-from-hand-written-per-command-specs-guarded-by-drift-and-coverage-tests-against-adrpy-help.md)).

## Installation

Requires Python 3.11 or later, on Windows, macOS or Linux.

```bash
pip install adrpy-tui
adrpy-tui
```

It installs adrpy-ai with it (see [Versions and compatibility](#versions-and-compatibility)), so the same environment also has adrpy-ai's `adrpy` and `adrpy-skills` commands. As a command-line tool in its own environment, with [pipx](https://pipx.pypa.io/): `pipx install adrpy-tui` -- pipx puts only `adrpy-tui` on your PATH (the interface runs its own adrpy either way); for the `adrpy` command as well, also run `pipx install adrpy-ai`. Straight from GitHub, a branch or a commit, without cloning: `pip install git+https://github.com/FRACerqueira/adrpy-tui.git`.

Whether `adrpy-tui` then runs from any folder depends on where it was installed. Into a Python whose `Scripts` folder (Windows) or `bin` folder (macOS, Linux) is on your PATH, it does. With `pip install --user`, that folder is often not on PATH, and pip says so ("... which is not on PATH"): add the folder it names to PATH. Into a virtual environment, only while that environment is activated. pipx puts its commands on PATH; if it warns that its folder is not, run `pipx ensurepath` once and open a new terminal. To check, run `where adrpy-tui` on Windows (`where.exe adrpy-tui` in PowerShell) or `command -v adrpy-tui` on macOS and Linux. Run from any folder, `adrpy-tui` opens the repository in that folder (see [Quick start](#quick-start)).

adrpy-ai's package is `adrpy-ai`; `ADRpy` on PyPI is an unrelated project. Don't install it in the same environment as adrpy-tui: on Windows and macOS their import folders (`adrpy` and `ADRpy`) are the same folder, and their files mix.

To install from a clone instead:

```bash
git clone https://github.com/FRACerqueira/adrpy-tui.git
cd adrpy-tui
pip install .
adrpy-tui
```

The source install needs a git clone: the version is read from git, so a folder from GitHub's "Download ZIP" does not install. On Windows, some file names under `doc/` are long; if `git clone` reports "Filename too long", clone with `git clone -c core.longpaths=true https://github.com/FRACerqueira/adrpy-tui.git`.

To work on adrpy-tui itself (running the test suite), see [Contributing](https://github.com/FRACerqueira/adrpy-tui/blob/main/CONTRIBUTING.md).

## Terminal requirements

- **About 100 columns by 40 rows, or more.** In a shorter terminal (around 33 rows), a form's list of decisions can be squeezed until none of its rows shows, so there is nothing to choose.
- **A font for the interface's languages.** The language list, and the interface once translated, show Japanese, Korean, Chinese and Russian text: a terminal whose font (or the fonts it falls back to) lacks those scripts draws them as boxes. A font family such as Noto CJK covers them.
- **When Ctrl+R runs nothing**, a required field (marked `*`) is empty or not valid: a notification names it and why ("Not run: Decision — Required."), its message shows under it, and the focus moves there. In a list, Enter moves from the filter to the list, and Enter again chooses the highlighted decision.

## Quick start

```bash
adrpy-tui                 # the repository in the current folder
adrpy-tui --path <repo>   # another repository
adrpy-tui --version       # the installed adrpy-tui and adrpy-ai
```

1. **The first run asks for the interface language** -- one of the eleven adrpy supports, your system's preselected. The main menu's **Language** changes it later. Messages that come from adrpy itself (why a command failed, a command's help) are shown as adrpy sends them, in English ([ADR0005V01](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/ADR0005V01R01-the-ui-is-localized-in-adrpy%27s-languages-through-json-language-packs,-chosen-on-first-run,-while-adrpy%27s-own-responses-stay-in-english.md)).
2. **The main menu** lists everything by use. In a folder that is not an ADR repository yet, choose **Repository → Initialize**; the other groups come alive once it is.
3. **A form** asks only for what its command needs, suggests values the repository already uses, and checks what it can before running. **Ctrl+R** runs it: a confirmation shows the exact `adrpy` command line; nothing runs until you confirm.
4. **The result** shows what adrpy did, its warnings, or why it refused -- with a hint to repair it when adrpy gives one.

## Features

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

adrpy-tui writes one file of its own, never in your repositories: the language, the appearance and customized colors, the changed keys and the last item chosen in each menu. Next to it, `error.log` holds the details of the last failure of adrpy-tui itself, if one happened.

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
| [Architecture decisions](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/adr/INDEX.md) | Contributors | Every recorded decision with its state, scope and dates, in the index adrpy regenerates at each command that writes a decision |
| [Decision log](https://github.com/FRACerqueira/adrpy-tui/blob/main/doc/decision-log/INDEX.md) | Contributors | Audit findings and other non-architectural decisions, one entry each, written with `adrpy log` |
| [Contributing](https://github.com/FRACerqueira/adrpy-tui/blob/main/CONTRIBUTING.md) | Contributors | Development setup, tests, translations, pull requests |
| [Changelog](https://github.com/FRACerqueira/adrpy-tui/blob/main/CHANGELOG.md) | Everyone | What changed |

## Contributing, security and license

- Contributions are welcome -- read [CONTRIBUTING.md](https://github.com/FRACerqueira/adrpy-tui/blob/main/CONTRIBUTING.md) first. The interface's translations beyond English have not been reviewed by native speakers yet; reviews are very welcome.
- Report a vulnerability privately, as [SECURITY.md](https://github.com/FRACerqueira/adrpy-tui/blob/main/SECURITY.md) explains. Vulnerabilities in adrpy itself belong to [adrpy-ai](https://github.com/FRACerqueira/adrpy-ai/security).
- This project follows its [Code of Conduct](https://github.com/FRACerqueira/adrpy-tui/blob/main/CODE_OF_CONDUCT.md).
- MIT licensed -- see [LICENSE](https://github.com/FRACerqueira/adrpy-tui/blob/main/LICENSE).
