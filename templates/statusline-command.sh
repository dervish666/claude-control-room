#!/bin/bash
# Claude Code status line: folder, branch and dirty count, model and effort, message
# count, context use, and the 5-hour and 7-day rate limits with reset times.
# Reads the JSON payload Claude Code pipes to stdin. Needs jq.
# effort.level in the payload is the live value; settings.json only holds the default.
# Turn pieces off in ~/.claude/statusline-config.txt, e.g. SHOW_WEEKLY=0

config_file="$HOME/.claude/statusline-config.txt"
[ -f "$config_file" ] && source "$config_file"
show_dir=${SHOW_DIRECTORY:-1}
show_branch=${SHOW_BRANCH:-1}
show_model=${SHOW_MODEL:-1}
show_effort=${SHOW_EFFORT:-1}
show_msgs=${SHOW_MESSAGES:-1}
show_usage=${SHOW_USAGE:-1}
show_bar=${SHOW_PROGRESS_BAR:-1}
show_limits=${SHOW_LIMITS:-1}
show_weekly=${SHOW_WEEKLY:-1}
show_reset=${SHOW_RESET_TIME:-1}

input=$(cat)

if ! command -v jq >/dev/null 2>&1; then
  printf 'statusline: jq not installed\n'
  exit 0
fi

