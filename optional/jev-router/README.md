# Jev router (optional)

A `UserPromptSubmit` hook that sizes each message you type and tells the main thread which helper agent should do the job. Background and measurements: [docs/07](../../docs/07-jev-router.md).

> **Privacy.** While the router is on, two things are posted to TypeSafe at `api.typesafe.ai` with every message you type: the message text (up to 4,000 characters), and the name and description of every skill in the router's catalogue (all of `~/.claude/skills` plus the plugin skills in `skills.allow`). If a skill description names a client, a person or an internal system, that goes too; check them with `routerctl skills`. Nothing is sent to any other provider. Turn it off for private work with `routerctl off`.

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

Run from this folder. It never overwrites: a file that already exists is skipped and named, so you can diff it yourself. The agents it adds are recorded in `~/.claude/router/installed-agents.txt` for the uninstall.

```bash
mkdir -p ~/.claude/router ~/.claude/agents
for f in route.py routerctl eval.example.json; do
  if [ -e ~/.claude/router/$f ]; then echo "skipped, exists: ~/.claude/router/$f"
  else cp $f ~/.claude/router/$f; fi
done
chmod +x ~/.claude/router/route.py ~/.claude/router/routerctl
for f in router-tiny.md router-everyday.md router-large.md router-hardest.md \
         router-frontend.md router-frontend-build.md; do
  if [ -e ~/.claude/agents/$f ]; then echo "skipped, exists: ~/.claude/agents/$f"
  else cp agents/$f ~/.claude/agents/$f && echo $f >> ~/.claude/router/installed-agents.txt; fi
done
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

Delete the hook entry from `settings.json`, then remove only what the install and the router created. Agents you had before the install are not in `installed-agents.txt`, so they stay. Your own `eval.json`, if any, stays too.

```bash
if [ -f ~/.claude/router/installed-agents.txt ]; then
  while read -r f; do
    case "$f" in router-tiny.md|router-everyday.md|router-large.md|router-hardest.md|router-frontend.md|router-frontend-build.md)
      rm -f ~/.claude/agents/"$f" ;;
    esac
  done < ~/.claude/router/installed-agents.txt
fi
for f in route.py routerctl eval.example.json ON skills.allow skills.json stats.jsonl installed-agents.txt; do
  rm -f ~/.claude/router/$f
done
rm -rf ~/.claude/router/__pycache__
rmdir ~/.claude/router 2>/dev/null || echo "left ~/.claude/router: it holds files this install did not create"
```

## Without it

The routing table in `CLAUDE.md` (see `templates/CLAUDE.md.template`) does the same job by hand at no cost: the main thread picks a tier per brief from the table. Most of the saving comes from that table, not from the classifier.

## Local files it creates

- `ON`: the switch.
- `skills.allow`: which plugin skills may be suggested.
- `skills.json`: the built catalogue.
- `installed-agents.txt`: the agent files the install added.
- `stats.jsonl`: one line per decision. **It holds message previews**: the first 90 characters of each message you typed, unless `ROUTER_LOG_PREVIEW=0`. The router creates it mode 0600 and tightens an existing copy to 0600.

All stay local. Keep them out of any repo you publish and out of synced folders.
