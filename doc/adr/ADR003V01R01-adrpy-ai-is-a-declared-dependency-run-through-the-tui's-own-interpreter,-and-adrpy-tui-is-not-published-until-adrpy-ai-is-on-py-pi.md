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
* An adrpy-ai installed or upgraded apart from the TUI (`pip install -U adrpy-ai`) must not go unnoticed: its contract may not be the one the forms were written against.

## Considered Options

* External prerequisite on `PATH`, found with `shutil.which` and version-checked at start-up.
* Declared dependency, run as `sys.executable -m adrpy`.
* Wait for adrpy-ai to be on PyPI before starting.

## Decision Outcome

Chosen option: "Declared dependency", because it guarantees the TUI and its adrpy live in one environment and removes a manual install step.

1. `adrpy-ai` is listed by name, with no URL, in `dependencies`, with the range of the series the TUI was validated against: `adrpy-ai>=0.1.dev0,<0.2`. A `git+` URL would need hatch's `allow-direct-references` and would be wrong the day adrpy-ai reaches PyPI. The floor is `0.1.dev0`, not `0.1`, because a development build comes before its release (PEP 440): `>=0.1` refuses the `0.1.devN` builds that git and an editable checkout install, `>=0.1.dev0` takes them and every `0.1.x` release alike, so the same range holds before and after adrpy-ai is published. The ceiling `<0.2` also refuses `0.2.devN`, the builds where a new series' contract changes first.
2. The TUI runs `[sys.executable, "-m", "adrpy", ...]` and `[sys.executable, "-m", "adrpy.skills", ...]`, never a bare `adrpy` from `PATH`.
3. Until `adrpy-ai` is available from PyPI, `pip install adrpy-tui` cannot resolve, so CI and local development install adrpy-ai from git (or an editable checkout) before `pip install -e ".[dev]"`.
4. **The TUI checks the installed adrpy-ai against the same range at start-up** and, outside it, says so on the main menu, with the other start-up warnings (the version found and the range expected). It is a warning, not a refusal: the TUI keeps working, and a command adrpy refuses shows adrpy's own error. This covers what the install-time range cannot -- an adrpy-ai upgraded or downgraded later, apart from the TUI. The range is written once in `pyproject.toml`; a test fails if the start-up check reads another.
5. **A development build gets no exception.** Accepting any `.dev` version whatever its series was considered, to ease local testing, and declined: the range already takes the `0.1.devN` builds; the exception would only silence the warning for a `0.2.devN` build -- the case the check exists for -- and for anyone installing from git as the README says, and it would be one more thing to undo at release.
6. **adrpy-tui is not published to PyPI until adrpy-ai is.** This is a decision not to act, and it is kept visible: the repository has no `publish.yml` workflow, and the README's installation section says why. Reopen this decision when adrpy-ai's first release is on PyPI: add the publish workflow, remove the README note. The range needs no change then; it moves when the TUI is validated against a new adrpy-ai series (the drift test of ADR004V01 shows what changed), raising the ceiling one series at a time.

### Positive Consequences

* The adrpy the TUI runs is always the one installed with it.
* One install step for users, once adrpy-ai is on PyPI.
* An adrpy-ai outside the validated series is refused at install time and, if it arrives later, named on the main menu.

### Negative Consequences

* adrpy-tui cannot be released until adrpy-ai is.
* In the meantime, every environment needs the extra git install step.
* Each new adrpy-ai series needs a TUI change (the ceiling) before it installs with the TUI, even when its contract did not change.
* The start-up check warns, it does not verify the contract: within the range, a contract change the drift test of ADR004V01 did not see in CI still surfaces only as adrpy's error on a command.

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
* Relates to [ADR004V01](ADR004V01R01-forms-come-from-hand-written-per-command-specs-guarded-by-drift-and-coverage-tests-against-adrpy-help.md) -- the drift test that validates a series before the range admits it.
