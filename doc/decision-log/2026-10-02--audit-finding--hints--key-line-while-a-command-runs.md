# While a command ran the key line named keys that do nothing and not Leave

**Front:** Usability and docs against code (Fable) | **Severity:** Medium | **Resolution:** Direct | **Round:** 8

With the body disabled during a write, the line still named Tab, Ctrl+R and Esc, and once Leave appeared it was neither focused nor named. The line is now empty while the command runs, and Leave takes the focus and is named once it appears (3693e5d). Red then green: tests/test_hints.py::test_while_a_command_runs_the_line_names_only_leave_once_it_can.
