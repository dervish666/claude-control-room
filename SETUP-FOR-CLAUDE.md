# Setup instructions for Claude

You are Claude Code, and the user has asked you to install or adapt the setup in this repository. These instructions are for you. Follow them in order. The user may already have a CLAUDE.md, agents, skills, hooks or a notes system of their own; your job is to fit this setup around what exists, not to replace it.

Read `README.md` and `docs/01-principles.md` first, so you can explain the two principles in your own words if asked.

## Ground rules

- **Read-only until the user approves a plan.** Steps 1 and 2 change nothing.
- **Back up before every write.** Copy any file you will change to `~/.claude/backups/control-room-<YYYYMMDD-HHMM>/`, keeping its path, before touching it.
- **Ask before every write.** Show the file, the action and the diff, and wait for a yes. A yes to one component covers that component's files only, unless the user explicitly says "yes to all".
- **Never overwrite.** Existing files are merged or skipped. If a name collides, propose a renamed copy.
- **The user's rules win.** Where their CLAUDE.md or conventions contradict a template, keep theirs and say so.
- **Never read, print or copy secrets.** Do not open credential files, `.env` files or token values in settings. When you inspect config, list key names only.
- **No network calls**, except the router eval in step 5 and only on an explicit yes, because it costs money and sends text to a third party.
- **Never enable bypass permission mode or the router yourself.** Explain, give the command, let the user run it.

## Step 1: Inventory (read-only)

Find out what the user already has. Run the checks, then show one table: item, found or not, path, notes.

1. **Claude Code version:** `claude --version`. The dispatcher needs `claude agents`, `claude --bg` and cross-session messaging; if `claude agents --json` fails, say the dispatcher layer will not work on this version.
2. **Global rules:** does `~/.claude/CLAUDE.md` exist? Size, and its `##` headings. Note any section that overlaps a template section (brevity, writing style, logging or notes, engineering principles, model routing).
3. **Agents:** list `~/.claude/agents/*.md`. Flag name collisions with `dispatcher`, `manager`, `codex-auditor`, `router-*`.
4. **Skills:** list `~/.claude/skills/*/`. Flag collisions with `session-log`, `skill-refiner`, `falsify-first`.
5. **Settings:** in `~/.claude/settings.json`, list which hook events already have entries (`PreToolUse`, `PreCompact`, `UserPromptSubmit` and so on, with matchers), and whether `statusLine` and `outputStyle` are set. Key names only.
6. **Output styles:** list `~/.claude/output-styles/`.
7. **MCP servers:** list registered server names (`claude mcp list`, or the `mcpServers` keys in config). Look for anything that serves notes (Obsidian, markdown, filesystem, Notion).
8. **Notes system:** look for an existing vault: `find ~ -maxdepth 4 -type d -name .obsidian -not -path '*/Library/*' 2>/dev/null`, plus `~/vault`, `~/notes`, `~/Documents/*notes*`. For each, report top-level folders, note count and whether it is a git repo.
9. **Tools:** `command -v git python3 jq codex syncthing`.
10. **Repos:** the git repos the user works in (ask, or list `~/code`, `~/projects`, `~/src` one level deep). These seed the vault's project map and the ledger's aliases.

## Step 2: Ask four questions

Ask these in one message, with your recommendation for each based on the inventory.

1. **Vault location.** Use the notes folder you found at `<path>`, create a new one at `~/vault`, or another path? If they have one, ask whether to map its existing folders onto the roles in docs/02 (projects, journal, topics, daily) or add the missing folders alongside. Never move or rename their notes.
2. **Sync.** One machine only, Syncthing across several (docs/04), or already synced some other way?
3. **Jev router.** Skip it (the default, and free: the routing table in CLAUDE.md does the job by hand), or install it? Installing needs a TypeSafe API key and means every typed message is posted to `api.typesafe.ai` while it is on.
4. **Dispatcher and managers.** Skip for now (vault and rules only), install in normal permission mode (the default), or install with bypass mode as an opt-in after reading docs/12?

Fill `{{NAME}}` from the first word of `git config user.name`, show it in the plan, and let the user change it. Fill `{{VAULT_PATH}}` from question 1.

## Step 3: Merge plan

Show one table covering every component, then wait for approval.

| Component | Source | Target | Action | Why |
|---|---|---|---|---|

Actions are **add** (target missing), **merge** (target exists, combine), or **skip** (collision the user should resolve, or not wanted).

Rules for each component:

