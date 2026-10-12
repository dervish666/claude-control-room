# Vault conventions

{{NAME}}'s knowledge base at `{{VAULT_PATH}}`. Every Claude session reads and writes here for continuity across sessions. The global `~/.claude/CLAUDE.md` says when to log; this file says how.

## Structure

| Path | Purpose | Filename |
|---|---|---|
| `index.md` | Catalogue of every project and topic note. Read first. | |
| `log.md` | Append-only record of structural vault changes | |
| `projects/` | One note per project: state, open items, session log | `{Project Name}.md` |
| `journal/` | Claude's entries about each session, first person | `YYYY-MM-DD-{morning,afternoon,evening,late}.md` |
| `topics/` | Evergreen research and reference | `{Topic}.md` |
| `daily/` | Which sessions ran each day | `YYYY-MM-DD.md` |
| `sources/` | Ingested external material | `{Title}.md` |
| `templates/` | Note templates. Do not edit unless asked. | |

## Project to repo map

The `session-log` skill uses this to pick the project note from the working directory. Unknown directory: ask.

| Directory contains | Project note |
|---|---|
| `acme-api` | `projects/Acme API.md` |
| `blog` | `projects/Blog.md` |

## Writing conventions

- Use `[[wikilinks]]` for every cross-reference, and check the target exists.
- Search before creating. Update an existing note rather than making a near-duplicate.
- Frontmatter is required on new notes: at least `tags` and `type`. Journals and dailies also need `date`.
- Project notes: one-line session-log entries, newest at the top of `## Recent Session Log`, at most 300 characters. Depth goes in the journal.
- Journal entries: honest and reflective, first person as Claude. Anything only {{NAME}} can verify goes under `## Not verified`.
- Topic notes: add a dated section when new findings land.

## Placement rule

Read a note before editing it. Insert session-log entries directly under the `## Recent Session Log` heading with a targeted edit. Never append to the end of the file (it lands below the footer) and never prepend to the file (it lands above the title).

## Ingesting a source

1. Create a note in `sources/` from the source template.
2. Summarise it and pull out the key points.
3. Update every project or topic note it touches: add links, revise claims it contradicts.
4. Add new notes to `index.md` and a line to `log.md`.

## Secrets

None in this vault. If a session finds one, it says so and does not copy it anywhere.

## Git

Local repository, no remote. Commit at the end of every session.
