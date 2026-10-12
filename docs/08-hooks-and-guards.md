# 08 Hooks and guards

Hooks are shell commands Claude Code runs at fixed points: before a tool call, when you submit a message, before compaction. The harness runs them, not the model, so they hold even when the model forgets an instruction. They load at session start: after any change, start a new session.

Merge `templates/hooks/settings.snippet.json` into `~/.claude/settings.json`. Never replace the whole file.

## deny-dangerous.sh (PreToolUse, Bash)

Denies a short list of commands that cannot be undone:

- `rm` with `-r`, `-f`, `--recursive` or `--force` where any target is `/`, `~`, `$HOME`, `${HOME}`, your home directory's real path, or a glob of those (`~/*`, `/*`). The hook tokenises the arguments with `shlex`, so quoting, `--`, a trailing slash or an extra target (`rm -rf ./build ~`) does not hide it. Commands inside a quoted string, such as `bash -c "..."`, are checked too.
- `git push --force`, `-f` or a `+refspec` (`--force-with-lease` passes)
- disk wipes (`mkfs`, `diskutil erase`)
- `git worktree add` (see [12](12-risks-and-costs.md) for why)

The list is tight on purpose. A guard that fires on ordinary work gets switched off, and then it guards nothing. Add a pattern only after the command it blocks has actually bitten you.

When I extended the git rules, my first version missed `git -C <dir> push --force`, because the global option sat between `git` and `push`. The current patterns allow global options in that gap. Test every new pattern against both a command it must block and a near miss it must allow; the script reads hook JSON on stdin, so a loop over a file of cases does it.

My first `rm` rule was a regex, and it missed `rm -rf -- "$HOME"`, `rm -rf ${HOME}` and `rm -rf ./build ~`. An outside audit caught it. Tokenising the arguments and judging each target fixed all of them.

The cases live in `templates/hooks/deny-cases.txt`, and `bash templates/hooks/test-deny-dangerous.sh` runs them: 30 cases, commands that must be denied and near misses that must pass (`rm -rf ~/tmp/x`, `rm -rf ./home`). They are in a file because this hook blocks its own test commands if you type them into Bash.

The hook reads its JSON on stdin. Passing it as a command-line argument fails on a large command with "argument list too long".

## precompact-flush.sh (PreCompact, auto)

When a long session is about to auto-compact, the first compaction is blocked once with a reminder to write in-flight decisions and findings to the vault. The next attempt goes through.

The marker file matters: a blocking hook without one blocks every attempt, forever. PreCompact hooks cannot add context, only block with a reason, which is why it works this way.

## The approval list (prompt level)

The dispatcher and manager agents carry a list of steps that need your explicit yes: pushes to main, deploys, force-push, discarding work, messaging people, spending money, secrets and anything irreversible ([05](05-dispatcher-manager.md)). That list lives in the agent prompts, not a hook, so it is only as strong as the model's adherence. The deny hook is the backstop for the few commands where a mistake is unrecoverable.

## Session titles (described, not shipped)

I run a `UserPromptSubmit` hook that names untitled manager sessions. On the second prompt it spawns a background job that asks the small tier for a two-to-five-word topic from the transcript, and the next prompt applies it as the session title. It refines once at prompt four, then stops for good, and never touches a title you set.

It is not shipped because it relies on a hook output field (`sessionTitle`) that is not in the published hook docs and may disappear. If you build one, run the nested `claude -p` with no settings sources, no MCP and a recursion-guard environment variable, or it will trigger its own hook.

## Status line

`templates/statusline-command.sh` shows folder, branch and dirty count, model and live effort, messages typed, context used (with window size, so 22% of 1M is not read as 22% of 200k) and the 5-hour and 7-day rate limits with reset times. It needs `jq`. Turn pieces off in `~/.claude/statusline-config.txt`.

## Output style

`templates/output-styles/tight.md` goes in `~/.claude/output-styles/`. Select it with `"outputStyle": "Tight"` in settings. It overlaps with the brevity rules in CLAUDE.md on purpose: the output style shapes every reply, while CLAUDE.md also reaches subagents and written files.

## Hook hygiene

- **Fail open, but log.** A hook that crashes should let the session carry on, and write why to stderr or a log. A silent failure looks identical to a hook that is working.
- **Time-box anything that calls the network.** The router gives up after 3.5 s and injects nothing.
- **Stop hooks that block need a marker**, for the same reason as the compaction hook.
