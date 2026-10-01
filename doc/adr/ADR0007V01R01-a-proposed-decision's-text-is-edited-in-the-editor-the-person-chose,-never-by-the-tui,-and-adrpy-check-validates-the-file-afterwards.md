<!-- Do not edit or remove this comment, lines and table (1-12) -->
|Fields|Values|
|--|--|
|File title md|A Proposed decision's text is edited in the editor the person chose, never by the TUI, and adrpy check validates the file afterwards|
|Version|01|
|Revision|01|
|Scope||
|Domain||
|Created|Proposed (2026-10-01) <!-- Proposed -->|
|Changed|Accepted (2026-10-01) <!-- Accepted -->|
|Superseded||
<!-- Do not edit or remove this comment, lines and table (1-12) -->
---
# A Proposed decision's text is edited in the editor the person chose, never by the TUI, and adrpy check validates the file afterwards

## Deciders

* Deciders: [list everyone involved in the decision] <!-- optional -->

Technical Story: creating a decision leaves its body as the repository's template, and the TUI offers no way to edit it.

## Context and Problem Statement

`adrpy new` writes the decision with the repository's template below its header, and takes no body: its arguments are `path`, `title`, `domain`, `scope` and `refdate`. No adrpy command writes a decision's body. ADR0001V01 keeps the TUI from writing a decision file itself. How does a person write a decision's text without leaving the TUI, and without the TUI writing the file?

## Decision Drivers <!-- optional -->

* [driver 1, e.g., a force, facing concern, …]
* [driver 2, e.g., a force, facing concern, …]
* … <!-- numbers of drivers can vary -->

## Considered Options

* Open the decision in an editor the person chose, then run `adrpy check`.
* A Markdown editor inside the TUI that writes the file itself.
* A new adrpy-ai command that writes a decision's body, fed by an editor inside the TUI.

## Decision Outcome

Chosen option: "Open the decision in an editor the person chose, then run `adrpy check`", because [justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | … | comes out best (see below)].

1. The editor is a per-user setting, kept with the language, appearance and keys; never in `.adrpy.json`, which is adrpy's and refuses a field it does not know (`config-unexpected-field`).
2. It is chosen from a closed list of editors that return only once the file is closed: in the terminal `vim`, `nvim`, `nano`, `micro`, `hx`; with a window `code --wait`, `codium --wait`, `subl --wait`, `kate --block`, `gedit --standalone`, `gvim -f`, `notepad`. An editor not found on PATH is shown, not offered. Visual Studio is left out: it has no way to wait for one file to be closed.
3. Only a Proposed decision is edited. The `new`, `version`, `revise` and `supersede` forms have an on/off "open in the editor" field while an editor is set, and a Proposed decision's detail offers Edit. An Accepted decision's text changes through `revise` or `version`, as adrpy's lifecycle has it.
4. The TUI starts the editor and waits for it; a terminal editor gets the terminal while the TUI is suspended. Once it returns, the TUI runs `adrpy check` and shows its result. It repairs nothing: a broken header is shown with check's hints, and the editor can be opened again.

### Positive Consequences <!-- optional -->

* [e.g., improvement of quality attribute satisfaction, follow-up decisions required, …]
* …

### Negative Consequences <!-- optional -->

* [e.g., compromising quality attribute, follow-up decisions required, …]
* …

## Pros and Cons of the Options <!-- optional -->

### [option 1]

[example | description | pointer to more information | …] <!-- optional -->

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]
* … <!-- numbers of pros and cons can vary -->

### [option 2]

[example | description | pointer to more information | …] <!-- optional -->

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]
* … <!-- numbers of pros and cons can vary -->

### [option 3]

[example | description | pointer to more information | …] <!-- optional -->

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]
* … <!-- numbers of pros and cons can vary -->

## Links <!-- optional -->

* Refines [ADR0001V01](ADR0001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md) -- the TUI still writes no decision file; the editor the person chose does.
* Relates to [ADR0006V02](ADR0006V02R02-a-read-from-adrpy-that-hangs-is-stopped,-a-write-never-is,-and-a-link-in-a-file-opens-only-a-file-inside-the-repository.md) -- only a file inside the repository is opened.