# One jq call, one field per line (empty lines preserved).
fields=$(printf '%s' "$input" | jq -r '
  (.workspace.current_dir // .cwd // ""),
  (.model.display_name // ""),
  (if .fast_mode then "1" else "0" end),
  (.effort.level // ""),
  ((.context_window.used_percentage // "") | tostring),
  ((.context_window.context_window_size // "") | tostring),
  ((.rate_limits.five_hour.used_percentage // "") | tostring),
  ((.rate_limits.five_hour.resets_at // "") | tostring),
  ((.rate_limits.seven_day.used_percentage // "") | tostring),
  ((.rate_limits.seven_day.resets_at // "") | tostring),
  (.transcript_path // "")' 2>/dev/null)
{
  read -r current_dir_path
  read -r model_name
  read -r fast_mode
  read -r effort_level
  read -r ctx_pct
  read -r ctx_size
  read -r h5_pct
  read -r h5_reset
  read -r d7_pct
  read -r d7_reset
  read -r transcript_path
} <<< "$fields"

BLUE=$'\033[0;34m'
GREEN=$'\033[0;32m'
GRAY=$'\033[0;90m'
YELLOW=$'\033[0;33m'
PURPLE=$'\033[38;5;99m'
RESET=$'\033[0m'

# Ten steps from dark green to deep red.
GRAD=(22 28 34 100 142 178 172 166 160 124)
grad_color() {
  local i=$(( ($1 - 1) / 10 ))
  [ "$i" -lt 0 ] && i=0
  [ "$i" -gt 9 ] && i=9
  printf '\033[38;5;%sm' "${GRAD[$i]}"
}

to_int() {
  case "$1" in ''|*[!0-9.]*) return ;; esac
  printf '%.0f' "$1" 2>/dev/null
}

# Epoch seconds to a local time string, on macOS (date -r) or GNU (date -d @).
fmt_time() {
  date -r "$1" "+$2" 2>/dev/null || date -d "@$1" "+$2" 2>/dev/null
}

dir_text=""
if [ "$show_dir" = "1" ] && [ -n "$current_dir_path" ]; then
  dir_text="${BLUE}$(basename "$current_dir_path")${RESET}"
fi

branch_text=""
git_dirty_text=""
if [ "$show_branch" = "1" ] && [ -n "$current_dir_path" ] && git -C "$current_dir_path" rev-parse --git-dir >/dev/null 2>&1; then
  branch=$(git -C "$current_dir_path" branch --show-current 2>/dev/null)
  [ -n "$branch" ] && branch_text="${GREEN}⎇ ${branch}${RESET}"
  dirty_count=$(git -C "$current_dir_path" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  if [ "$dirty_count" = "0" ]; then
    git_dirty_text="${GREEN}✓${RESET}"
  else
    git_dirty_text="${YELLOW}✎ ${dirty_count}${RESET}"
  fi
fi

model_text=""
if [ "$show_model" = "1" ] && [ -n "$model_name" ]; then
  model_text="${PURPLE}${model_name}${RESET}"
  [ "$fast_mode" = "1" ] && model_text="${model_text}${YELLOW}⚡${RESET}"
  [ "$show_effort" = "1" ] && [ -n "$effort_level" ] && model_text="${model_text}${GRAY} ${effort_level}${RESET}"
fi

# Messages you typed: user lines minus tool results and meta entries.
msgs_text=""
if [ "$show_msgs" = "1" ] && [ -f "$transcript_path" ]; then
  msg_count=$(grep '"type":"user"' "$transcript_path" 2>/dev/null | grep -v '"toolUseResult"' | grep -cv '"isMeta":true')
  [ "${msg_count:-0}" -gt 0 ] 2>/dev/null && msgs_text="${GRAY}✉ ${msg_count}${RESET}"
fi

usage_text=""
ctx_int=$(to_int "$ctx_pct")
if [ "$show_usage" = "1" ] && [ -n "$ctx_int" ]; then
  bar=""
  if [ "$show_bar" = "1" ]; then
    filled=$(( ctx_int >= 100 ? 10 : (ctx_int * 10 + 50) / 100 ))
    bar=" "
    for i in 0 1 2 3 4 5 6 7 8 9; do
      if [ "$i" -lt "$filled" ]; then bar="${bar}▓"; else bar="${bar}░"; fi
    done
  fi
  # Window size, so 22% of 1M is not mistaken for 22% of 200k.
  size_label=""
  if [ "${ctx_size:-0}" -ge 1000000 ] 2>/dev/null; then
    size_label="${GRAY}·$((ctx_size / 1000000))M${RESET}"
  elif [ "${ctx_size:-0}" -ge 1000 ] 2>/dev/null; then
    size_label="${GRAY}·$((ctx_size / 1000))k${RESET}"
  fi
  usage_text="$(grad_color "$ctx_int")Ctx ${ctx_int}%${bar}${RESET}${size_label}"
fi

h5_text=""
h5_int=$(to_int "$h5_pct")
if [ "$show_limits" = "1" ] && [ -n "$h5_int" ]; then
  h5_text="$(grad_color "$h5_int")5h ${h5_int}%${RESET}"
  if [ "$show_reset" = "1" ] && [ -n "$h5_reset" ]; then
    t=$(fmt_time "$h5_reset" %H:%M)
    [ -n "$t" ] && h5_text="${h5_text}${GRAY} ↻${t}${RESET}"
  fi
fi

d7_text=""
d7_int=$(to_int "$d7_pct")
if [ "$show_limits" = "1" ] && [ "$show_weekly" = "1" ] && [ -n "$d7_int" ]; then
  d7_text="$(grad_color "$d7_int")7d ${d7_int}%${RESET}"
  if [ "$show_reset" = "1" ] && [ -n "$d7_reset" ]; then
    t=$(fmt_time "$d7_reset" %a)
    [ -n "$t" ] && d7_text="${d7_text}${GRAY} ↻${t}${RESET}"
  fi
fi

output=""
sep="${GRAY} │ ${RESET}"
append() {
  [ -z "$1" ] && return
  [ -n "$output" ] && output="${output}${sep}"
  output="${output}$1"
}

append "$dir_text"
append "$branch_text"
if [ -n "$git_dirty_text" ]; then
  if [ -n "$branch_text" ]; then output="${output} ${git_dirty_text}"; else append "$git_dirty_text"; fi
fi
append "$model_text"
append "$msgs_text"
append "$usage_text"
append "$h5_text"
append "$d7_text"

printf '%s\n' "$output"
