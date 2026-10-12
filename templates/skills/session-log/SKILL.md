---
name: session-log
description: "Write a structured session summary to the notes vault. Detects the current project, adds a one-line entry to the project note, writes a journal entry, and updates the daily note. Use when ending a session, or when the user says 'log this', 'session summary', 'write session notes', 'update vault', or 'session-log'."
---

# Session log

Write this session's summary to the vault at `{{VAULT_PATH}}`.

## Tools

Use the `mcp__vault__*` tools (rename to your notes MCP server) for every read and write, so the search index and link graph stay in sync. Shell commands (`ls`, `git`) are fine for checks and commits. Without an MCP server, use Read and Edit, never a blind Write.

## Before any write: whole-file writes overwrite silently

A whole-file write replaces the file with no warning. Journal filenames are designed to collide: two sessions on the same afternoon both want `YYYY-MM-DD-afternoon.md`. So check the path exists before writing it, every time:

```bash
ls {{VAULT_PATH}}/journal/YYYY-MM-DD-afternoon.md 2>/dev/null && echo "OCCUPIED"
```

If another session holds it, write yours as `YYYY-MM-DD-{time-of-day}-{project-slug}.md`. Use patch or append tools for notes that already exist.

## Core principle: the project note is an index, not a diary

The project note is read at the start of every session on the project, so it must stay glanceable. Depth goes in the journal; the project note points at it.

## Step 1: Detect the project

Match the working directory against the project map in `{{VAULT_PATH}}/CLAUDE.md`. No match: ask which project this was.

## Step 2: Work out what happened

From the conversation:

- what was worked on, and what shipped (versions, commits, merged branches)
- what failed and why (headline here, depth in the journal)
- decisions made and their reasons
- landmines a future session must know (a fix that must not be undone, a credential to rotate)
- anything only a person can verify (a device, a login, a real render)

## Step 3: Keep the note's structure

If the note has an established structure, keep it. Otherwise use this order, creating any missing section:

1. `# Project`, one-line description
2. `## Current State`: refresh every session
3. `## Open / Pending`: remove what shipped, add what surfaced
4. `## Historical Summary`
5. `## Recent Session Log`
6. `## Reference`
7. `## Related`

## Step 4: Write the entry

One entry, **at most 300 characters**, directly under `## Recent Session Log`, above the previous newest entry:

```markdown
- [YYYY-MM-DD] **headline, 12 words or fewer** · commit or version · [[journal/entry-name]]
```

The line says what changed and where to read about it. Not why, not how. One optional sub-bullet, at most 150 characters and starting `⚠`, for a landmine that must survive nobody opening the journal.

Read the note first and anchor the edit on the heading text. Never append to the end of the file (below the footer, splitting the log) and never prepend to the file (above the title).

## Step 5: Curate

- Refresh `## Current State` and `## Open / Pending`.
- If the log holds more than 10 to 12 entries, or the note passes about 20 KB, condense the oldest era into one line under `## Historical Summary`.
- Before condensing, measure which section is big. It is often Reference, and the fix there is a topic note.
- Before deleting a condensed entry, grep each landmine, credential pointer and open decision in it against the vault. Anything that lives only in that entry moves first.

## Step 6: Journal entry

Write `journal/YYYY-MM-DD-{time-of-day}.md` from the journal template, after the collision check above. First person as Claude: what happened, what worked, what did not, what surprised you, what a future session should know. Link the project note and any earlier journal entries it follows from. Anything only a person can check goes under `## Not verified`, one bullet each with what to check and how. No heading if there is nothing.

## Step 7: Daily note

Open `daily/{today}.md`, creating it from the daily template if missing, and add one bullet for this session under `## Conversations with Claude`, linking the journal entry.

## Step 8: Commit

```bash
git -C {{VAULT_PATH}} add -A && git -C {{VAULT_PATH}} commit -m "session log: <project>, <headline>"
```

The vault is a local repository. Committing every session is what makes a bad edit recoverable.

## Step 9: Confirm

Say what was written and where, in two lines.
