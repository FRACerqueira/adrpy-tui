# On Windows a value with a quote and a line break was shown escaped twice

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

display_command quoted list2cmdline's output again for a value with a line break, so a"b<LF>c read back as a\"b<LF>c. Such a value is now quoted from itself (_quoted). Also found by the test-adequacy front. Covered by a CommandLineToArgvW round trip over every value up to 4 characters in tests/test_client.py.
