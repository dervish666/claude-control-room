#!/bin/bash
# PreCompact hook (matcher: auto). Blocks the FIRST auto-compaction of a session with
# a reminder to write in-flight state to the vault, then always lets it through.
#
# A blocking hook without a marker file loops forever, so the marker bounds it to one
# flush per session; later compactions pass silently. PreCompact cannot inject
# context, only block with a reason, hence this design.

INPUT=$(cat)
SESSION_ID=$(printf '%s' "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id','unknown'))" 2>/dev/null)
MARKER="${PRECOMPACT_MARKER_DIR:-${TMPDIR:-/tmp}}/claude-precompact-flushed-${SESSION_ID:-unknown}"

if [ -f "$MARKER" ]; then
  exit 0
fi

# If the marker cannot be written, blocking would repeat on every attempt and the
# session could never compact. Let compaction through and say why.
if ! touch "$MARKER" 2>/dev/null; then
  echo "precompact-flush: cannot create marker $MARKER; allowing compaction without the flush reminder" >&2
  exit 0
fi
echo '{"decision": "block", "reason": "Before compaction: write any in-flight decisions, task state and unlogged findings to the vault (the project note, or today'"'"'s daily note) so they survive the context squeeze. Then continue. Compaction will proceed on the next attempt."}'
