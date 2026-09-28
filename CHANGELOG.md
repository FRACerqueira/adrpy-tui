# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project intends to follow [Semantic Versioning](https://semver.org/) once it reaches `1.0.0`.

## [Unreleased]

### Added

- **The first screens.** The header, the language choice on first run, the main menu with every adrpy and adrpy-skills command grouped by use, the `new`, `approve`, `reject`, `undo`, `version`, `revise`, `supersede` and `init` forms, the config and install-level config editors, the guided migrate builder, the `log` form, the AI skills screens (list, install, remove), change repository, the explore screen (every decision, then one decision's detail with the commands its state allows) and the check screen (a decision picker lists every decision with its label, the ones the command cannot take disabled), the confirmation screen showing the exact command line about to run, the result screen and the help of every command. Every command of adrpy and adrpy-skills has its screen.
- **Keys that can be changed** (run, preview, show all), kept per user; the key line always names the key that works.
- **Previews** (F3) of any decision or log entry from every list of them, with links between `.md` files followed; explore shows each decision's folder and filters by it; a decision-log browser.
- **Appearance presets**: Default (dark), Light and High contrast, previewed live and kept per user, with any color customizable on top of them.
- **The highlighted item stands out**: in menus and tables its whole row takes the highlight color, with its text in the cursor color (3:1 or more apart from the other rows in every preset); out of focus it keeps the cursor color; the row under the mouse is underlined.
- **Headings and table headers in help and previews** are the theme's text in bold: in Default and High contrast they were the buttons' blue, 2.36:1 on the dark screen.
- **Every screen meets WCAG contrast in every preset**, measured on everything drawn: placeholders, disabled options (a configuration group's title, a decision shown with F2), a select's arrow, unchecked radio buttons and checkboxes, and the focus border (now the highlight color) were below it.
- **Every screen opens with the focus where the keys act** -- the list, its filter or the first field; only help and previews scroll.
- **The application's icon** (`src/adrpy_tui/icon.png`, kept out of the wheel) heads the README and every page under `doc/`; each page opens with a line to the README and the other pages, and the README lists them all (`tests/test_docs.py` also checks that no relative link is broken).
- **adrpy-ai's validated range**: adrpy-tui requires `adrpy-ai>=0.1.dev0,<0.2` (the 0.1 series, development builds included) and, when an adrpy-ai outside it is installed later, says so on the main menu ([ADR003V01](doc/adr/ADR003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md)).
- **Every change goes through adrpy** ([ADR001V01](doc/adr/ADR001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md)), run from the TUI's own interpreter ([ADR003V01](doc/adr/ADR003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md)).
- **The UI speaks the eleven languages adrpy supports** ([ADR005V01](doc/adr/ADR005V01R01-the-ui-is-localized-in-adrpy%27s-languages-through-json-language-packs,-chosen-on-first-run,-while-adrpy%27s-own-responses-stay-in-english.md)). adrpy's own messages stay in English. The ten non-English packs have not been reviewed by native speakers yet.
