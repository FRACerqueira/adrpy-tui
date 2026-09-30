# No test checked that No or Esc on the confirmation runs nothing

**Front:** Test adequacy (Fable) | **Severity:** Medium | **Resolution:** Direct | **Round:** 1

Running the command whatever the answer passed all 390 tests (mutation reproduced on a copy: 389 passed, the one failure unrelated). Covered now by tests/test_ui.py::test_no_or_esc_on_the_confirmation_runs_nothing; the mutation fails 2 tests.
