# The only test of the key line while a command runs raced a 0.3 s timer

**Front:** Test adequacy by mutation (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 9

test_while_a_command_runs_the_line_names_only_leave_once_it_can set READ_TIMEOUT to 0.3 s and asserted an empty line before the Leave panel appeared: 1 failure in 4 runs under load, and one false kill. The panel is now raised by the test itself, the timer out of reach (1532a2e).
