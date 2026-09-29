# The on_top guards are kept by an AST test, by design

Each of the 29 action handlers starts with if not on_top(...): return; tests/test_textual_names.py checks that every one does. A handler added without it fails that test; nothing else enforces it.
