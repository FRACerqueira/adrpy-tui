# A left editor is forgotten when the TUI restarts

Once the person stops waiting, the editor's process is kept in the client's list and writes are refused until it closes. A new TUI started while it is still open has no record of it: it would allow a write or a second editor on the same file. Closing this would need state kept across runs. Accepted by the owner as a design limit (ADR0007V01).
