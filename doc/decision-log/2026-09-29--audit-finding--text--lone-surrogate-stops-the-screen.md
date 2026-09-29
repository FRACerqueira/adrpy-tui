# A file name holding a lone surrogate stopped the screen from drawing for the rest of the session

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Medium | **Resolution:** Direct | **Round:** 2

NTFS allows a lone surrogate in a name, and adrpy reports it; written to the terminal it cannot be encoded, and Textual's writer thread died, leaving keys working blind. printable() now shows U+FFFD and visible() <U+D800>. Covered by tests/test_text.py and tests/test_untrusted_text.py (drawn text encoded as UTF-8). Note: the killed test's own message holds the surrogate, which the xdist workers cannot pass on, so that mutation is seen failing only in a serial run.
