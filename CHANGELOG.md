# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project intends to follow [Semantic Versioning](https://semver.org/) once it reaches `1.0.0`.

## [Unreleased]

### Added

- **The first screens.** The header, the language choice on first run, the main menu with every adrpy and adrpy-skills command grouped by use, the `new`, `approve`, `reject`, `undo`, `version`, `revise`, `supersede` and `init` forms, the config and install-level config editors, the guided migrate builder, the `log` form, the AI skills screens (list, install, remove), change repository, the explore screen (every decision, then one decision's detail with the commands its state allows) and the check screen (a decision picker lists every decision with its label, the ones the command cannot take disabled), the confirmation screen showing the exact command line about to run, the result screen and the help of every command. Every command of adrpy and adrpy-skills has its screen.
- **Appearance presets**: Default (dark), Light and High contrast, previewed live and kept per user, with any color customizable on top of them.
- **Every change goes through adrpy** ([ADR001V01](doc/adr/ADR001V01R01-every-read-and-change-goes-through-the-adrpy-cli-as-a-subprocess,-and-the-tui-decides-on-the-json-code-and-data-only.md)), run from the TUI's own interpreter ([ADR003V01](doc/adr/ADR003V01R01-adrpy-ai-is-a-declared-dependency-run-through-the-tui%27s-own-interpreter,-and-adrpy-tui-is-not-published-until-adrpy-ai-is-on-py-pi.md)).
- **The UI speaks the eleven languages adrpy supports** ([ADR005V01](doc/adr/ADR005V01R01-the-ui-is-localized-in-adrpy%27s-languages-through-json-language-packs,-chosen-on-first-run,-while-adrpy%27s-own-responses-stay-in-english.md)). adrpy's own messages stay in English. The ten non-English packs have not been reviewed by native speakers yet.
