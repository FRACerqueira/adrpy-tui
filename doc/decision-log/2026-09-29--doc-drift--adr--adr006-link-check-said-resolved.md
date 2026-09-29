# ADR006V01 said a link is checked after resolving it, which the code does not do and must not do

**Front:** Command fidelity and untrusted input (Opus) | **Severity:** Low | **Resolution:** Escalated | **Round:** 2

Resolving opens the target, which may be on another machine. ADR006V02 says what is done: lexical, then lstat folder by folder.
