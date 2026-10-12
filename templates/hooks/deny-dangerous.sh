#!/bin/bash
# PreToolUse guard (matcher: Bash). Denies a small set of catastrophic commands.
# The deny set is kept tight on purpose: a guard that fires on ordinary work gets
# switched off. It blocks:
#   1. rm with -r, -R, -f, --recursive or --force where any target is /, ~, $HOME,
#      ${HOME}, your home directory's real path, or a glob of those (~/*, /*).
#      Arguments are tokenised, so quoting, `--` and extra targets don't hide it.
#      Commands inside quoted strings (bash -c "...") are checked too.
#   2. git push --force / -f / +refspec  (--force-with-lease is allowed)
#   3. disk wipes: mkfs, diskutil erase*
#   4. git worktree add  (sessions work in the main checkout on a branch; the Agent
#      tool's isolation: "worktree" is made by the harness, not through Bash)
# Add your own patterns to DENY, with a reason the model will read.
# Output contract: hookSpecificOutput.permissionDecision "deny" JSON on stdout.
# The hook JSON arrives on stdin and is passed straight through to python.

read -r -d '' SCRIPT <<'PYEOF'
import json, os, re, shlex, sys

try:
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "") or ""
except Exception as ex:
    print(f"deny-dangerous: unreadable hook input: {ex}", file=sys.stderr)
    sys.exit(0)

cmd = cmd.replace("\\\n", " ")


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))
    sys.exit(0)


# ---- rm: tokenise, then judge each target --------------------------------------

SEPARATORS = {";", "&", "&&", "|", "||", "(", ")", "\n"}
HOME = os.path.expanduser("~").rstrip("/")


def tokens(text):
    """Shell-ish tokens with ; & | ( ) split out. Falls back to a plain split."""
    try:
        lex = shlex.shlex(text, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        # Unbalanced quotes: split on whitespace and separators, strip quote marks.
        parts = re.split(r"(\s+|;|&&|\|\||&|\||\(|\))", text)
        return [p.strip("\"'") for p in parts if p and not p.isspace()]


def dangerous_target(t):
    t = t.replace("${HOME}", "~").replace("$HOME", "~")
    if HOME and (t == HOME or t.startswith(HOME + "/")):
        t = "~" + t[len(HOME):]
    # Peel trailing slashes and glob tails: ~/ , ~/* , /* , ~/.* , //
    while True:
        before = t
        for tail in ("/*", "/.*", "*", "/"):
            if t.endswith(tail) and len(t) > len(tail):
                t = t[: -len(tail)]
        if t == before:
            break
    return t in ("/", "~", "")


def rm_is_dangerous(toks):
    i = 0
    while i < len(toks):
        if os.path.basename(toks[i]) != "rm":
            i += 1
            continue
        forceful, targets, end_of_flags = False, [], False
        j = i + 1
        while j < len(toks) and toks[j] not in SEPARATORS:
            a = toks[j]
            if not end_of_flags and a == "--":
                end_of_flags = True
            elif not end_of_flags and a.startswith("--"):
                forceful |= a in ("--recursive", "--force")
            elif not end_of_flags and a.startswith("-") and len(a) > 1:
                forceful |= any(c in a[1:] for c in "rRf")
            else:
                targets.append(a)
            j += 1
        if forceful and any(dangerous_target(t) for t in targets if t != ""):
            return True
        i = j
    return False


def scan(text, depth=0):
    toks = tokens(text)
    if rm_is_dangerous(toks):
        return True
    # A quoted string may itself be a command: bash -c "rm -rf ~"
    if depth < 2:
        return any(scan(t, depth + 1) for t in toks if " " in t)
    return False


if scan(cmd):
    deny("rm -rf targeting filesystem root or home is blocked (deny-dangerous hook)")

# ---- everything else: patterns -------------------------------------------------

# git global options that may sit between `git` and the subcommand: -C dir, -c k=v, ...
GIT = r"""\bgit(?:\s+(?:(?:-[Cc]|--(?:git-dir|work-tree|namespace|config-env|attr-source))\s+(?:"[^"]*"|'[^']*'|[^\s"'])+|-[-\w]+(?:=(?:"[^"]*"|'[^']*'|[^\s"'])+)?))*"""

DENY = [
    (GIT + r"""\s+push\b(?=.*(\s--force(?![\w-])|\s-[vqun46]*f[vqun46]*\b)|[^;&|\n]*\s\+\S)""",
     "git push --force is blocked; use --force-with-lease if you really mean it (deny-dangerous hook)"),
    (r"""\b(mkfs(\.\w+)?|diskutil\s+(erase\w*|zeroDisk|partitionDisk))\b""",
     "Disk-wipe command blocked (deny-dangerous hook)"),
    (GIT + r"""\s+worktree\s+add\b""",
     "Creating worktrees is blocked; work in the main checkout on a branch, or use the Agent tool's isolation: 'worktree' (deny-dangerous hook)"),
]

for pattern, reason in DENY:
    if re.search(pattern, cmd, re.IGNORECASE):
        deny(reason)
sys.exit(0)
PYEOF
exec python3 -c "$SCRIPT"
