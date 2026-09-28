<img src="../src/adrpy_tui/icon.png" width="160" alt="adrpy-tui icon">

[← README](../README.md) · [Architecture](architecture.md) · [Forms](forms.md) · **Manual test checklist** · [Decisions](adr/)

# Manual test checklist

What the automated tests cannot check -- a real terminal's rendering, keys
and colors, and how the screens feel -- walked through before a release,
screen by screen. Build the repositories first:

```bash
python scripts/make_sample_repo.py <folder> --reset --extra 40
```

`<folder>/sample` has decisions in every state (and 40 more, for several
pages), `legacy` hand-written files for migrate, `broken` two files with the
same number for check, and `empty` no config. After a round, `--reset` puts
everything back.

Run it in each terminal the release supports (Windows Terminal, conhost,
macOS Terminal, a Linux terminal), with `adrpy-tui --path <folder>/<repo>`.

## Every screen

- [ ] The banner's double rules and letters are whole, in the banner color.
- [ ] The key line at the bottom matches the keys that work.
- [ ] `Esc` goes back one level; on the main menu it leaves.
- [ ] A list longer than eight rows shows "Items … · page … · PgUp/PgDn";
      `PgUp`, `PgDn`, `Home` and `End` move as it says.
- [ ] Without touching the mouse, each screen opens with the keys acting
      where they should: on a list screen the arrows move the list (or,
      in its filter, typing filters while the arrows still move the list);
      on a form, typing goes into the first field; only a command's help
      and a preview scroll with the arrows. Check the screens whose content
      arrives after they open too: check, migrate, the skills list, the
      configuration and a decision's detail.
- [ ] In every preset, the highlighted row stands out from the others at
      a glance -- its whole row in the highlight color, its text readable
      on it; with the focus elsewhere (a list's filter, a form's other
      field), it stays visible, quieter; the row under the mouse is
      underlined and never mistaken for the highlighted one.

## Keys and previews (`sample`)

- [ ] F2 and F3 reach the program in this terminal. On a Mac laptop they
      need Fn unless the system is set otherwise; VS Code's integrated
      terminal may take some F keys itself.
- [ ] F3 on explore, the picker, check's errors, a result, migrate's files
      and the log browser opens the rendered file; a link to another ADR
      opens it; Esc comes back.
- [ ] Keys: give Run another key; the key line of a form names it and it
      runs; a key another action has is refused.

## First run and appearance (`empty`)

- [ ] With no state file (`%APPDATA%\adrpy-tui\state.json` removed on
      Windows, `~/.local/state/adrpy-tui/state.json` elsewhere), the first
      screen is the language choice, the system's language highlighted.
- [ ] The main menu disables Decisions, Explore and validate and Decision
      log, each saying it needs an initialized repository.
- [ ] Language: another language rebuilds every screen in it.
- [ ] Appearance: each preset previews as the cursor moves; `Esc` restores
      the saved one; Light and High contrast are readable, the highlighted
      menu item included.
- [ ] Customize colors: a color shows at once; a hard-to-read one is warned
      about; "Back to the preset" and "Restore every color" undo it.

## Repository (`empty`, then `legacy`)

- [ ] Initialize `empty` in another language: the menus come alive, the
      labels are that language's.
- [ ] Configuration: every group lists its fields; editing marks them;
      `Ctrl+R` confirms one `config` with only the changed fields.
- [ ] Migrate `legacy`: the proposed pattern reads the number and title of
      the sample; Preview lists every file; Migrate confirms the two
      commands and migrates.

## Decisions (`sample`)

- [ ] New decision: scope and domain suggest the repository's values
      (`→` accepts); a forbidden character can't be typed.
- [ ] Approve, Reject, Undo, New version, New revision, Supersede: the
      picker lists only what each takes, by default; switching "Only the
      available ones" off shows the rest disabled.
- [ ] The confirmation shows the exact command; the result shows adrpy's
      answer.

## Explore and validate (`sample`, `broken`)

- [ ] Explore: the columns line up, in every language; the folder column
      and the folder select show ADR003, which lives in `backend/`; a
      decision's detail shows its content and the actions its state allows,
      each opening its form with the decision chosen.
- [ ] After an action, the detail and the list show the change.
- [ ] Check on `broken`: the errors list, each hint below it; on `sample`,
      "No inconsistencies".

## Decision log and AI skills (`sample`)

- [ ] New entry: the fields each classification takes appear with it.
- [ ] Browse the entries: the classification select filters them; Enter
      opens one rendered.
- [ ] AI skills: install for this repository, list shows it installed,
      remove takes it away. (Installing in the user folder writes to your
      real home.)

## Help and change repository

- [ ] Command help: every command's contract, adrpy's descriptions in
      English.
- [ ] Change repository: the tree lists folders only; choosing one, then
      `Ctrl+R`, works on it from then on.
