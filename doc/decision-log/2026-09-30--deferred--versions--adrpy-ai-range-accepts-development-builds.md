# The adrpy-ai range still accepts the development builds from before the contract change

**Reopen-when:** adrpy-ai 0.1.0 is published on PyPI

pyproject.toml requires adrpy-ai>=0.1.dev0,<0.2, which admits development builds older than the contract this TUI follows (.adrpy.json, the index, the retired fields), so the start-up check cannot catch one. Raising the floor now would refuse the editable development install, which reports 0.1.dev335.

Deferred by the project owner: the floor is revisited when adrpy-ai 0.1.0 is published.
