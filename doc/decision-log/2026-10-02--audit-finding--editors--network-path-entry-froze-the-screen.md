# A network share on PATH froze the screen about 21 s while looking for the editor

**Front:** Resilience and untrusted input (Sonnet) | **Severity:** Low | **Resolution:** Escalated | **Round:** 8

located() looked at every absolute PATH entry on the UI thread; an unreachable share (off the VPN) took 21.06 s on the first look. The owner chose (a): skip network (UNC) entries and keep the lookup for the session per PATH; the Editor screen looks again as it opens (de33e9a). Tests: test_a_network_path_entry_is_never_touched, test_the_lookup_is_done_once_per_path, test_the_editor_screen_lists_an_editor_installed_while_the_tui_ran.
