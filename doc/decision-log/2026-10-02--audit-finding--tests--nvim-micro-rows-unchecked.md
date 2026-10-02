# Two rows of the editor table were never checked

**Front:** Test adequacy by mutation (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 8

test_each_editor_waits_for_its_file_to_be_closed listed 10 of the 12 editors: dropping terminal=True from nvim or micro survived the full suite, which would have started them as window editors with no terminal. Both rows added (de33e9a).
