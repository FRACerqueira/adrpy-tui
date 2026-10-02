<!-- Do not edit or remove this comment, lines and table (1-12) -->
|Fields|Values|
|--|--|
|File title md|A Proposed decision's text is edited in the editor the person chose, never by the TUI, and adrpy check validates the file afterwards|
|Version|01|
|Revision|02|
|Scope||
|Domain||
|Created|Proposed (2026-10-01) <!-- Proposed -->|
|Changed|Accepted (2026-10-01) <!-- Accepted -->|
|Superseded||
<!-- Do not edit or remove this comment, lines and table (1-12) -->
---
# A Proposed decision's text is edited in the editor the person chose, never by the TUI, and adrpy check validates the file afterwards

## Deciders

* Deciders: Fernando Cerqueira (repo owner).

Technical Story: creating a decision leaves its body as the repository's template, and the TUI offers no way to edit it.

## Context and Problem Statement

`adrpy new` writes the decision with the repository's template below its header, and takes no body: its arguments are `path`, `title`, `domain`, `scope` and `refdate`. No adrpy command writes a decision's body. ADR0001V01 keeps the TUI from writing a decision file itself. How does a person write a decision's text without leaving the TUI, and without the TUI writing the file?

## Decision Drivers <!-- optional -->

* The TUI writes no decision file (ADR0001V01).
* A person writes a decision's text without leaving the TUI, in an editor they already use.
* An editor that returns at once would let check run before the text is written.
* An Accepted decision's text changes only through adrpy's lifecycle (`revise`, `version`).

## Considered Options

* Open the decision in an editor the person chose, then run `adrpy check`.
* A Markdown editor inside the TUI that writes the file itself.
* A new adrpy-ai command that writes a decision's body, fed by an editor inside the TUI.

## Decision Outcome

Chosen option: "Open the decision in an editor the person chose, then run `adrpy check`", because it keeps ADR0001V01 whole without a change to adrpy-ai, and the text is written in the editor the person already uses.

1. The editor is a per-user setting, kept with the language, appearance and keys; never in `.adrpy.json`, which is adrpy's and refuses a field it does not know (`config-unexpected-field`). None is the default: no editor is opened and the field and Edit below are not offered; the person edits the file, knowing its body is the template.
2. It is chosen from a closed list of editors that return only once the file is closed: in the terminal `vim`, `nvim`, `nano`, `micro`, `hx`; with a window `code --wait`, `codium --wait`, `subl --wait`, `kate --block`, `gedit --standalone`, `gvim -f`, `notepad`. An editor not found on the PATH of the system the TUI runs on is shown with the reason, not offered (inside WSL, that is the distribution's PATH). Visual Studio is left out: it has no way to wait for one file to be closed.
3. Only a Proposed decision is edited. The `new`, `version`, `revise` and `supersede` forms have an on/off "open in the editor" field while an editor is set, and a Proposed decision's detail offers Edit. An Accepted decision's text changes through `revise` or `version`, as adrpy's lifecycle has it.
4. The TUI starts the editor and waits for it, as for a write: no other adrpy command runs meanwhile, and the person can stop waiting for an editor with a window. A terminal editor gets the terminal while the TUI is suspended, and keeps it until it closes. Once it returns, the TUI runs `adrpy check` and shows its result. It repairs nothing: a broken header is shown with check's hints, and the editor can be opened again.

### Positive Consequences <!-- optional -->

* No adrpy-ai change: every write to a decision's header is still adrpy's.
* A broken header is found at once, by `adrpy check`, with its hints.

### Negative Consequences <!-- optional -->

* The TUI starts a program that is not adrpy.
* On Windows a launcher such as `code.cmd` runs through `cmd.exe`, whose quoting a decision's name (commas, apostrophes, `%`) must survive.
* An editor that does not wait for its file to be closed cannot be on the list.

## Pros and Cons of the Options <!-- optional -->

### Open the decision in an editor the person chose, then run `adrpy check`

* Good, because the TUI writes no decision file.
* Good, because it needs no adrpy-ai change.
* Bad, because the TUI must know how each editor waits, and a launcher's quoting.

### A Markdown editor inside the TUI that writes the file itself

* Good, because the text is written without leaving the TUI's own screens.
* Bad, because the TUI would write a decision file, against ADR0001V01, and keep the header's 12 lines whole itself -- an adrpy rule written again.

### A new adrpy-ai command that writes a decision's body, fed by an editor inside the TUI

* Good, because every write still goes through adrpy, as `adrpy log --body` does for a log entry.
* Bad, because it needs a new command, its contract and tests in adrpy-ai, and a new adrpy-ai release first.

## Links <!-- optional -->

* Refines [ADR0001V01](ADR0001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md) -- the TUI still writes no decision file; the editor the person chose does.
* Relates to [ADR0006V02](ADR0006V02R02-a-read-from-adrpy-that-hangs-is-stopped,-a-write-never-is,-and-a-link-in-a-file-opens-only-a-file-inside-the-repository.md) -- only a file inside the repository is opened.
