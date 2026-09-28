"""`adrpy-skills list`: its own screen (ui/skills.py), every skill of
every provider with whether it is installed."""

VIEW = "skills-list"
PATH_FLAG = "path"
FIELDS = ()
# Flags adrpy-skills has that this screen deliberately does not offer: it
# lists them all.
NOT_OFFERED = {"provider": "the screen lists every provider", "skill": "the screen lists every skill"}
