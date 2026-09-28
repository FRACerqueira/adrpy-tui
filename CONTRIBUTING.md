# Contributing to adrpy-tui

Thanks for considering a contribution. Read this before opening a pull request, it will save you a round trip.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [The Project's Own Verification Discipline](#the-projects-own-verification-discipline)
- [Coding Guidelines](#coding-guidelines)
- [Translations](#translations)
- [Architecture Decisions](#architecture-decisions)
- [Commit Messages](#commit-messages)
- [Submitting a Pull Request](#submitting-a-pull-request)

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). Participation implies agreement with it.

## Development Setup

Requires Python 3.11+. adrpy-ai is not on PyPI yet, so install it from git first ([ADR003V01](doc/adr/ADR003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md)):

```bash
git clone https://github.com/FRACerqueira/adrpy-tui.git
cd adrpy-tui
python -m venv .venv
.venv/bin/pip install git+https://github.com/FRACerqueira/adrpy-ai.git@develop   # .venv\Scripts\pip on Windows
.venv/bin/pip install -e ".[dev]"
.venv/bin/adrpy-tui
```

The version comes from git (hatch-vcs), so build from a git checkout.

A runtime dependency beyond `adrpy-ai` and `textual` is a significant decision ([ADR002V01](doc/adr/ADR002V01R01-textual-is-the-tui-framework,-a-deliberate-runtime-dependency-unlike-adrpy-ai.md)) — discuss it in an issue first.

## Running Tests

```bash
pytest
```

The UI tests drive the app headless through Textual's `App.run_test()`; the integration tests run the real adrpy against repositories created in a temporary folder. Some tests compare the forms and language packs with the installed adrpy's own `help` ([ADR004V01](doc/adr/ADR004V01R01-forms-come-from-hand-written-per-command-specs-guarded-by-drift-and-coverage-tests-against-adrpy-help.md)): a failure there after upgrading adrpy-ai means a form needs updating, not the test.

## The Project's Own Verification Discipline

1. **Bug fixes**: write a test that reproduces the bug, confirm it fails *for the reason you believe it does*, then fix it, and confirm the same test passes plus the rest of the suite still does.
2. **New behavior**: write the test for the new behavior before or alongside the implementation, not after.
3. **A finding that turns out not to be a bug** still becomes a permanent test with a comment explaining why the suspected failure doesn't materialize.

## Coding Guidelines

- **The CLI is the only way in.** The TUI never writes a decision, config or decision-log file itself, and decides on a response's `code` and `data`, never on `detail` ([ADR001V01](doc/adr/ADR001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md)).
- **Layers go one way**: `__main__.py` → `ui/` → `forms/` → `core/`; `core/` never imports Textual. See [`doc/architecture.md`](doc/architecture.md).
- **Simplicity first**, **surgical changes**, **match existing style**; every changed line should trace back to the request that caused it.

## Translations

Every text the TUI shows lives in `src/adrpy_tui/resources/language_packs/<language>.json` ([ADR005V01](doc/adr/ADR005V01R01-the-ui-is-localized-in-adrpy%27s-languages-through-json-language-packs,-chosen-on-first-run,-while-adrpy%27s-own-responses-stay-in-english.md)). A new text is added to `en-us.json` and to every other pack in the same change; a test fails otherwise. Reviews of the existing translations by native speakers are very welcome.

## Architecture Decisions

Architectural choices (a new dependency, a structural or cross-cutting design decision) are recorded in [`doc/adr/`](doc/adr/), written with `adrpy` itself. Please open an issue to discuss one before implementing it.

## Commit Messages

Focus on *why*, not just *what*. Reference the specific behavior or finding being addressed.

## Submitting a Pull Request

1. Fork the repository and create a branch from `develop`.
2. Make your change, following the guidelines above.
3. Run `pytest` and confirm everything passes (skips are fine, failures aren't).
4. Open a pull request against `develop`, describing what changed and why. Link any related issue.

`main` only receives releases; day-to-day work happens on `develop`.
