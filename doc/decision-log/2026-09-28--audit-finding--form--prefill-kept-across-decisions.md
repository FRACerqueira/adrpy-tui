# version and supersede kept the first decision's scope and domain when another was chosen

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Direct | **Round:** 1

The prefill filled only empty fields. Fixed: a value filled from a decision is replaced by the next choice's; one the person typed stays. Covered by tests/test_ui.py::test_choosing_another_decision_replaces_what_the_first_one_filled_in.
