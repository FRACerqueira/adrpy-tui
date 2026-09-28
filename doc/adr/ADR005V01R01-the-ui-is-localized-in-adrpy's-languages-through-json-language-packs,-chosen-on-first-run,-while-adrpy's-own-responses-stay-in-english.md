<!-- Do not remove this comment, lines and table (1-12) -->
|Adr-Plus Fields|Values|
|--|--|
|File title md|The UI is localized in adrpy's languages through JSON language packs, chosen on first run, while adrpy's own responses stay in English|
|Version|01|
|Revision|01|
|Scope|i18n|
|Domain|ui|
|Created|Proposed (2026-09-28) <!-- Proposed -->|
|Changed|Accepted (2026-09-28) <!-- Accepted -->|
|Superseded||
<!-- Do not remove this comment, lines and table (1-12) -->
---
# The UI is localized in adrpy's languages through JSON language packs, chosen on first run, while adrpy's own responses stay in English

## Deciders

* Deciders: Fernando Cerqueira (repo owner), decided while designing adrpy-tui's first screens.

Technical Story: the TUI must be usable in every language adrpy supports, and a person running it for the first time chooses the language before anything else.

## Context and Problem Statement

adrpy-ai ships language packs (`adrpy/resources/language_packs/<language>.json`) for eleven languages: `en-us`, `pt-br`, `de-de`, `es-es`, `fr-fr`, `it-it`, `ja-jp`, `ko-kr`, `nl-be`, `ru-ru`, `zh-cn`. They translate a decision's header labels and default template (`adrpy init --language`), not the CLI's messages: every `detail`, every `help` description and every failure code is English.

How is the TUI's own text localized, how is the language chosen, and what happens to the text adrpy itself returns?

## Decision Drivers

* The same eleven languages as adrpy, and no drift between the two lists.
* No further runtime dependency (ADR002V01 allows Textual only) and no build step.
* Follow adrpy-ai's own model where possible.
* Never alter what adrpy returns (ADR001V01).

## Considered Options

* `gettext` catalogs (`.po` compiled to `.mo`).
* JSON language packs loaded with `importlib.resources`, as adrpy-ai does.
* English only.

## Decision Outcome

Chosen option: "JSON language packs", because it is adrpy-ai's own mechanism, needs only the standard library and no compile step, and keeps every text of a language in one reviewable file.

1. Every text the TUI itself shows -- menus, labels, field checks, header lines, key hints -- comes from `adrpy_tui/resources/language_packs/<language>.json`, one file per language adrpy supports. `en-us` is the reference.
2. Two tests keep the packs honest: every pack has exactly `en-us`'s keys, and the set of packs equals the languages `adrpy help init` lists for `--language`.
3. On first run -- no language stored in the per-user state file -- the first screen, under the header, is the language choice, listing each language by its own name, with the operating system's language preselected when it is one of the eleven, `en-us` otherwise. The choice is stored, and a "Language" item in the main menu changes it later.
4. The UI language preselects `--language` in the `init` form.
5. **adrpy's own responses are shown as adrpy sends them, in English**: `detail`, `help` descriptions, failure codes. The TUI does not translate them. This is a decision not to act: it is visible to the person because the result and help screens show adrpy's text as is, and the README says so. Reopen it if adrpy-ai localizes its messages.
6. The ten non-English packs were written from `en-us` without a native speaker's review; each needs one, and the CHANGELOG says so until it has happened.

### Positive Consequences

* The TUI speaks every language adrpy supports, with no new dependency.
* A language added to adrpy fails the TUI's tests until the TUI has its pack too.

### Negative Consequences

* A screen mixes languages: the TUI's text is localized, adrpy's messages are English.
* Every new text needs eleven translations before the tests pass.
* The first translations are unreviewed.

## Pros and Cons of the Options

### gettext catalogs

* Good, because it is the standard mechanism, with plural forms and translator tooling.
* Bad, because `.mo` files need a compile step (`msgfmt` is not always installed with Python) and binary files in the repository.

### JSON language packs

* Good, because it matches adrpy-ai, needs only the standard library, and a missing key is caught by a test.
* Bad, because there is no plural handling or translator tooling.

### English only

* Good, because there is nothing to translate.
* Bad, because it fails the requirement.

## Links

* Follows adrpy-ai's language packs (`adrpy/resources/language_packs/`).
* Relates to [ADR001V01](ADR001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md) -- adrpy's responses are shown, never rewritten.
* Relates to [ADR002V01](ADR002V01R01-textual-is-the-tui-framework,-a-deliberate-runtime-dependency-unlike-adrpy-ai.md) -- no dependency beyond Textual.
