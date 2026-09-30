# No test held the config editor's fields, choices and length limits to adrpy's own schema

**Front:** TUI adherence to the current CLI contract (round 5) | **Severity:** Low | **Resolution:** Direct | **Round:** 5

The editor's 26 fields matched adrpy's schema, but only by hand: nothing would fail if a field, a choice or a length limit drifted. The fixture config still seeds lenseq 3 and no revision, so no real-CLI test uses the default names; that is left as it is, since the fixture's sizes are what the other tests are written for.

Fix: test_the_config_editor_fields_are_adrpy_s_own compares fields, INT_FIELD_BOUNDS, the separator and casetransform choices and every length limit with adrpy.core.config.
