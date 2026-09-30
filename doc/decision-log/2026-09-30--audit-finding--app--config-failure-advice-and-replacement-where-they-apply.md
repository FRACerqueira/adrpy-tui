# The repair-by-hand advice showed for any failure, and an unreadable install config could not be replaced

**Front:** TUI adherence to the current CLI contract (round 6 confirmation) | **Severity:** Low | **Resolution:** Direct | **Round:** 6

Round 5 added the advice to repair .adrpy.json by hand for every failure but config-not-found: io-error and the tui-* codes say nothing of the file, and for config-file-empty adrpy says to remove it. The install-level editor offered --seed and --language only when no file existed, though both replace an unreadable one without reading it.

Fix: the advice shows only for a config-* refusal other than config-file-empty; the install editor offers the replacement next to a config-* refusal only (the second opinion found it first offered after a timeout too, beside a valid file). Red then green in tests/test_ui.py.
