# 12 Risks, costs and known limits

## Permission mode

**The templates assume normal permission mode.** In normal mode a background manager stops at each permission prompt and waits; you see it as a session needing input. Three ways to live with that, from safest:

1. **Normal mode plus an allow-list.** Add the read-only and routine commands your managers run (`git status`, your test runner, your build) to `permissions.allow` in settings. Run `/fewer-permission-prompts` after a week to pick them from real transcripts.
2. **Auto mode**, if your Claude Code version has it: a classifier approves routine actions and stops for risky ones.
3. **Bypass mode (opt-in).** `--dangerously-skip-permissions` on the dispatcher and managers. This is how I run it, and it is a real risk:
   - Nothing stops a tool call except your hooks and the model's own adherence to the approval list.
   - The deny hook ([08](08-hooks-and-guards.md)) covers a handful of catastrophic commands, not "anything bad".
   - A prompt injection in a web page, issue or file a session reads acts with your full permissions.
   - The forged-message check in the manager is the only thing between another session and your approval.

   Use bypass only on a machine where everything the sessions can reach is backed up or disposable, and never with credentials in the environment that you could not rotate quickly.

## What leaves the machine

| What | Where | When |
|---|---|---|
| Your messages and session context | Anthropic | Always; it is how Claude Code works |
| Each typed message, up to 4,000 characters | TypeSafe (`api.typesafe.ai`) | Only while the Jev router is on |
| Name and description of every skill in the router's catalogue | TypeSafe | Every message, while the Jev router is on |
| The tail of the previous reply | TypeSafe | Only with the effort plugin on |
| The audit prompt, and any file contents Codex reads while auditing | OpenAI | Each time a manager spawns `codex-auditor` |
| Push notification text | Your phone, through the Claude app | Each `NEEDS OWNER` push |
| Vault contents | Wherever you sync or serve it | If you set up sync or remote access |

The dispatcher prompt forbids secrets and personal data in push text. Keep it that way.

## Usage limits

Every manager session draws on the same weekly usage limit, and managers run on the top tier. Five idle-but-alive managers cost nothing; five busy ones cost five times as much. The dispatcher starts managers only when an instruction needs one, and once a day offers to close sessions idle for more than 24 hours. The status line shows the 5-hour and 7-day windows so you see the burn.

## Known limit: background sessions and the shared checkout

The manager rule is "work in the main checkout on a branch, never create worktrees by hand", and the deny hook blocks `git worktree add`. That keeps one checkout per repo and stops worktrees piling up.

It clashes with background sessions. In my testing, a session started with `claude --bg` could not Edit or Write files in its shared checkout until it isolated itself into a worktree, which is the thing the rule forbids. I have not resolved this. Settings has a `worktree.bgIsolation` key that looks relevant, but I have not verified what it does. Until this is settled, options are:

- start managers interactively (in a terminal tab) rather than with `--bg`, or
- let background managers delegate writes to subagents with `isolation: "worktree"`, which the harness creates, and have them merge and clean up before reporting `DONE`, or
- relax the worktree rule for background sessions and accept the cleanup.

## Other things that will bite

- **Busy can lie.** A session with a live background child process never goes idle. See [05](05-dispatcher-manager.md).
- **Names drift.** Sessions are renamed by hooks and die with derived names. Key everything on session id.
- **Undocumented features move.** The dispatcher depends on `claude agents --json`, `--bg`, cross-session messaging and `~/.claude/sessions/<pid>.json`, all recent. Pin the Claude Code version you tested with, and re-test after upgrades.
- **Vault collisions.** Two sessions writing the same journal filename the same evening overwrite each other. The `session-log` skill checks first.
- **Secrets in git history.** If a secret ever lands in the vault's git history, that repo can never be pushed anywhere. Decide where secrets live before the first commit.
