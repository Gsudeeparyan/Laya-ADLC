#!/bin/sh
# Laya guard: stops an agent's most damaging commands and writes before they run.
# Reads the tool call as JSON on stdin. Prints a deny decision, or nothing to allow it.
# A crash denies the call (Copilot treats a non-zero exit as a denial); a timeout does not.

dir=$(dirname "$0")
patterns="$dir/laya-guard-patterns.txt"
[ -r "$patterns" ] || { echo "laya-guard: $patterns not found" >&2; exit 1; }

payload=$(cat | sed 's/\\[nrt]/ /g')
shell_tool=no
if printf '%s' "$payload" | grep -Eiq '"(toolName|tool_name)" *: *"(bash|sh|powershell|pwsh|shell|execute|run_in_terminal|runInTerminal|terminal)"'; then
  shell_tool=yes
fi

tab=$(printf '\t')
decision=$(tr -d '\r' < "$patterns" | while IFS="$tab" read -r scope flags regex reason; do
  case "$scope" in ''|'#'*) continue ;; esac
  if [ "$scope" = shell ] && [ "$shell_tool" = no ]; then continue; fi
  if [ "$flags" = i ]; then opt=-Eiq; else opt=-Eq; fi
  if printf '%s' "$payload" | grep "$opt" -e "$regex"; then
    printf '{"permissionDecision":"deny","permissionDecisionReason":"%s"}' "$reason"
    break
  fi
done)
[ -z "$decision" ] || printf '%s\n' "$decision"
exit 0
