# The WCAG sweeps measured with the tests' own copy of the contrast formula

**Front:** Test adequacy (Fable) | **Severity:** Medium | **Resolution:** Direct | **Round:** 1

core/contrast.py, used by the color note, could drift unseen. The tests now use the production formula, checked on known values (21:1, 4.54:1, ...); a doubled ratio fails 5 tests.
