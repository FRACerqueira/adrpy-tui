<!-- Do not remove this comment, lines and table (1-12) -->
|Fields|Values|
|--|--|
|File title md|Forms come from hand-written per-command specs guarded by drift and coverage tests against adrpy help|
|Version|01|
|Revision|01|
|Scope|forms|
|Domain|ui|
|Created|Proposed (2026-09-28) <!-- Proposed -->|
|Changed|Accepted (2026-09-28) <!-- Accepted -->|
|Superseded||
<!-- Do not remove this comment, lines and table (1-12) -->
---
# Forms come from hand-written per-command specs guarded by drift and coverage tests against adrpy help

## Deciders

* Deciders: Fernando Cerqueira (repo owner), decided while designing adrpy-tui's forms.

Technical Story: the forms must cover every adrpy and adrpy-skills command with rich components (select lists for enums, ranges, conditional fields, suggestions), see [`doc/forms.md`](../forms.md).

## Context and Problem Statement

`adrpy help --full` returns each command's arguments with `name`, `type` (`string`, `integer`, `switch`, `boolean`) and `required`. The allowed choices and ranges exist only as prose inside `description` ("One of ('-', '_', '.')", "Integer between 3 and 6"), and so do the conditional rules (`log`'s `--front`/`--severity`/`--resolution` only for `audit-finding`/`doc-drift`, `--reopenwhen` only for `deferred`).

Are forms generated from `adrpy help` at runtime, or defined by hand?

## Decision Drivers

* Forms need choices, ranges and conditions to offer a `Select` or a conditional field rather than a bare text box.
* Parsing prose descriptions is fragile: adrpy-ai may reword a description in any release.
* Hand-written forms can silently fall behind the CLI, which is exactly what adrpy-ai's own generated command docs avoid.
* "Cover every command" must be checkable, not a promise.

## Considered Options

* Generate every form from `adrpy help --full` at runtime.
* Generate from `adrpy help`, parsing choices and ranges out of the descriptions.
* Hand-written specs per command, guarded by tests against `adrpy help --full`.

## Decision Outcome

Chosen option: "Hand-written specs, guarded by tests", because it is the only option that gives rich components without depending on prose, while still failing loudly when the CLI changes.

1. One module per command under `forms/`, registered in `core/registry.py` (as adrpy-ai maps its verbs to `cli/` modules), holds that command's spec: the component for each flag, its choices or range, conditional visibility, and where suggestions and eligibility come from. The spec's vocabulary:
   * a field shown only while another holds a value (`shown_when`), and required only while shown (`required_if_shown`) when adrpy itself takes the flag as optional -- `required` always stays adrpy's;
   * a field of the screen only, never sent (`local`), such as the choice of which fields appear;
   * a command whose interaction is not a form declares a screen of its own (`VIEW`: explore, check, config, installconfig, migrate, skills list); its flags are still listed, the screen building them;
   * a flag a screen deliberately does not offer is named with the reason (`NOT_OFFERED`), rather than silently left out.
2. A **drift test** compares every spec with `adrpy help --full` and `adrpy-skills help --full`: the flag names -- the fields but the `local` ones, the path flag and the `NOT_OFFERED` ones -- are exactly the command's, each field's `required` is adrpy's, and adrpy's commands require the path flag (adrpy-skills defaults it to the current folder). It runs against the installed adrpy-ai in CI.
3. A **coverage test** checks that every command either `help` lists is reachable from the menu.
4. Descriptions shown in the forms still come from `help` at runtime, so the text the person reads is adrpy's own.

### Positive Consequences

* Rich components for every command.
* A new or renamed flag in adrpy-ai fails CI instead of silently producing a stale form.
* Coverage of all commands is enforced by a test.

### Negative Consequences

* Choices and ranges are duplicated from adrpy-ai's prose; the drift test checks names and `required`, not the choices themselves -- a changed range is only caught by the CLI rejecting the value.
* Every new adrpy command needs a spec before CI goes green.

## Pros and Cons of the Options

### Generate every form at runtime

* Good, because it never drifts.
* Bad, because every field becomes a plain text box or switch -- no enums, ranges or conditions.

### Generate and parse the descriptions

* Good, because choices would follow adrpy automatically.
* Bad, because it breaks on any rewording of a description.

### Hand-written specs, guarded by tests

* Good, because it gives rich components with drift detected in CI.
* Bad, because choices and ranges are maintained twice.

## Links

* Modeled on adrpy-ai's `tests/test_command_docs.py`, which fails when the generated command docs fall behind `describe()`.
* Relates to [ADR0003V01](ADR0003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui's-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md) -- the drift test stands in for a version floor.
