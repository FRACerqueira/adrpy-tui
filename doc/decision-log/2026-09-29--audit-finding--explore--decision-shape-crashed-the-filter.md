# A decision of an unexpected shape ended the app on the next key in its filter

**Front:** Resilience (Sonnet 5.5) | **Severity:** Medium | **Resolution:** Direct | **Round:** 4

A header that is not an object, or a name that is not text, was shown as a failure note, then raised again in the filter's own handler. Closed as a class: decisions.listed (core/decisions.py) reads explore's decisions into one shape wherever they enter (explore, the detail, the form and its picker, migrate), and leaves out one whose name or path is not text. Swept: every other use of adrpy's data in ui/ runs inside read. Covered by tests/test_ui.py::test_a_decision_of_an_unexpected_shape_never_ends_the_app.
