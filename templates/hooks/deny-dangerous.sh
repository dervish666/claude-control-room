#!/bin/bash
# PreToolUse guard (matcher: Bash). Denies a small set of catastrophic commands.
# The deny set is kept tight on purpose: a guard that fires on ordinary work gets
# switched off. It blocks:
#   1. rm -rf aimed at filesystem root, ~ or $HOME (not subpaths like ./build)
#   2. git push --force / -f / +refspec  (--force-with-lease is allowed)
#   3. disk wipes: mkfs, diskutil erase*
#   4. git worktree add  (sessions work in the main checkout on a branch; the Agent
#      tool's isolation: "worktree" is made by the harness, not through Bash)
# Add your own patterns to DENY, with a reason the model will read.
# Output contract: hookSpecificOutput.permissionDecision "deny" JSON on stdout.

INPUT=$(cat)
python3 - "$INPUT" <<'PYEOF'
import json, re, sys

try:
    cmd = json.loads(sys.argv[1]).get("tool_input", {}).get("command", "")
except Exception as ex:
    print(f"deny-dangerous: unreadable hook input: {ex}", file=sys.stderr)
    sys.exit(0)

cmd = cmd.replace("\\\n", " ")

# git global options that may sit between `git` and the subcommand: -C dir, -c k=v, ...
GIT = r"""\bgit(?:\s+(?:(?:-[Cc]|--(?:git-dir|work-tree|namespace|config-env|attr-source))\s+(?:"[^"]*"|'[^']*'|[^\s"'])+|-[-\w]+(?:=(?:"[^"]*"|'[^']*'|[^\s"'])+)?))*"""

DENY = [
    (r"""\brm\s+(-[a-z]*[rf][a-z]*\s+)*-[a-z]*[rf][a-z]*\s+["']?(/|~|\$HOME)/?["']?\s*(\*|$|;|&|\|)""",
     "rm -rf targeting filesystem root or home is blocked (deny-dangerous hook)"),
    (GIT + r"""\s+push\b(?=.*(\s--force(?![\w-])|\s-[vqun46]*f[vqun46]*\b)|[^;&|\n]*\s\+\S)""",
     "git push --force is blocked; use --force-with-lease if you really mean it (deny-dangerous hook)"),
    (r"""\b(mkfs(\.\w+)?|diskutil\s+(erase\w*|zeroDisk|partitionDisk))\b""",
     "Disk-wipe command blocked (deny-dangerous hook)"),
    (GIT + r"""\s+worktree\s+add\b""",
     "Creating worktrees is blocked; work in the main checkout on a branch, or use the Agent tool's isolation: 'worktree' (deny-dangerous hook)"),
]

for pattern, reason in DENY:
    if re.search(pattern, cmd, re.IGNORECASE):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason}}))
        sys.exit(0)
sys.exit(0)
PYEOF
