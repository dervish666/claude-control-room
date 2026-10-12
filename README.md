# claude-control-room

How I keep track of a dozen Claude Code sessions across a dozen repos without losing the plot. The setup is heavily customised, but it rests on two rules:

1. **One source of truth: the vault.** Anything that should outlive a session goes into one folder of markdown notes. Every session starts by reading it and ends by writing to it.
2. **One point of communication: the dispatcher.** I talk to one Claude Code session. It routes my instructions to a manager session per repo, keeps a ledger of what is open, and pings my phone only when something needs me.

Everything else here (model routing, hooks, the office dashboard) is optional. Those two rules do most of the work.

```
                 you
                  |
                  v
           +-------------+      ledger.md (open tasks only)
           | dispatcher  |----> T-12 acme-api  NEEDS OWNER Q-1
           +-------------+      T-13 blog      DONE
             |    |    |
     +-------+    |    +--------+
     v            v             v
 +--------+  +--------+    +--------+
 |manager |  |manager |    |manager |   one per repo, delegates
 |acme-api|  |  blog  |    |  infra |   every real job to subagents
 +--------+  +--------+    +--------+
   |  |          |             |
  agents       agents        agents     small / mid / top / design tiers
     \            |             /
      v           v            v
   +-----------------------------------+
   | vault: projects/ journal/ topics/ |   read at session start,
   | daily/ index.md log.md            |   written at session end
   +-----------------------------------+
```

## Who this is for

Claude Code users who run more than one session at a time and keep losing track of what each one is doing, what was decided last week, and which session is waiting on them. You need Claude Code with `--agent`, `--bg` and `claude agents` (I run 2.1.29x), git and python3.

## Start here

Open Claude Code in this folder and say:

> Follow SETUP-FOR-CLAUDE.md.

It inventories what you already have (CLAUDE.md, agents, skills, hooks, notes), asks four questions, shows a merge plan, and asks before every write. Nothing is overwritten without a backup and your yes.

If you would rather read first, go in order:

| Doc | What it covers |
|---|---|
| [01 Principles](docs/01-principles.md) | The two rules and what breaks without them |
| [02 Vault](docs/02-vault.md) | Folder layout, note types, the session-log rules that stop notes rotting |
| [03 Vault MCP](docs/03-vault-mcp.md) | Why sessions should reach the vault through an MCP server |
| [04 Sync](docs/04-sync.md) | One vault on several machines with Syncthing |
| [05 Dispatcher and managers](docs/05-dispatcher-manager.md) | The protocol: task ids, reports, relayed answers, the approval list |
| [06 Model routing](docs/06-model-routing.md) | Tiers, and why every subagent call names its model |
| [07 Jev router](docs/07-jev-router.md) | Optional: a classifier that sizes each message and picks the helper |
| [08 Hooks and guards](docs/08-hooks-and-guards.md) | The deny hook, the compaction flush, the status line |
| [09 Office](docs/09-office.md) | The live dashboard: what it shows and the API behind it |
| [10 Writing rules](docs/10-writing-rules.md) | Brevity and anti-slop rules every session follows |
| [11 Engineering principles](docs/11-engineering-principles.md) | Lessons that change how sessions verify their work |
| [12 Risks and costs](docs/12-risks-and-costs.md) | Bypass mode, what leaves the machine, known limits |

## What is in the repo

| Path | What it is | Needed? |
|---|---|---|
| `templates/CLAUDE.md.template` | Global rules: brevity, writing, vault logging, principles, routing table | Core |
| `templates/agents/` | `dispatcher`, `manager`, `codex-auditor` | Core (codex-auditor optional) |
| `templates/dispatcher/ledger.md` | Empty ledger in the format the dispatcher keeps | Core |
| `templates/vault/` | Vault conventions, index, log and note templates | Core |
| `templates/skills/` | `session-log`, `skill-refiner`, `falsify-first` | Core |
| `templates/hooks/` | `deny-dangerous.sh` with its test cases, `precompact-flush.sh`, a settings snippet | Recommended |
| `templates/output-styles/tight.md` | Short-answer output style | Optional |
| `templates/statusline-command.sh` | Status line: branch, model, effort, context, rate limits | Optional |
| `optional/jev-router/` | Message classifier hook and six helper agents | Optional, needs a paid third-party API |

The office dashboard is described in docs/09 but not shipped as code.

## Dependencies

- **Required:** Claude Code, git, python3.
- **Strongly advised:** an MCP server for your notes folder (any Obsidian MCP server works).
- **Optional:** Obsidian as a viewer, Syncthing for more than one machine, `jq` for the status line, the Claude mobile app for push alerts, the Codex CLI for `codex-auditor`, a TypeSafe API key for the Jev router.

## Licence

Code and templates (everything under `templates/` and `optional/`) are MIT. The prose docs (`README.md`, `SETUP-FOR-CLAUDE.md`, everything under `docs/`) are CC BY 4.0. See [LICENSE](LICENSE).

## TODO

- Sanitised screenshots of the office and the dispatch board (docs/09). The real ones show private project names.
