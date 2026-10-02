# The update check had no deadline for the whole answer

**Front:** Resilience and untrusted input (Sonnet) | **Severity:** Low | **Resolution:** Direct | **Round:** 10

TIMEOUT bounds each socket read, not the exchange: a server sending a byte every half second held the check (thread and socket) for the whole run, up to the 4 MiB limit. The answer is now read in read1 chunks under a 15-second DEADLINE (74102ac); quitting never waited, the thread being a daemon. Red then green: tests/test_updates.py::test_an_answer_that_trickles_in_is_given_up_at_the_deadline; positive control against a real local HTTP server, plain and chunked.
