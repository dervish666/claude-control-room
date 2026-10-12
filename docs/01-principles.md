# 01 Principles

## The problem

Once you run more than two or three Claude Code sessions, three things go wrong.

- **Knowledge evaporates.** A session works out why the build breaks on Tuesdays, then ends. Next week a fresh session works it out again, or worse, tries the fix that already failed.
- **Questions get stranded.** Five sessions each end a turn with "shall I deploy?" in five terminals. You answer two and forget three.
- **Nobody knows what is open.** You remember asking for something on Monday. Which session? Did it finish? Was it pushed?

Every fix I tried that added another place to look (a todo app, a notes file per repo, a channel) made it worse. The fix that worked was removing places.

## Rule 1: one source of truth

The vault is a folder of markdown notes that every session reads and writes. It holds anything that should outlive the session that learned it:

- **project notes**, one per project: current state, open items, a short log of sessions with links to the detail
- **journal entries**: what happened in a session, what failed and why
- **topic notes**: research and reference that more than one project uses
- **daily notes**: which sessions ran today

A session starts by reading the index and the relevant project note, and ends by writing a log line and a journal entry. That loop is the whole mechanism. It works because it is the only place: if a decision is not in the vault, it was not made.

Docs [02](02-vault.md), [03](03-vault-mcp.md) and [04](04-sync.md) cover the layout, the access path and sync.

## Rule 2: one point of communication

I talk to one session, the **dispatcher**. It does no project work. It:

- routes each instruction to the right **manager** (one Claude Code session per repo), with a task id
- keeps a **ledger** of open tasks
- hears back from managers in a fixed format: `DONE`, `NEEDS OWNER` or `FAILED`
- pushes my phone only for `NEEDS OWNER`, batched, once per question
- relays my answers back word for word

Managers plan and delegate to subagents. They never talk to each other and never to me unless I open their terminal; everything goes through the dispatcher.

Doc [05](05-dispatcher-manager.md) has the protocol.

## How the two fit

The ledger and the vault answer different questions. The ledger says **what is open right now and who is waiting on whom**, and it only holds open tasks. The vault says **what happened and what we know**, and it keeps everything. When a task closes, its story goes to the vault through the manager's session log, and its row leaves the ledger.

So there is still exactly one place for each kind of fact. That is the rule. "One place" does not mean one file.

## What you can skip

Both rules work without anything else in this repo. Model routing, the Jev classifier, the hooks and the office dashboard each fix a smaller problem. Start with the vault, add the dispatcher when you have more than three sessions, and add the rest when you feel the specific pain each one solves.
