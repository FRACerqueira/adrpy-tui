# The lists of per-user settings and the security scope missed the update check

**Front:** Usability and docs against code (Fable); the first start also raised by Resilience and untrusted input (Sonnet) | **Severity:** Low | **Resolution:** Direct | **Round:** 10

README, SECURITY.md and architecture.md listed what state.json holds without the two settings (README and SECURITY without the editor either); SECURITY's scope did not name the one outbound request; no doc said the first start checks too, before any screen that could turn it off, as ADR0008V01 decides. All now say so, SECURITY naming the HTTPS GET and that it sends nothing of the person's or the repository's (74102ac).
