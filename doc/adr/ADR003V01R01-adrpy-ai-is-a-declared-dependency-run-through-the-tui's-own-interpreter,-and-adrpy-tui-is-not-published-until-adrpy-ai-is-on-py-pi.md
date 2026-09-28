<!-- Do not remove this comment, lines and table (1-12) -->
|Adr-Plus Fields|Values|
|--|--|
|File title md|adrpy-ai is a declared dependency run through the TUI's own interpreter, and adrpy-tui is not published until adrpy-ai is on PyPI|
|Version|01|
|Revision|01|
|Scope|packaging|
|Domain|dependencies|
|Created|Proposed (2026-09-28) <!-- Proposed -->|
|Changed|Accepted (2026-09-28) <!-- Accepted -->|
|Superseded||
<!-- Do not remove this comment, lines and table (1-12) -->
---
# adrpy-ai is a declared dependency run through the TUI's own interpreter, and adrpy-tui is not published until adrpy-ai is on PyPI

## Deciders

* Deciders: Fernando Cerqueira (repo owner), decided while designing adrpy-tui's architecture.

Technical Story: ADR001V01 makes the adrpy CLI the TUI's only way in; this decides how that CLI is obtained and invoked. At the time of the decision, adrpy-ai has no git tag and no PyPI release: installed from git, it reports `0.1.devN`.

## Context and Problem Statement

The TUI needs an `adrpy` whose JSON contract it was built against. It can require one on `PATH` as an external prerequisite, or declare `adrpy-ai` as a package dependency and run the copy installed next to it. PyPI rejects packages whose dependencies are direct `git+` references, and `adrpy-ai` itself is not on PyPI yet.

How does adrpy-tui obtain and invoke adrpy, and what does that mean for publishing adrpy-tui?

## Decision Drivers

* The TUI must talk to the adrpy it was installed with, not whichever `adrpy` happens to be first on `PATH`.
* Installing adrpy-tui should be enough to get a working adrpy.
* adrpy-ai is not on PyPI, and a `0.1.devN` build does not satisfy a `>=0.1.0` pin.

## Considered Options

* External prerequisite on `PATH`, found with `shutil.which` and version-checked at start-up.
* Declared dependency, run as `sys.executable -m adrpy`.
* Wait for adrpy-ai to be on PyPI before starting.

## Decision Outcome

Chosen option: "Declared dependency", because it guarantees the TUI and its adrpy live in one environment and removes a manual install step.

1. `adrpy-ai` is listed by name, with no URL and no version floor, in `dependencies`. A `git+` URL would need hatch's `allow-direct-references` and would be wrong the day adrpy-ai reaches PyPI.
2. The TUI runs `[sys.executable, "-m", "adrpy", ...]` and `[sys.executable, "-m", "adrpy.skills", ...]`, never a bare `adrpy` from `PATH`.
3. Until `adrpy-ai` is available from PyPI, `pip install adrpy-tui` cannot resolve, so CI and local development install adrpy-ai from git (or an editable checkout) before `pip install -e ".[dev]"`.
4. **adrpy-tui is not published to PyPI until adrpy-ai is.** This is a decision not to act, and it is kept visible: the repository has no `publish.yml` workflow, and the README's installation section says why. Reopen this decision when adrpy-ai's first release is on PyPI: add the version floor, add the publish workflow, remove the README note.

### Positive Consequences

* The adrpy the TUI runs is always the one installed with it.
* One install step for users, once adrpy-ai is on PyPI.

### Negative Consequences

* adrpy-tui cannot be released until adrpy-ai is.
* In the meantime, every environment needs the extra git install step.
* No version floor means an incompatible adrpy-ai is not rejected at install time; the drift test of ADR004V01 catches contract changes in CI instead.

## Pros and Cons of the Options

### External prerequisite on PATH

* Good, because adrpy-tui could be published on its own right now.
* Bad, because the TUI may run a different adrpy than the one it was tested with, and needs its own version check.

### Declared dependency

* Good, because TUI and adrpy share one environment.
* Bad, because publishing waits for adrpy-ai.

### Wait for adrpy-ai on PyPI

* Good, because there is no interim workaround.
* Bad, because work on the TUI would not start.

## Links

* Refines [ADR001V01](ADR001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md).
* Relates to [ADR004V01](ADR004V01R01-forms-come-from-hand-written-per-command-specs-guarded-by-drift-and-coverage-tests-against-adrpy-help.md) -- the drift test that stands in for a version floor.
