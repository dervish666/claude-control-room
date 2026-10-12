# 03 Reaching the vault through MCP

Claude Code can read and write the vault with its own file tools. That works, and it is the fallback. I use an MCP server instead, for three reasons.

1. **Search that ranks.** A server can keep a full-text index (SQLite FTS5 with BM25 ranking in mine) and answer "what do we know about rate limits" across hundreds of notes in one call. Grep returns every line containing the word.
2. **Links as data.** Backlinks and related-note lookups come from a maintained wikilink graph rather than a grep for `[[name]]`.
3. **Edits that respect structure.** A section-patch tool ("insert under this heading") makes the placement rule in [02](02-vault.md) easy to follow. A raw file write makes it easy to break.

## What to look for

Any Obsidian MCP server will do. Check it has:

| Need | Why |
|---|---|
| Read note, read several notes | Session start |
| Ranked search | Finding prior work |
| Patch or insert under a heading | Session-log placement |
| Write with an existence check, or a separate create | Journals collide by design |
| Recent notes | "What happened this week" |
| Backlinks or related notes | Cross-referencing |
| A lint for broken links and sync conflict files | Curation |

Register it once, under one name:

```bash
claude mcp add --scope user vault -- <your server command>
```

Then name it in your CLAUDE.md so every session prefers those tools over raw file access. The template uses `mcp__vault__*`; change it to whatever name you register.

## Gotchas I hit

- **Whole-file writes overwrite silently.** My server's write tool replaced a file with no warning. A session overwrote another session's journal from earlier the same day. Check the path is free first, every time.
- **Keep the index out of the vault.** If the vault syncs between machines, a SQLite index inside it syncs too and corrupts. Put it under `~/.cache/`.
- **Watch the watcher.** My server's file watcher silently watched nothing after a library upgrade, so the index went stale while every search "worked". If search stops finding new notes, check the watcher before the query.
- **One registration.** I once had the same server registered twice under two names. Both sets of tools showed up and sessions picked between them at random.

## Remote access (optional)

I also expose the vault to Claude on the web and phone, through the same server in HTTP mode behind an authenticated tunnel. If you do this:

- Put an OAuth or access-token layer in front of it. Never a bare public endpoint.
- Keep secrets off the machine that serves it.
- Remember prompt injection: a web session that reads a poisoned page could be steered into reading notes and sending them out through another connector. Read-only is the safe default.
- Local sessions should still use the local server, which is faster and does not depend on the tunnel.