- **`templates/CLAUDE.md.template`** to `~/.claude/CLAUDE.md`. If it exists, add only the sections it lacks. For a section with the same purpose, show theirs and the template side by side and propose a merged version that keeps their rules. Replace `mcp__vault__*` with their notes server's tool prefix.
- **`templates/agents/*.md`** to `~/.claude/agents/`. Skip `dispatcher.md` and `manager.md` unless question 4 said yes. Skip `codex-auditor.md` unless `codex` is installed. On a name collision, propose a suffixed copy (`manager-ccr.md`) and say how to start it.
- **`templates/dispatcher/ledger.md`** to `~/.claude/dispatcher/ledger.md`, only with the dispatcher. Fill the aliases table from the repos in step 1.
- **`templates/vault/`** into the vault. Add `CLAUDE.md`, `index.md` and `log.md` only if missing; otherwise propose additions. Put note templates in the vault's templates folder, skipping any name that exists. Fill the project map in the vault's `CLAUDE.md` from the user's repos. If the vault is new, also create `projects/`, `journal/`, `topics/`, `daily/`, `sources/`, and suggest `git init` (ask).
- **`templates/skills/*`** to `~/.claude/skills/`. Same collision rule as agents.
- **`templates/hooks/`**: `deny-dangerous.sh`, `precompact-flush.sh`, `test-deny-dangerous.sh` and `deny-cases.txt` to `~/.claude/hooks/`, then `chmod +x` the scripts. If the user already has a hook of the same name, skip it and show both.
- **`templates/hooks/settings.snippet.json`** into `~/.claude/settings.json`. Merge with a script that parses the JSON, appends hook entries to existing event arrays, and leaves every other key untouched. Skip `statusLine` or `outputStyle` if already set, unless the user asks. Show the before and after diff.
- **`templates/statusline-command.sh`** to `~/.claude/`, only if `jq` is installed and no status line is set.
- **`templates/output-styles/tight.md`** to `~/.claude/output-styles/`.
- **`optional/jev-router/`**, only if question 3 said yes. Follow its README. Tell the user to put `TYPESAFE_API_KEY` in their shell profile themselves; never write the key anywhere.
- **Notes MCP server.** If they have none, recommend any Obsidian MCP server (docs/03) and give the `claude mcp add` command for them to run. Do not install packages without a yes.
- **Sync.** If question 2 chose Syncthing, show the `.stignore` from docs/04 and the steps. Do not configure Syncthing yourself.

## Step 4: Install

Work one component at a time, in the plan's order. For each: back up, show the diff, ask, write, then validate:

- `python3 -m json.tool ~/.claude/settings.json >/dev/null` after any settings change. If it fails, restore the backup at once and say so.
- Each agent and skill file still opens and closes its frontmatter with `---`.
- Hook scripts are executable.
- No `{{NAME}}` or `{{VAULT_PATH}}` placeholders remain in installed files: `grep -rn '{{NAME}}\|{{VAULT_PATH}}' <installed paths>`.

## Step 5: Smoke test

Run each check and report pass or fail with the evidence. A check that could not fail proves nothing, so each one includes a case that must fail.

1. **Deny hook.** Run `bash ~/.claude/hooks/test-deny-dangerous.sh ~/.claude/hooks/deny-dangerous.sh`. It feeds every case in `deny-cases.txt` (commands that must be denied, and near misses that must pass) through the installed hook and must report all passed. Do not type the dangerous cases into Bash yourself: the installed hook will block your own command.
2. **Compaction hook.** Pipe `{"session_id":"ccr-smoke"}` in twice. The first run must block, the second must pass. Delete the marker file afterwards.
3. **Status line**, if installed. Pipe a sample payload with a model name, a context percentage and rate limits, and confirm each appears.
4. **Vault.** With the user's yes, create `topics/control-room-smoke-test.md` through the notes MCP server, find it with a search, then delete it. If search does not find a note you just wrote, the index is not watching the vault; report that, do not wave it through.
5. **Dispatcher**, if installed. You cannot start it from here. Give the user these steps:
   1. `mkdir -p /tmp/ccr-probe && git -C /tmp/ccr-probe init`
   2. In a new terminal: `claude --agent dispatcher -n dispatcher`
   3. Tell it: `start a manager in /tmp/ccr-probe and ask it to reply DONE with its repo path`
   4. Expect a ledger row for T-1, a DONE report naming the path, and the row moving to Closed today.
6. **Router**, if installed and only on a yes (it makes live paid calls): `~/.claude/router/routerctl eval`. Five cases cost a fraction of a cent. Expect most, not necessarily all, to match; report the misses.

## Step 6: Report

Tell the user, briefly:

- what was installed, merged and skipped, with paths
- where the backups are
- that hooks, agents and output styles load at session start, so a new session is needed
- anything that failed a smoke test, and what you think caused it
- how to undo: restore from the backup folder, and remove the hook entries from settings

Then suggest a first real use: "at the end of this session, run the session-log skill", so the vault gets its first entry.
