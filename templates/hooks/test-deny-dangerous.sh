#!/bin/bash
# Runs every case in deny-cases.txt through deny-dangerous.sh and checks the verdict.
# Usage: bash test-deny-dangerous.sh [path/to/deny-dangerous.sh]
# Exit status is the number of failures.

here=$(cd "$(dirname "$0")" && pwd)
hook=${1:-$here/deny-dangerous.sh}
fails=0
total=0

while IFS=$'\t' read -r expect cmd; do
  case "$expect" in ''|'#'*) continue ;; esac
  cmd=${cmd//@HOME@/$HOME}
  out=$(python3 -c 'import json,sys; print(json.dumps({"tool_input": {"command": sys.argv[1]}}))' "$cmd" | bash "$hook")
  if [ -n "$out" ]; then got=DENY; else got=ALLOW; fi
  total=$((total + 1))
  if [ "$got" = "$expect" ]; then
    printf 'ok    %-5s %s\n' "$got" "$cmd"
  else
    printf 'FAIL  want %-5s got %-5s %s\n' "$expect" "$got" "$cmd"
    fails=$((fails + 1))
  fi
done < "$here/deny-cases.txt"

echo "$((total - fails))/$total passed"
exit "$fails"
