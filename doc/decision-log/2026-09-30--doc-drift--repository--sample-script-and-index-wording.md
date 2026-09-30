# The sample script labelled a revise R01, and the docs said adrpy regenerates the index at every write

**Front:** Documentation versus code (round 5) | **Severity:** Low | **Resolution:** Direct | **Round:** 5

scripts/make_sample_repo.py labelled the revise it runs R01, where revise on an R01 creates R02 (tests/test_sample_repo.py already expected R02). README and CHANGELOG said adrpy regenerates its decisions index at every write, where it is every command that writes a decision (and config). Fixed in the texts; the sample keeps its explicit --lenrevision 2, which makes it independent of adrpy's defaults.
