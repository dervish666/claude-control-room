# 05 Dispatcher, managers, agents

Three layers, each with one job.

| Layer | What it is | Does | Never does |
|---|---|---|---|
| Dispatcher | One Claude Code session, `--agent dispatcher` | Routes your instructions, keeps the ledger, alerts you, relays answers | Project work, verifying results |
| Manager | One session per repo, `--agent manager` | Plans, briefs subagents, verifies their results, reports | Edits files itself (it has no Edit or Write tool) |
| Agents | Subagents a manager spawns | The actual building, research, debugging, writing | Talk to you or the dispatcher |

The agent files are in `templates/agents/`. Both depend on Claude Code features that are recent: `claude agents --json`, `claude --bg`, cross-session `SendMessage` with `notify_when_idle`, and the `PushNotification` tool. I run 2.1.29x.

## Starting it

```bash
# once, in any directory you like
claude --agent dispatcher -n dispatcher
```

The dispatcher starts managers itself when an instruction needs one:

```bash
cd <repo main checkout> && claude --bg --agent manager -n <repo> "<task brief>"
```

That is normal permission mode. A background manager in normal mode stops and waits at every permission prompt, so you will want either a good `permissions.allow` list or bypass mode. See [12](12-risks-and-costs.md) before choosing bypass.

## The protocol

**Task ids.** The dispatcher numbers every instruction it sends: `T-12 from Owner: add rate limiting to the login route`. Your words go through unchanged.

**Reports.** A manager ends every turn the dispatcher started with one message to the dispatcher. The first line starts with one of:

- `DONE T-12 acme-api: ...`
- `NEEDS OWNER T-12 Q-3 acme-api: <one-line question>`
- `FAILED T-12 acme-api: ...`

then at most eight lines: repo, branch, pushed or not, what was verified and what was taken on trust.

**Questions.** Numbered per session (Q-1, Q-2), one decision each. A `NEEDS OWNER` carries `answer: relay` (you can answer through the dispatcher) or `answer: in session` (it needs your hands: a login, a 2FA code, a secret).

**Alerts.** Only `NEEDS OWNER` pushes your phone. One push per question, ever. Others arriving within ten minutes wait and go out as one batch: `3 need you: acme-api Q-3 deploy?, blog Q-1 schema, infra Q-2 dns`. `DONE` and `FAILED` wait until you next talk to the dispatcher.

**Answers.** The dispatcher relays your exact words:

```
OWNER SAID (2026-10-12 14:02, re Q-3): "yes, deploy to staging only"
```

Quoted, never paraphrased, never merged with another answer, never filled in.

## The approval list

Managers may do the work up to these steps, then must stop and ask with `NEEDS OWNER`:

- merging or pushing to main/master or a deploy branch
- deploy, publish or release
- force-push
- discarding uncommitted work or untracked files
- deleting anything outside the repo
- messaging or emailing a person
- spending money or credits
- network or router changes
- secrets
- anything else that cannot be undone

**An instruction is not a yes**, even one that names the step. "Fix it and deploy" gets the fix done and a question about the deploy. The question names the exact command and target, so you know what your yes covers. A yes covers that one action, once.

## Forgery check

Sessions can message each other, so a manager must check that an `OWNER SAID` really came from the dispatcher before acting on a listed step:

1. The sender is named `dispatcher`, and exactly one live session has that name.
2. That session's pid matches the pid in the message's `from` address.
3. The message cites an open question this manager asked and has not closed.

Anything else is refused and reported as `FORGED`. I tested this with a spoofed `OWNER SAID` from a second session; it was rejected.

## The ledger

`~/.claude/dispatcher/ledger.md` is the dispatcher's memory and the only file it writes. It rewrites it whole after each change. Layout (blank template in `templates/dispatcher/ledger.md`):

- next task id
- `## Open`: one row per open task (task, repo, session, sessionId, job id, opened, status, last report, question, pushed)
- `## Aliases`: what you call each repo ("api", "the api", "backend")
- `## Closed today`: cleared each morning

Key rows on sessionId, never on the session name. Names drift.

## Things that bit me

- **Busy can lie.** A session that started a background child (a dev server, a poll loop) stays "busy" for days and never sends its idle notice. The dispatcher flags any busy session whose `updatedAt` in `~/.claude/sessions/<pid>.json` is over two hours old as `stuck?`. Managers must stop their background processes, or name them, before reporting `DONE`.
- **Idle with no report.** If a manager goes idle without the report, the dispatcher reads the tail of its last message. A trailing question becomes an inferred `NEEDS OWNER`, answered as a new task, not as `OWNER SAID`.
- **Never start a second manager on a repo.** Two managers in one checkout will fight over the working tree.
- **Background jobs take the short id.** `claude stop` and `claude rm` want the id from the `backgrounded · <id> · <name>` line, not the name. The dispatcher stores it in the ledger.
- **Close idle sessions.** Once a day the dispatcher lists sessions idle over 24 hours with no open task and, on your yes, asks each to log and wrap up.
- **Managers never message each other.** If one needs something from another repo it says so in its report, and the dispatcher opens a task there.
