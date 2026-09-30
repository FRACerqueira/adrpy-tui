# The log browser used folderlog as typed, could list the decisions folder, and hid a folder it could not list

**Front:** TUI folders, links and exclusions (round 7) | **Severity:** Low | **Resolution:** Direct | **Round:** 7

With `folderlog: doc/adr.` (Windows opens doc\adr) the browser listed the decisions as log entries, where adrpy refuses that config; a subfolder it could not list vanished without a word. The log browser, migrate and explore now share core/files.repository_folder: the folder normalized, checked inside with no link on the way, then resolved; the browser lists nothing for a log folder that is, holds or lies in the decisions folder, and names a folder it cannot list (not one that does not exist yet). The second opinion caught two faults of the first version before commit: the highlighted entry's line compared the resolved folder with the one as typed and a `..` in folderlog ended the app, and a log folder not created yet read as one that cannot be listed.
