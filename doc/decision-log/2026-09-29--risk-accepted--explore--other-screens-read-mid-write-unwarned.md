# Screens other than Check read the repository while a left write runs, without a warning

The detail, explore, the log browser, migrate and the config editors read what may be half-written. Owner's choice (K4 option a): any write they offer is refused (tui-write-still-running) and the result offers Check, which warns; a warning on every screen would need ADR0006V02 revised.
