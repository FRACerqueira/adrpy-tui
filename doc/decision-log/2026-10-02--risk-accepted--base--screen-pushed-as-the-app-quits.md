# A screen pushed in the same tick as the app quits raises NoMatches in its on_mount

Found by the round 8 stability pass: an on_mount that queries a widget its compose yields raises NoMatches when the screen is pushed in the same tick as exit(); about 10 screens have this shape since v0.1.0 (editing.py and editor.py among the new ones). Reached only by a programmatic push followed by exit(), not by keys (the key probes exited cleanly). Accepted by the owner as a known risk, outside the round's scope.
