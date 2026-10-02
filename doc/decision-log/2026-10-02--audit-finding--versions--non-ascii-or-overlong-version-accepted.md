# A version in digits other than ASCII, or thousands of digits long, was accepted

**Front:** Resilience and untrusted input (Sonnet) | **Severity:** Low | **Resolution:** Direct | **Round:** 10

order() matched \d without re.ASCII and had no length bound: from PyPI, "٣.0" outranked 0.2.1, and a 4000-digit version was shown whole on the main menu. A version is now ASCII digits and at most 64 characters (74102ac). Red then green: tests/test_updates.py::test_a_version_with_digits_other_than_ascii_or_too_long_is_refused and ::test_a_version_from_pypi_with_other_digits_is_never_offered.
