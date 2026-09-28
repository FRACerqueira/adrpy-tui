# Forms

How every `adrpy` and `adrpy-skills` command is reached and filled in,
with the Textual 8 widget used for each kind of input. Where Textual has no
ready-made component, the closest core widget is used rather than a custom
one or a new dependency, so the experience can be validated first
([ADR002V01](adr/ADR002V01R01-textual-is-the-tui-framework,-a-deliberate-runtime-dependency-unlike-adrpy-ai.md)).

## Header

Every screen extends one base screen that renders the same header;
modals open over it, so it stays visible.

```
══════════════════════════════════════
    _    ____  ____       ______   __
   / \  |  _ \|  _ \     |  _ \ \ / /
  / _ \ | | | | |_) |____| |_) \ V /
 / ___ \| |_| |  _ <_____|  __/ | |
/_/   \_\____/|_| \_\    |_|    |_|
══════════════════════════════════════
Welcome to adrpy-tui (<version>) · adrpy-ai <version>
Repo: <repository root>
'<command>' command started
```

The banner is FIGlet *standard* text stored in the source (no FIGlet
dependency), between two double rules.

## Colors

CSS colors, as Textual theme variables:

| Role | Color |
|---|---|
| Banner, command started/finished | darkorange `#FF8C00` |
| Info, key footer | grey `#808080` |
| Warnings | gold `#FFD700` |
| Summary, confirmation | navajowhite `#FFDEAD` |
| Help | skyblue `#87CEEB` |
| Error | red `#FF0000` |
| Result | white `#FFFFFF` |
| Typed value | cyan `#00FFFF` (approximate, to validate) |
| Highlighted item | green `#00FF00` (approximate, to validate) |

## Components

| Input | Used for | Textual |
|---|---|---|
| Menu | menus | `OptionList` (disabled items), description panel below |
| Decision choice | choosing a decision | `AdrPicker`: filter `Input` + `OptionList`, status column, ineligible items disabled |
| Enum | separator, casetransform, language, log enums | `Select` |
| Validated text | titles, labels, prefix | `Input(max_length, restrict, validators)` |
| Text with suggestions | scope, domain | `Input` whose inline suggestion continues what was typed (prefix match, `→` accepts it), plus a line below listing existing values that contain the text or look like it (`difflib`) |
| Small integer range | lenseq/lenversion/lenrevision | `Select` over the allowed range |
| Date | refdate | `MaskedInput` `9999-99-99`, defaults to today |
| On/off | `--empty`, booleans | `Switch` |
| Several of a list | explore columns, migrate list | `SelectionList` |
| Table | explore | `DataTable` + filter |
| Folder or file | repository, `--seed` | `DirectoryTree` filtered |
| Confirmation | every change | modal showing the exact command line about to run |
| Progress | reads | `LoadingIndicator` |
| Decision content | detail view | `MarkdownViewer`, read-only |

## Menus

```
Main menu
├─ 1 Decisions             new · approve · reject · undo · version · revise · supersede
├─ 2 Explore and validate  explore (table → detail) · check
├─ 3 Decision log          log
├─ 4 Repository            init · config · migrate
├─ 5 Install config        installconfig
├─ 6 AI skills             list · install · remove
├─ 7 Command help          one item per adrpy and adrpy-skills command
├─ 8 Change repository
├─ 9 Language
└─ 0 Exit
```

- The first run starts with the language choice (ADR005V01): the eleven
  languages adrpy supports, each by its own name, the operating system's
  language preselected when it is one of them. "Language" changes it later,
  from the same list with "← Back" on top and the current language
  highlighted; the first run has no Back, since there is no menu yet.
- With no repository configured (`config-not-found`), groups 1-3 and
  `config`/`migrate` are disabled.
- Every submenu starts with "← Back"; `Esc` also goes back one level. A
  submenu opens on its first command, or on the item last selected in it;
  choosing Back is not remembered. A grey line under each screen lists its
  keys.
- The last selected item of each menu is remembered across sessions.
- The repository is chosen once, shown in the header and changed from the
  menu, rather than asked for in every command.

## Per-command forms

Eligibility compares against the canonical status `explore` reports
(`Proposed`, `Accepted`, `Rejected`); the repository's own labels from
`adrpy config` are only displayed. `refdate` is never after today and,
where the command says so, never before the decision's own relevant date
from `explore`.

| Command | Fields → component |
|---|---|
| `new` | title `Input` (required; no `\|<>:"/\?*`) · domain, scope `Input` + suggestions from `explore` · refdate |
| `approve`, `reject` | `AdrPicker` (`Proposed`) · refdate |
| `undo` | `AdrPicker` (`Accepted`/`Rejected`) |
| `version` | `AdrPicker` (`Accepted`/`Rejected`) · scope, domain prefilled from the header · refdate · `--empty` `Switch` |
| `revise` | `AdrPicker` (`Accepted`/`Rejected`) · refdate |
| `supersede` | `AdrPicker` (`Accepted`) · title, scope, domain prefilled · refdate |
| `explore` | `DataTable`, File and Status fixed, other columns picked in a `SelectionList`, filter; `Enter` opens the detail (header fields + `MarkdownViewer`) with the actions the status allows |
| `check` | table of file, code and repair hint, or "no inconsistencies" |
| `init` | folder `DirectoryTree` · config source `RadioSet`: install-level/built-in, language pack (`Select`, preselected with the UI language), seed file. Language is disabled when `installconfig` reports `configured: true` |
| `config` | field list with current value and description, plus "Save and exit"; each field opens its editor (enum → `Select`, integer → `Select`, boolean → `Switch`, template → `TextArea`, text → `Input`). Only changed fields become flags |
| `installconfig` | the same field editor, plus seed and language |
| `migrate` | (1) read-only list of every file's state; (2) without a `migrationpattern`, a guided builder from a sample file name, with position/length per part and a live preview through `explore --migrationpattern`; (3) confirm, then `config --migrationpattern` and `migrate` |
| `log` | classification `Select` · scope, slug `Input` (kebab-case) · summary `Input` · body `TextArea` · refdate · front, severity, resolution, round only for `audit-finding`/`doc-drift` · reopenwhen only for `deferred` |
| `skills list` | table of skill, provider, scope, installed, drifted |
| `skills install`, `skills remove` | provider, skill `SelectionList` · target `RadioSet` (project/global; global only for claude) · `--force`, `--allow-external-links` `Switch` |
| `help` | description, arguments table and failure codes table, in the help color |

## Result screen

Success shows the result in white and any `warnings` in gold; failure shows
`detail` in red and, when present, `data.errors` as a table with repair
hints. `Enter` returns to the menu.
