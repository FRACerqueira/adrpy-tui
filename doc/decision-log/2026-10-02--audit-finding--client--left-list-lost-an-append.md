# The list of left writes and editors lost an append to a concurrent check

**Front:** Stability and concurrency (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 8

Client.still_writing() read, filtered and rebuilt _left without a lock while a worker appended to it: an append landing in between was lost (11 to 15 of 400,000 in a stress run, 3 of 3), and a write or a second Edit would then have been allowed while the editor stayed open. Not reached from the keyboard. Both sides now hold one lock (de33e9a). Red not kept as a test: with the fix that stress run is quadratic; tests/test_client.py::test_a_left_editor_is_never_lost_to_a_check_reading_the_list_at_once checks both sides hold the lock.
