# Links to files with accents or spaces do open from a preview

The resilience pass reported that such links never open, the href arriving percent-encoded. Re-run through the real click path, `decisão 2.md` opened: Textual 8.2.8 unquotes the href (`_markdown.py:1114`). The pass had called follow_link with the raw href, skipping that step. Its related claim that markup cannot reach the notification fell with it (see notification-renders-markup).
