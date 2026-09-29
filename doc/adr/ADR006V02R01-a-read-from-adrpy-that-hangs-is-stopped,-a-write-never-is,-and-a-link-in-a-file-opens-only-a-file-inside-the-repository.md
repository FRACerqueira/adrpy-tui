<!-- Do not remove this comment, lines and table (1-12) -->
|Adr-Plus Fields|Values|
|--|--|
|File title md|A read from adrpy that hangs is stopped, a write never is, and a link in a file opens only a file inside the repository|
|Version|02|
|Revision|01|
|Scope|integration|
|Domain|architecture|
|Created|Proposed (2026-09-29) <!-- Proposed -->|
|Changed|Accepted (2026-09-29) <!-- Accepted -->|
|Superseded||
<!-- Do not remove this comment, lines and table (1-12) -->
---
# A read from adrpy that hangs is stopped, a write never is, and a link in a file opens only a file inside the repository

## Deciders

* Deciders: Fernando Cerqueira (repo owner), in the first round of the pre-release audit; version 02 in its second round.

Technical Story: the audit's resilience pass found that the client runs adrpy with no timeout: a hung adrpy leaves the start-up screen loading forever, blocks every later call behind the one-call lock, and keeps the process alive after the person quits. Its command-fidelity passes found that a link in a decision or log file is followed to any path it names, including a network share (`//host/share/x.md`) that the operating system connects to on the first look.

The second round found what version 01 left open. Leaving a write released the one-call lock while adrpy still wrote, so a second write could start beside it; a write queued behind a hung read ignored Leave and started after the person left; quitting still waited for a read. And the link check was lexical: a folder link (a symlink, a Windows junction) inside the repository led anywhere -- version 01 said the link was checked "after resolving it", which the code did not do and must not do.

## Context and Problem Statement

Every read and change is an adrpy subprocess (ADR001V01). A read (`explore`, `config` with no field flags, `check`, `help`, `skills list`) can be stopped at any time without harm; a write (`new`, `approve`, `migrate`, ...) may be half-way through writing files when it is stopped. Separately, the preview follows links between `.md` files, and the file holding the link is not always the person's own.

When adrpy does not answer, what does the TUI do with a read, and with a write? And which files may a link in a file open?

## Decision Drivers

* A person must never be left without a visible state and a way out.
* adrpy's own writes must never be interrupted by the TUI: a half-written repository is worse than a slow one.
* The silence of a stopped or abandoned call must not pass for success.
* Content from a file the TUI did not write must not make the machine reach anything outside the repository.
* Two adrpy writes must never run on one working copy at once: adrpy-ai has no concurrency control by design, and calls it a usage error (its own ADR001V01).

## Considered Options

* A timeout on reads only; a write is never stopped, the person may leave it, and the result is said to be unknown.
* The same long timeout on every call, a write included.
* No timeout; only a way to leave and a "still waiting" line.
* Links: only `.md` files inside the repository; or any `.md` file the link names.
* A write left running: refuse another write while it runs, letting reads through; or hold the one-call lock until it ends.

## Decision Outcome

Chosen option: "A timeout on reads only", because it keeps every read bounded without ever interrupting adrpy in the middle of a write; and, for links, "only inside the repository", because nothing in an ADR repository needs a link outside it and a network path turns one click into a connection to another machine. For a write left running, "refuse another write", because two adrpy writes on one working copy are a usage error and the Check the person is offered must still run.

1. **A read that does not answer within its timeout is stopped** (its process ended) and becomes a failed result with the TUI's own code `tui-timeout`, shown as any failure is. Reads change nothing, so stopping one is safe.
   Quitting the TUI stops a read in flight the same way.
2. **A write is never stopped by the TUI.** When it has not answered within the same time, the screen says so -- adrpy is still running, its result is unknown -- and offers to leave. Leaving stops the TUI's waiting only; adrpy's process goes on to its own end. Quitting the TUI does not wait for it either. A write still waiting for adrpy -- another call ahead of it -- can be left too, and is then never started (`tui-not-started`).
3. **While a write that was left still runs, the TUI starts no other write** (`tui-write-still-running`); reads, Check first, still run. Holding the one-call lock until it ends would block the very Check the person is offered.
4. **A preview opens only a `.md` file inside the repository**, whoever names it -- a link, adrpy, a command's result -- and so do the decisions and log folders a configuration names. An absolute path, a network path, or one that leads outside the repository is refused before the file system is touched; then each folder below the repository's root is looked at with `lstat`, and a folder link on the way (a symlink, a junction) is not followed. The path is never resolved: resolving opens the target, which may be on another machine. The preview names what it refuses, as it names a web link. Web links are still never opened (ADR001V01's boundaries).

### Visibility plan

This is a decision not to act automatically on a failure (a hung write is not killed), so it says how the person notices it on the day it matters:

* A write past its time shows, on the running screen itself: "adrpy has not answered in N s. It is still running, so its result is unknown. Leave, then run Check to see the repository's state." with Check offered there. A result that never came is never shown as success.
* A stopped read shows `tui-timeout` with the command and the time waited, on the screen that asked.
* A refused link names the path and why it was not opened.
* A refused write says a command the person left still runs, and to wait for it, then run Check.

### Positive Consequences

* No screen waits forever on a read; the one-call lock is always released for a read.
* A write is never cut half-way by the TUI.
* A link cannot make the TUI touch a file or a machine outside the repository.

### Negative Consequences

* A write that really hangs keeps running in the background until adrpy ends or the person ends it; the TUI only says so.
* A legitimately slow read on a very large repository is stopped at the timeout.
* Links to `.md` files outside the repository (a sibling checkout) no longer open from the preview, nor does a repository whose documents are reached through a folder link.
* After leaving a write, no other write can run until adrpy ends it; if it truly hangs, only ending that process frees the TUI for writes.

## Pros and Cons of the Options

### A timeout on reads only

* Good, because every read is bounded, and no write is interrupted.
* Bad, because a hung write has no automatic end.

### The same long timeout on every call

* Good, because nothing waits forever.
* Bad, because it can stop adrpy in the middle of writing a decision, leaving the repository for `check` to repair.

### No timeout

* Good, because nothing is ever stopped.
* Bad, because a hung read blocks every later call behind the one-call lock.

### Refuse writes while a left one runs

* Good, because two writes never run at once, and Check still runs.
* Bad, because a hung left write blocks every later write until its process ends.

### Hold the lock until the left write ends

* Good, because nothing at all runs beside it.
* Bad, because the Check the person is offered waits behind it too.

### Links anywhere

* Good, because a link to a sibling repository would open.
* Bad, because a network path makes the machine connect to another host on one click, from a file the person may not have written.

## Links

* Refines [ADR001V01](ADR001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md) -- the subprocess boundary and the never-opened web links.
* Version 02 of ADR006V01 (the pre-release audit's second round).
* Relates to [ADR003V01](ADR003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md) -- the adrpy the TUI runs.
