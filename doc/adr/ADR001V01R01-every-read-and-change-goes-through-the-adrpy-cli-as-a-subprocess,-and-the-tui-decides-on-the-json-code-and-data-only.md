<!-- Do not remove this comment, lines and table (1-12) -->
|Adr-Plus Fields|Values|
|--|--|
|File title md|Every read and change goes through the adrpy CLI as a subprocess, and the TUI decides on the JSON code and data only|
|Version|01|
|Revision|01|
|Scope|integration|
|Domain|architecture|
|Created|Proposed (2026-09-28) <!-- Proposed -->|
|Changed|Accepted (2026-09-28) <!-- Accepted -->|
|Superseded||
<!-- Do not remove this comment, lines and table (1-12) -->
---
# Every read and change goes through the adrpy CLI as a subprocess, and the TUI decides on the JSON code and data only

## Deciders

* Deciders: Fernando Cerqueira (repo owner), decided while designing adrpy-tui's architecture.

Technical Story: adrpy-tui is the human-friendly layer over adrpy-ai, whose README states the goal directly: guided ADR management "that runs every change through the adrpy CLI".

## Context and Problem Statement

adrpy-ai is a JSON-only CLI with no wizard: every command takes flags and returns one JSON object on stdout (`{"success": ..., "data"/"code": ...}`), with a documented, closed set of failure codes per command and a human-readable `detail` that callers must not decide on (adrpy-ai ADR010V01). It is also a Python package, so its internals (`adrpy.core.*`) could be imported directly.

How does the TUI talk to adrpy: through the CLI's public JSON contract, or through adrpy-ai's internal Python API?

## Decision Drivers

* The TUI must never reimplement or bypass an adrpy rule (validate-before-act, the single-owner model, the supersede and family rules).
* adrpy-ai's JSON contract is public, documented and self-describing (`adrpy help --full`); its internal modules are not a stable API.
* What the TUI does must be exactly what a person or an agent would get by running the same command.
* Every call's outcome must be decidable from stable fields only.

## Considered Options

* Run the CLI as a subprocess and parse its JSON.
* Import adrpy-ai's internal modules and call them in-process.

## Decision Outcome

Chosen option: "Run the CLI as a subprocess and parse its JSON", because it is the only option that keeps the TUI bound to the public contract and makes every TUI action reproducible as a shell command.

1. Every read and every change is an `adrpy` or `adrpy-skills` invocation. The TUI never writes a decision file, a config file or a decision-log entry itself. Reading a decision's `.md` to display it is allowed.
2. One module (`client.py`) runs the subprocess and returns `success`, `data`, `code`, `detail`, `warnings` and the exit code. A stdout that is not a single JSON object is reported as a contract violation.
3. The TUI decides on `code` and `data` only. `detail` is shown to the person and never parsed. Where the TUI pre-validates a field for convenience, the CLI's failure code remains the final word.
4. Calls run one at a time in a background worker, so the UI stays responsive without ever running two adrpy commands at once (adrpy-ai ADR001V01's single-owner model).
5. Decisions are made on the canonical status `explore` reports (`Proposed`, `Accepted`, `Rejected`, `Superseded`), which does not change with the labels a repository configures (adrpy-ai ADR004V02's hidden marker). The configured labels (`statusnew`, `statusacc`, ...) are read through `adrpy config` for display only.

### Positive Consequences

* No adrpy rule is duplicated; a rule change in adrpy-ai reaches the TUI without a TUI change.
* The confirmation screen can show the exact command line about to run, and it is reproducible outside the TUI.
* Coupling is limited to a documented contract with its own compatibility commitments.

### Negative Consequences

* Each action costs a Python process start (tens of milliseconds), noticeable only if a screen chains many calls.
* Data the CLI does not expose cannot be shown without asking for a CLI change first.

## Pros and Cons of the Options

### Run the CLI as a subprocess and parse its JSON

* Good, because it is the public, documented contract, with a closed failure-code set per command.
* Good, because every TUI action equals a command a person or agent can run.
* Bad, because of the per-call process start.

### Import adrpy-ai's internal modules

* Good, because calls are in-process and fast.
* Bad, because `adrpy.core.*` is not a stable API: any internal refactor in adrpy-ai could break the TUI.
* Bad, because it invites calling a lower layer directly and skipping the command-level checks.

## Links

* Relates to adrpy-ai [ADR010V01](https://github.com/FRACerqueira/adrpy-ai/blob/main/doc/adr/ADR010V01-failure-responses-carry-a-human-readable-detail-in-the-stdout-json,-with-stderr-kept-as-a-copy-outside-the-contract.md) -- decide on `code`/`data`, never on `detail`.
* Relates to adrpy-ai [ADR001V01](https://github.com/FRACerqueira/adrpy-ai/blob/main/doc/adr/ADR001V01-single-owner-working-copy-without-concurrency-control,-validating-the-whole-repository-before-every-lifecycle-action.md) -- single owner per working copy.
* Relates to adrpy-ai [ADR004V02](https://github.com/FRACerqueira/adrpy-ai/blob/main/doc/adr/ADR004V02-decision-status-recognition-uses-a-hidden-canonical-marker%3B-status-labels-and-the-filename-separator-both-gain-an-existing-decisions-guard.md) -- status recognized by a canonical marker, not by its label.
* Refined by [ADR003V01](ADR003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui's-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md) -- how the CLI is obtained and invoked.
