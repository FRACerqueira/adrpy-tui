# forms.md said turning the check on asks PyPI at once, also when it already had

**Front:** Stability and concurrency (Opus) -- round 11, on round 10's fixes | **Severity:** Low | **Resolution:** Escalated | **Round:** 11

PyPI is asked at most once per run, so turning the check off and on again in a run that started with it on asks nothing, and a failure stays said for the rest of the run; forms.md said every turn on asks at once. The owner chose to keep once per run and correct the text: turned on during a run that started with it off, the check asks at once (a73cdcb).
