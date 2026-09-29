<!-- Do not remove this comment, lines and table (1-12) -->
|Fields|Values|
|--|--|
|File title md|Textual is the TUI framework, a deliberate runtime dependency unlike adrpy-ai|
|Version|01|
|Revision|01|
|Scope|ui|
|Domain|dependencies|
|Created|Proposed (2026-09-28) <!-- Proposed -->|
|Changed|Accepted (2026-09-28) <!-- Accepted -->|
|Superseded||
<!-- Do not remove this comment, lines and table (1-12) -->
---
# Textual is the TUI framework, a deliberate runtime dependency unlike adrpy-ai

## Deciders

* Deciders: Fernando Cerqueira (repo owner), decided while designing adrpy-tui's architecture.

Technical Story: adrpy-tui needs menus, forms, tables, a file tree and modals, on Windows, macOS and Linux.

## Context and Problem Statement

adrpy-ai has zero runtime dependencies by design, and a pull request adding one there is treated as a significant decision. adrpy-tui is a separate distribution with a different job: an interactive UI. The standard library's `curses` is not available on Windows CPython, and building menus, forms, tables and a file tree on raw terminal I/O is a large amount of code to own.

Does adrpy-tui follow adrpy-ai's zero-dependency rule, or take a TUI framework?

## Decision Drivers

* Windows is a first-class platform (the maintainer's own, and in adrpy-ai's CI matrix).
* The forms need a select list, a filterable list, a table, a directory tree, a multi-line editor, a switch, a masked input and modals.
* The same test discipline as adrpy-ai: the UI must be drivable from pytest.
* Supply-chain surface should stay small.

## Considered Options

* Standard library only (`curses` or raw terminal I/O).
* prompt_toolkit.
* Textual.

## Decision Outcome

Chosen option: "Textual", because it ships every widget the forms need (`OptionList`, `Select`, `SelectionList`, `DataTable`, `DirectoryTree`, `TextArea`, `Switch`, `MaskedInput`, `MarkdownViewer`, modal screens), runs on Windows, and has a headless test driver (`App.run_test()`).

1. `textual` is adrpy-tui's runtime dependency besides `adrpy-ai`. This deliberately differs from adrpy-ai's zero-dependency rule, which is scoped to adrpy-ai and is unaffected.
2. Screens are built from Textual's own widgets. Composites of them (a decision picker, a suggester, the banner header) are covered by this decision. Where Textual has no ready-made component (a calendar, a slider, a suggestion list), the closest core widget is used (`MaskedInput`, a `Select` over the range, a single inline suggestion) until the experience is validated. A widget drawn from scratch, or a further dependency (such as textual-autocomplete), is a new decision, not implied by this one.

### Positive Consequences

* One cross-platform framework covers every screen, including Windows.
* UI tests run headless in pytest.
* Colors are CSS values, so the palette in `doc/forms.md` maps directly.

### Negative Consequences

* A runtime dependency with its own transitive dependencies (Rich and others), and a supply-chain surface adrpy-ai does not have.
* Textual's API has changed across major versions; upgrades need attention.
* A calendar, a slider and a suggestion list are approximated with core widgets until validated.

## Pros and Cons of the Options

### Standard library only

* Good, because it adds no dependency.
* Bad, because `curses` is missing on Windows CPython.
* Bad, because every widget would be built and maintained here.

### prompt_toolkit

* Good, because it is mature and cross-platform, with strong input and completion.
* Bad, because full-screen layouts with tables, trees and modals take considerably more code than in Textual.

### Textual

* Good, because it has all the needed widgets, CSS styling and a test driver.
* Bad, because it is a heavier dependency with a fast-moving API.

## Links

* Contrasts with adrpy-ai's zero-dependency principle (adrpy-ai `CONTRIBUTING.md`, "Development Setup").
* Relates to [`doc/forms.md`](../forms.md) -- the component mapping.
