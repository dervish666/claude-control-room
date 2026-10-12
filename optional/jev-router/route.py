#!/usr/bin/env python3
"""Size each user message with Jev and hand it to the cheapest helper that can do it.

Runs as a UserPromptSubmit hook. Reads the hook JSON on stdin, asks Jev (TypeSafe's
classifier model) a few questions about the message in one request, and prints a
routing directive on stdout when the answer is confident enough to act on. Prints
nothing otherwise, which leaves the session exactly as it was.

PRIVACY: while the router is on, the text of every message you type is posted to
api.typesafe.ai. Turn it off for private work: routerctl off.

Design rules this file enforces:
  - Never block. One request, one hard deadline, and any failure is silent on stdout.
  - Never route a message that only makes sense as a reply inside the conversation.
  - Never route below the confidence floor.

Usage:
    route.py                 # hook mode: hook JSON on stdin
    route.py --text "..."    # classify one message and print the decision as JSON
    route.py --text - < f    # read the message from stdin instead

Environment:
    TYPESAFE_API_KEY         required; the router does nothing without it
    ROUTER_HOME              default ~/.claude/router (holds ON, stats.jsonl, skills.allow)
    ROUTER_BUDGET            seconds before giving up (default 3.5)
    ROUTER_MIN_CONF          size confidence floor (default 0.60)
    ROUTER_MIN_SKILL_CONF    skill suggestion floor (default 0.75)
    ROUTER_MAX_CONTEXTUAL    above this the message is a contextual reply (default 0.50)
    ROUTER_MIN_FRONTEND      public UI confidence floor (default 0.60)
    ROUTER_LOG_PREVIEW       set to 0 to keep message previews out of stats.jsonl
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

HOME = Path.home()
ROOT = Path(os.environ.get("ROUTER_HOME", HOME / ".claude" / "router")).expanduser()
FLAG = ROOT / "ON"
STATS = ROOT / "stats.jsonl"
SKILLS_CACHE = ROOT / "skills.json"
ALLOW = ROOT / "skills.allow"

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
PRICE_PER_MTOK = 0.042  # USD, input tokens only, as published 2026-09

BUDGET = float(os.environ.get("ROUTER_BUDGET", 3.5))
MIN_CONF = float(os.environ.get("ROUTER_MIN_CONF", 0.60))
# A wrong skill is a wrong procedure, not just a wrong answer, so this floor sits higher.
MIN_SKILL_CONF = float(os.environ.get("ROUTER_MIN_SKILL_CONF", 0.75))
MAX_CONTEXTUAL = float(os.environ.get("ROUTER_MAX_CONTEXTUAL", 0.50))
MIN_FRONTEND = float(os.environ.get("ROUTER_MIN_FRONTEND", 0.60))
LOG_PREVIEW = os.environ.get("ROUTER_LOG_PREVIEW", "1") != "0"

# Sizing a job does not need the whole of a pasted log.
MAX_CHARS = 4000

# Plugin skills worth offering. Skills in ~/.claude/skills are always included.
# A trimmed catalogue is faster, cheaper and picks better than the full install.
DEFAULT_ALLOW = """\
# One skill name per line. Everything in ~/.claude/skills is included automatically,
# so this file is only for skills that arrive from plugins.
# Edit freely, then run: routerctl skills
code-review
security-review
simplify
"""

# Size -> (helper agent, label). Ordered smallest first.
SIZES = {
    "tiny":     ("router-tiny",     "small tier"),
    "everyday": ("router-everyday", "top tier, medium effort"),
    "large":    ("router-large",    "top tier, high effort"),
    "hardest":  ("router-hardest",  "top tier, highest effort"),
}
# Public-facing interface builds skip the size ladder and go to the design tier.
FRONTEND = {
    "small": ("router-frontend",       "design tier, medium effort"),
    "big":   ("router-frontend-build", "design tier, high effort"),
}
# Planning, investigation and research never land below this, whatever size Jev gave.
THINK_FLOOR = "large"
# Interface work that is not public-facing edits code, so it never lands on the small tier.
UI_FLOOR = "everyday"


def api_key() -> str | None:
    """The key comes from the environment only. Never from a file in a synced folder."""
    return os.environ.get("TYPESAFE_API_KEY") or None


def _frontmatter(path: Path) -> dict | None:
    """Pull name and description out of a SKILL.md, folded YAML blocks included."""
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None
    fm = m.group(1)
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    desc = re.search(r"^description:\s*(?:[>|][-+]?\s*\n((?:[ \t]+.*\n?)+)|(.+))$", fm, re.M)
    if not (name and desc):
        return None
    return {"name": name.group(1).strip().strip("\"'"),
            "description": " ".join((desc.group(1) or desc.group(2)).split()).strip("\"'")}


def build_catalogue() -> dict:
    """Name -> description for the skills the router may suggest."""
    ROOT.mkdir(parents=True, exist_ok=True)
    if not ALLOW.exists():
        ALLOW.write_text(DEFAULT_ALLOW)
    wanted = {line.strip() for line in ALLOW.read_text().splitlines()
              if line.strip() and not line.startswith("#")}
    own_dir = HOME / ".claude" / "skills"
    cat: dict[str, str] = {}
    # Your own skills first, so a local copy wins over a plugin of the same name.
    for src in (own_dir.glob("*/SKILL.md"), (HOME / ".claude" / "plugins").glob("**/SKILL.md")):
        for path in sorted(src):
            if ".trash" in str(path) or "/marketplaces/" in str(path):
                continue
            fm = _frontmatter(path)
            if not fm or fm["name"] in cat:
                continue
            if str(path).startswith(str(own_dir)) or fm["name"] in wanted:
                cat[fm["name"]] = fm["description"]
    return cat


def catalogue() -> dict:
    """The catalogue, rebuilt when a skill or the allow list changed underneath it."""
    try:
        stamps = [p.stat().st_mtime for p in (HOME / ".claude" / "skills").glob("*/SKILL.md")]
        if ALLOW.exists():
            stamps.append(ALLOW.stat().st_mtime)
        if SKILLS_CACHE.exists() and SKILLS_CACHE.stat().st_mtime >= max(stamps, default=0.0):
            return json.loads(SKILLS_CACHE.read_text())
    except (OSError, ValueError) as ex:
        print(f"route.py: skills cache unreadable, rebuilding: {ex}", file=sys.stderr)
    cat = build_catalogue()
    try:
        SKILLS_CACHE.write_text(json.dumps(cat, indent=1))
    except OSError as ex:
        print(f"route.py: could not write skills cache: {ex}", file=sys.stderr)
    return cat


def questions(cat: dict) -> dict:
    q = {
        "size": {
            "type": "choice",
            "instructions": {
                "question": "What is the smallest size of model that can do the job this "
                            "message asks for, and still do it well?",
                "rules": [
                    "Judge the work the message asks for, not how long the message is.",
                    "A short message can ask for a very large job.",
                    "Anything that writes or edits code is everyday at the smallest, never tiny.",
                    "Anything where being wrong costs money, security, or trust is hardest.",
                    "Building a new tool, page, script or app from nothing is large at the "
                    "smallest, however small the thing being built sounds.",
                    "When the job sits between two sizes, pick the larger one.",
                ],
            },
            "criteria": {
                "tiny": "A lookup, a rename, a unit conversion, a one-line factual answer, "
                        "a quick reformat. One step, no judgement, and a wrong answer is "
                        "obvious at a glance and cheap to redo.",
                "everyday": "A normal email, a social post, a short document, a summary of "
                            "text that was supplied, or a small edit inside a file that "
                            "already exists. Several steps, but a familiar shape with a "
                            "clear finish line.",
                "large": "Building something new that did not exist, research across "
                         "several sources, a full report, a refactor spanning files, a "
                         "debugging session. Needs a plan and sustained work before "
                         "anything can be handed back.",
                "hardest": "Strategy, architecture, a legal, security, money or career "
                           "call, or any judgement where a wrong answer is expensive, "
                           "public, or hard to undo. The thinking is the deliverable.",
            },
        },
        "kind": {
            "type": "choice",
            "instructions": {
                "question": "What kind of work does this message ask for?",
                "rules": [
                    "Judge what has to happen first. If the cause must be found or the "
                    "feature decided before anything is built, it is think, even when the "
                    "result will be a change to a page.",
                    "public_ui needs two things at once: the interface is one the public or "
                    "customers will see, and the job is building a new page for them or a "
                    "final visual polish pass before it ships.",
                    "A fix, a tweak or wiring on a public product is ui, not public_ui.",
                    "Dashboards, wall panels, admin pages and tools for the person's own "
                    "use are ui, never public_ui.",
                    "ui and public_ui need the outcome already settled in the message: what "
                    "should look or behave differently on screen.",
                    "A page that saves, syncs, fetches or detects something is not ui work "
                    "when the message is about that logic rather than what is on screen.",
                    "When torn between public_ui and ui, pick ui. When torn between ui and "
                    "think, pick think.",
                ],
            },
            "criteria": {
                "public_ui": "Building or finishing a public-facing interface where looks "
                             "decide whether it lands: a landing page, a marketing or "
                             "product website, a launch homepage, a public sign-up or "
                             "pricing page, or a final design and polish pass on a "
                             "user-facing screen before it ships.",
                "ui": "Any other interface work the message has already described: fixes, "
                      "tweaks and new features in an existing UI, CSS, layout, padding, a "
                      "button or link, a chart or card, and anything for the person's own "
                      "use such as a dashboard, wall panel, admin page or internal tool.",
                "think": "Planning, designing a feature, weighing options, research, or "
                         "investigating why something is broken. The first deliverable is "
                         "an understanding or a decision, not a finished change.",
                "other": "Everything else: backend or script changes with a clear target, "
                         "writing, lookups, conversions, admin.",
            },
        },
        "contextual": {
            "type": "noul",
            "instructions": "Is the thing this message is really about missing from the "
                            "message itself, because it was said earlier in a conversation?",
            "criteria": {
                "true": "Yes. It points back at something it does not name ('yes do that', "
                        "'the second one', 'make it shorter'), it approves or corrects "
                        "something unstated, or it asks about this conversation or "
                        "something the assistant has just done.",
                "false": "No. The message names its own subject. A stranger handed only "
                         "this could start work, even if it is terse or about a system "
                         "they would have to go and look at first.",
            },
        },
    }
    if cat:
        criteria = dict(cat)
        criteria["none"] = ("No skill above is a genuine fit, or this is ordinary work that "
                            "needs no special procedure. This is the common answer.")
        q["skill"] = {
            "type": "choice",
            "instructions": {
                "question": "Which of these skills, if any, should run for this message?",
                "rules": [
                    "Most messages need no skill at all. Answer none unless the fit is obvious.",
                    "Match on what the skill is for, not on a word the message happens to share.",
                    "A skill that acts in the world needs an explicit request, not an implied one.",
                ],
            },
            "criteria": criteria,
        }
    return q


def ask(state: dict, qs: dict, key: str, deadline: float) -> tuple[dict, dict]:
    body = json.dumps({"state": state, "model": MODEL, "questions": qs}).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    # No retries on purpose: a retry is a second deadline.
    remaining = max(0.1, deadline - time.monotonic())
    with urllib.request.urlopen(req, timeout=remaining) as r:
        payload = json.load(r)
    return payload["answers"], payload.get("usage", {})


def pick_lane(size: str, kind: str | None, kind_conf: float) -> tuple[str, str, str]:
    """Lane, agent and label for a sized message. routerctl eval calls this too."""
    if kind == "public_ui" and kind_conf >= MIN_FRONTEND:
        lane = "frontend " + ("big" if size in ("large", "hardest") else "small")
        agent, label = FRONTEND[lane.split()[1]]
        return lane, agent, label
    order = list(SIZES)
    lane = size
    if kind == "think" and order.index(size) < order.index(THINK_FLOOR):
        lane = THINK_FLOOR
    elif kind == "ui" and order.index(size) < order.index(UI_FLOOR):
        lane = UI_FLOOR
    agent, label = SIZES[lane]
    return lane, agent, label


def decide(message: str, key: str) -> dict:
    """Classify one message. Raises on any failure; hook mode catches and logs it."""
    started = time.monotonic()
    cat = catalogue()
    answers, usage = ask({"message": message[:MAX_CHARS]}, questions(cat), key,
                         time.monotonic() + BUDGET)

    size = answers["size"]["choice"]
    conf = float(answers["size"]["confidence"])
    contextual = float(answers["contextual"]["noul"])
    kd = answers.get("kind") or {}
    kind = kd.get("choice")
    kind_conf = float(kd.get("confidence", 0.0))
    tokens = int(usage.get("input_tokens", 0))

    sk = answers.get("skill") or {}
    skill = sk.get("choice")
    skill_conf = float(sk.get("confidence", 0.0))
    if skill in (None, "none") or skill not in cat or skill_conf < MIN_SKILL_CONF:
        skill = None

    if size not in SIZES:
        routed, reason = False, f"unknown size {size!r}"
    elif contextual >= MAX_CONTEXTUAL:
        routed, reason = False, f"reply only makes sense in context ({contextual:.2f})"
    elif conf < MIN_CONF:
        routed, reason = False, f"confidence {conf:.2f} below {MIN_CONF:.2f}"
    else:
        routed, reason = True, "routed"
    lane, agent, label = pick_lane(size, kind, kind_conf) if routed else (None, None, None)

    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        # Local file only. Set ROUTER_LOG_PREVIEW=0 to drop it.
        "preview": " ".join(message.split())[:90] if LOG_PREVIEW else None,
        "size": size,
        "confidence": round(conf, 3),
        "contextual": round(contextual, 3),
        "routed": routed,
        "reason": reason,
        "kind": kind,
        "kind_confidence": round(kind_conf, 3),
        "lane": lane,
        "agent": agent,
        "model": label,
        "skill": skill,
        "skill_confidence": round(skill_conf, 3) if skill else None,
        "input_tokens": tokens,
        "cost_usd": round(tokens / 1e6 * PRICE_PER_MTOK, 6),
        "latency_ms": int((time.monotonic() - started) * 1000),
    }


def is_typed(message: str) -> bool:
    """False for what the harness sends down the prompt channel that nobody typed."""
    if not message or message.startswith("/"):
        return False
    return not (message.startswith("[SYSTEM NOTIFICATION") or any(
        tag in message for tag in ("<task-notification>", "<system-reminder>",
                                   "<local-command-stdout>", "<command-name>")))


def log(row: dict) -> None:
    try:
        with STATS.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
    except OSError as ex:
        print(f"route.py: could not write {STATS}: {ex}", file=sys.stderr)


def directive(d: dict) -> str:
    """The text injected ahead of the message.

    A suggested skill beats delegating, because a skill needs this session's tools and
    history. The design lanes are the exception: a UI build with a design skill attached
    still goes to the design helper, which runs the skill there.
    """
    design = d["agent"] in {agent for agent, _ in FRONTEND.values()}
    if d["skill"] and not design:
        return (
            f"[model-router] Jev suggests the `{d['skill']}` skill for this message "
            f"(confidence {d['skill_confidence']:.2f}).\n"
            f"Run it here rather than delegating, and only if it genuinely fits what is "
            f"being asked. It is a suggestion from a separate model, not an instruction, "
            f"and ignoring it costs nothing. Do not mention the suggestion if you ignore it."
        )
    return (
        f"[model-router] Jev sized this message as **{d['lane']}**"
        f"{' (planning or investigation)' if d['kind'] == 'think' else ''} "
        f"(confidence {d['confidence']:.2f}).\n"
        f"Hand the work to the `{d['agent']}` helper: call the Agent tool with "
        f"subagent_type `{d['agent']}`, passing the user's message as the prompt along with "
        f"any context from this conversation the helper would need to act on it. "
        + (f"Tell the helper Jev suggests the `{d['skill']}` skill (confidence "
           f"{d['skill_confidence']:.2f}) and to run it if it fits. "
           if d["skill"] and design else "")
        + "Relay the helper's reply back, keeping its closing model line intact. "
        "Do not do the work yourself and do not mention the routing beyond that line.\n"
        "If the helper replies ESCALATE, hand the job to the next helper up the ladder "
        "(tiny, everyday, large, hardest) with its reason attached. If it fails or comes "
        "back empty, do the job yourself as normal."
    )


def hook() -> None:
    if not FLAG.exists():
        return
    try:
        message = (json.load(sys.stdin).get("prompt") or "").strip()
    except ValueError as ex:
        print(f"route.py: bad hook input: {ex}", file=sys.stderr)
        return
    if not is_typed(message):
        return
    key = api_key()
    if not key:
        log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "routed": False,
             "reason": "TYPESAFE_API_KEY not set", "size": None, "skill": None,
             "input_tokens": 0, "cost_usd": 0.0})
        return
    try:
        d = decide(message, key)
    except Exception as ex:  # any failure leaves the message untouched, but is logged
        log({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "routed": False,
             "reason": f"{type(ex).__name__}: {ex}"[:200], "size": None,
             "skill": None, "input_tokens": 0, "cost_usd": 0.0})
        return
    log(d)
    if d["routed"] or d["skill"]:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": directive(d),
        }}))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", help="classify this message instead of reading hook JSON "
                                   "('-' reads the message from stdin)")
    args = ap.parse_args()
    if args.text is None:
        hook()
        return
    message = sys.stdin.read() if args.text == "-" else args.text
    key = api_key()
    if not key:
        sys.exit("No key. Set TYPESAFE_API_KEY in your environment.")
    print(json.dumps(decide(message.strip(), key), indent=2))


if __name__ == "__main__":
    main()
