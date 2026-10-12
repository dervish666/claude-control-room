# Jev router (optional)

A `UserPromptSubmit` hook that sizes each message you type and tells the main thread which helper agent should do the job. Background and measurements: [docs/07](../../docs/07-jev-router.md).

> **Privacy.** While the router is on, the text of every message you type (up to 4,000 characters) is posted to TypeSafe at `api.typesafe.ai`. It is not sent to any other provider. Turn it off for private work with `routerctl off`.

> **Cost.** TypeSafe is a paid API billed on input tokens. In my measurements the size, kind and skill questions together cost about $0.22 per 1,000 messages and added about 1.2 s per message on average.

**Off by default.** Nothing happens until you run `routerctl on` and set `TYPESAFE_API_KEY`.

## Files

| File | What it does |
|---|---|
| `route.py` | The classifier and hook entry point. `--text "..."` classifies one message from the command line |
| `routerctl` | `on`, `off`, `status`, `log`, `skills`, `eval` |
| `eval.example.json` | Five generic cases. Copy to `eval.json` and replace with twenty or more of your own real messages |
| `agents/router-*.md` | The six helpers: tiny, everyday, large, hardest, frontend, frontend-build |

## Install

```bash
mkdir -p ~/.claude/router
cp route.py routerctl eval.example.json ~/.claude/router/
chmod +x ~/.claude/router/route.py ~/.claude/router/routerctl
cp agents/router-*.md ~/.claude/agents/
```

Set the key in your shell profile, not in a file inside a synced folder or in `settings.json`:

```bash
export TYPESAFE_API_KEY=...   # from your TypeSafe account
```

Add the hook to `~/.claude/settings.json` under `hooks`:

```json
"UserPromptSubmit": [
  { "hooks": [ { "type": "command",
    "command": "if [ -f \"$HOME/.claude/router/ON\" ]; then python3 \"$HOME/.claude/router/route.py\"; else cat >/dev/null; fi; exit 0" } ] }
]
```

Start a new Claude Code session (hooks and agents load at session start), then `~/.claude/router/routerctl on`.

## Check it

```bash
~/.claude/router/routerctl eval      # live calls, writes nothing to stats
~/.claude/router/routerctl status
~/.claude/router/routerctl log 20
```

## Remove it

Delete the hook entry from `settings.json`, then `rm -r ~/.claude/router ~/.claude/agents/router-*.md`.

## Without it

The routing table in `CLAUDE.md` (see `templates/CLAUDE.md.template`) does the same job by hand at no cost: the main thread picks a tier per brief from the table. Most of the saving comes from that table, not from the classifier.

## Local files it creates

`ON` (the switch), `skills.allow` (which plugin skills may be suggested), `skills.json` (built catalogue), `stats.jsonl` (one line per decision, including the first 90 characters of the message unless `ROUTER_LOG_PREVIEW=0`). All stay local. Keep them out of any repo you publish.
