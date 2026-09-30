# A decision's detail offered the actions of its old state while reading it again

**Front:** Async event ordering in one session (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 3

Back on the detail after a command run from it, the old actions stayed on offer: approve could be chosen again on a decision just approved. They are disabled until the re-read answers. Swept the four screens with on_screen_resume: only the detail offers actions on what it read. Covered by tests/test_async_screens.py::test_a_detail_offers_no_action_while_it_reads_its_decision_again.
