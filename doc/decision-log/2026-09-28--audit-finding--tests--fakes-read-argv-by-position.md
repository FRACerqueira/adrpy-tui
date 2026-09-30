# A test fake still read the adrpy-skills verb from the wrong argument

**Front:** Test adequacy (Fable) | **Severity:** Low | **Resolution:** Direct | **Round:** 1

BlockingOn read argv[4], the bug already fixed in FakeClient. Every fake now reads the command through one helper, conftest.command_of, which also survived the `-P` added to the argv.
