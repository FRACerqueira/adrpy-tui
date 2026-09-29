# Round 3's choice to drop every invisible character from a field did not hold

Retracts 2026-09-29--audit-finding--text--invisible-characters-filled-into-fields.md and 2026-09-29--audit-finding--text--pasted-controls-hidden-from-the-confirmation.md: their fix dropped every Cf character. Round 4 found it changed text the person never typed; field_text now drops only the bidirectional controls and the tag characters (2026-09-29--audit-finding--text--only-bidirectional-controls-dropped.md).
