"""Per-user state: the interface language and the last item selected in
each menu.

A file that can't be read starts empty, and one that can't be written is
skipped, without interrupting the person: losing it only means choosing the
language again on the next run.
"""

import json
import os
from pathlib import Path


def default_state_path():
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    else:
        base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    return base / "adrpy-tui" / "state.json"


class UserState:
    def __init__(self, path):
        self._path = Path(path)
        data = self._load()
        language = data.get("language")
        self.language = language if isinstance(language, str) else None
        items = data.get("last_menu_item")
        self._items = {k: v for k, v in items.items() if isinstance(v, str)} if isinstance(items, dict) else {}

    def _load(self):
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def last(self, menu_id):
        return self._items.get(menu_id)

    def remember(self, menu_id, item_id):
        self._items[menu_id] = item_id
        self._save()

    def set_language(self, language):
        self.language = language
        self._save()

    def _save(self):
        data = {"language": self.language, "last_menu_item": self._items}
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass
