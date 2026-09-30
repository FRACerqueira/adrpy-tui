# A configuration that is not an object left the start-up screen on a failure note

**Front:** Resilience (Sonnet 5.5) | **Severity:** Low | **Resolution:** Direct | **Round:** 4

repository_read called .get on whatever `config` held. decisions.repository_config reads it as {} when it is not an object, in the app, the config editor and migrate. Covered by tests/test_ui.py::test_a_configuration_that_is_not_an_object_still_reaches_the_menu.
