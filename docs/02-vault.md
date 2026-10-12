# 02 The vault

A folder of markdown files, `~/vault` in my setup. Obsidian is a nice viewer for it, with a graph and backlinks, but nothing here needs Obsidian. Claude reads and writes plain markdown with YAML frontmatter.

## Layout

| Path | Holds | Filename |
|---|---|---|
| `index.md` | Catalogue of every project and topic note. Read first. | |
| `log.md` | Append-only record of structural vault changes | |
| `projects/` | One note per project | `{Project Name}.md` |
| `journal/` | Claude's entries about each session | `YYYY-MM-DD-{time-of-day}.md` |
| `topics/` | Evergreen research and reference | `{Topic}.md` |
| `daily/` | Which sessions ran today, links out | `YYYY-MM-DD.md` |
| `sources/` | Ingested articles, papers, docs | `{Title}.md` |
| `templates/` | Note templates | |
| `CLAUDE.md` | Vault conventions for any session working inside it | |

Starter versions of all of these are in `templates/vault/`.

## The project note is an index, not a diary

This is the rule that took longest to learn. A project note gets read at the start of every session on that project, so it must stay glanceable. Its shape:

1. `# Project`, one-line description
2. `## Current State`: version, test counts, key facts. Refreshed every session.
3. `## Open / Pending`: curated open items
4. `## Historical Summary`: one line per older era
5. `## Recent Session Log`: newest first
6. `## Reference`: config, paths, durable facts
7. `## Related`: wikilinks

A session-log entry is **one line, at most 300 characters**: what changed and where to read about it.

```markdown
- [2026-10-12] **Moved auth to middleware, 3 routes left** · a1b2c3d · [[journal/2026-10-12-afternoon]]
```

The why, the dead ends and the root-cause trace go in the journal entry. One exception: a landmine that must survive nobody opening the journal (a credential to rotate, a deploy not to repeat) gets one sub-bullet, at most 150 characters, starting `⚠`.

I set a character budget because "keep it short" failed. A 2,500-character paragraph is technically one line.

## Placement: read, then insert at the top of the log

The single biggest cause of note rot: a session appends its entry to the end of the file, below `## Reference` and `## Related`, and the log splits in two. The opposite mistake, prepending to the file, lands the entry above the title.

So: read the note, then make a targeted edit anchored on the `## Recent Session Log` heading, putting the entry directly under it. The `session-log` skill does this.

## Journal entries

Written at session end in the first person, as Claude. Honest and reflective: what worked, what did not, what surprised it, what a future session should know. Frontmatter carries `date`, `tags` and `type: journal`.

Two sessions writing the same evening will collide on `2026-10-12-evening.md`. Check the path first, and if another session holds it, suffix yours with the project slug.

Anything only a person can check (a real device, a login, a render the harness cannot produce) goes under a fixed `## Not verified` heading, one bullet per item, saying what to check and how.

## Topic notes

When a session researches something useful beyond today, it writes or updates a topic note. Update, never duplicate: add a dated section to the existing note.

## Curation

Living notes rot by accretion. My triggers for a restructure pass:

- a project note past about 20 KB, or a log with more than 10 to 12 entries
- anything a month since its last pass

Before condensing, measure which section is big (it is often Reference, not the log), and grep every landmine in the entries you are about to delete. Once, an entry due for roll-off was the only record of a production token that still needed rotating.

## Git

Make the vault a local git repo and commit at the end of every session. It is the undo button for a bad bulk edit or a clobbered journal.

## Secrets

Keep secrets out of the vault. If you must keep them there, put them in one folder that is excluded from sync, from git and from any remote access path, and decide that **before the first commit**. A secret that lands in git history stays there.
