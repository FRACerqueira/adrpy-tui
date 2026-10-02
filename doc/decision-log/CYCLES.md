# Decision log cycles

A **cycle** groups a range of `Round` numbers (see `INDEX.md`) under a
human-friendly name, for narrative and retrospective reference only. It is
never a field on individual decision-log entries -- only `Round`, a single,
project-wide, ever-increasing integer, lives there. This file is the only
place a cycle's name is recorded.

## The naming rule

1. **Derive the name from the cycle's own dominant theme**, grounded in the
   real content of its rounds (the scope and front of its `audit-finding`
   and `doc-drift` entries, and any ADR born or touched during it), and
   state which entries support it.
2. **Name the outcome, not the process**: someone with no context should be
   able to guess what got safer or better.
3. **Short, and immutable once written here.** A correction is a new note
   pointing at the old one, never an edit in place.
4. **Named in hindsight**, once the cycle is over.
5. **Closed by the project owner** saying the audit is done or paused, not
   by a round count or a calendar.
6. **Always proposed, never decided by the agent alone**: the same "ask
   before writing" gate as every other decision-log write.

## Cycles

| Rounds | Dates | Name | Notes |
|---|---|---|---|
| 1-4 | 2026-09-28 to 2026-09-29 | **Untrusted-Input and adrpy-Call-Lifecycle Hardening** | Closed and named by the project owner (2026-09-29), after round 4. Supporting evidence (rule 1): the 8 High `audit-finding` entries, all in round 1, are about untrusted input and adrpy's calls -- a repository's `adrpy/` folder running instead of adrpy, markup from files and adrpy reaching the UI, a hung adrpy with no way out. The most frequent scopes over the four rounds are `client`, `preview`, `text` and `files` besides `tests`: what a file, adrpy's JSON or a field may hold (`visible`, `field_text`, `decisions.listed`), a link or folder link leading outside the repository (`core/files.py`), and a call that hangs, is left or outlives the app. ADR006 was born in this cycle (V01, the read timeout and the link scope) and revised twice (V02, a write left and never stopped; V02R02, Check's warning). Scores per front fell from round 1 to round 4 -- fidelity 43 to 8, resilience 27 to 11, async 23 to 4 -- with no High after round 1; the test-adequacy front stayed near 15, measured by mutation testing from round 3 on. |
| 5-7 | 2026-09-30 | **Adherence to adrpy's Current Contract, and Folders as adrpy Resolves Them** | Closed and named by the project owner (2026-09-30). Supporting evidence (rule 1): 18 `audit-finding`/`doc-drift` entries over the three rounds (scores 9, 9, 4; no High). The result and config screens follow adrpy's current contract, and migrate and the log browser mirror its listing rules (rounds 5-6); round 7 spelled every configured folder as adrpy resolves it through one helper, told a folder link apart from a path outside the repository, and mirrored adrpy-ai round 53's any-case `.md` in the log (`the-log-browser-spells-its-folder-as-adrpy-resolves-it`, `the-log-browser-reads-md-in-any-case-as-adrpy`). |
| 8-9 | 2026-10-02 | **Editing Decisions in the Person's Editor, and Screens That Say Only What Acts** | Closed and named by the project owner (2026-10-02), after round 9. Supporting evidence (rule 1): 26 `audit-finding`/`doc-drift` entries over the two rounds (scores 28, 18; no High, no Retraction; 23 Direct, 3 Escalated to the owner). ADR0007 was born in this cycle (V01, a Proposed decision's text edited in the person's editor, never by the TUI) and its item 4 corrected twice. Half the entries are the editor: the client's list of left processes, an editor started after the wait was left, a PATH share that froze the screen, a broken header with no way to edit it again (`client--left-list-lost-an-append`, `editors--network-path-entry-froze-the-screen`, `check--broken-header-left-no-edit`). The other half is the screens saying only what acts: the key line built from what each screen shows and has the focus (`hints--enter-and-arrows-unnamed-on-forms`, `hints--key-line-while-a-command-runs`), what check says after an edit, the texts in each pack's own words, and tests for the mutations that survived. Every screen fits 80x24 and buttons say what they do by color, from the same release. The usability front fell from 18 to 12 without reaching zero; what remains needs a real terminal (the manual checklist). |
| 10-11 | 2026-10-02 | **Checking for a Newer Version Without Trusting the Network** | Closed and named by the project owner (2026-10-02), after round 11. Supporting evidence (rule 1): 17 `audit-finding`/`doc-drift` entries over the two rounds (scores 13, 4; no Medium or High, no Retraction; 12 Direct, 5 Escalated to the owner) and two `risk-accepted`, all on the update check ADR0008V01 born in this cycle (and undone, rewritten and approved again three times as the rounds decided its first start, what is never offered, its deciders and its timeout). Most entries are PyPI's answer treated as untrusted: HTTP errors that escaped the check, no deadline for the whole answer and then one that covered the body only, versions in other digits or thousands long, and the answer's hand-off to the app swallowing or crashing on it (`updates--http-errors-escaped-the-check`, `updates--no-deadline-for-the-whole-answer`, `updates--deadline-covered-only-the-body`, `versions--non-ascii-or-overlong-version-accepted`, `app--answer-hand-off-swallowed-ui-bugs`, `updates--status-line-before-the-screen-was-mounted`). The rest is a failure made visible (the Updates screen's status line, a timeout on the main menu) and the docs saying what the check sends and when it asks. |
