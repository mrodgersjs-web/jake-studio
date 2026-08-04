#!/usr/bin/env bash
# TAC Tool-Call Tracker — increments counters and auto-suggests /tac-verify.
#
# Uses jq (fast C binary) instead of python. Single invocation per command.
#
# Usage:
#   tac-tool-tracker.sh record   # increment tool_calls
#   tac-tool-tracker.sh build    # increment builds (a build task started)
#   tac-tool-tracker.sh verify   # mark that a verify just happened
#   tac-tool-tracker.sh core4    # mark that a core4 declaration happened
#   tac-tool-tracker.sh status   # print current state
#   tac-tool-tracker.sh reset    # reset all counters
#   tac-tool-tracker.sh get <key>  # get a single field value

set -u

TAC_STATE_DIR="${TAC_STATE_DIR:-$HOME/.jake/state/tac}"
TAC_STATE_FILE="$TAC_STATE_DIR/current.json"
THRESHOLD="${TAC_VERIFY_THRESHOLD:-3}"

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    TAC_STANDALONE=1
fi

mkdir -p "$TAC_STATE_DIR" 2>/dev/null || true

# Initialize state file if missing
if [ ! -f "$TAC_STATE_FILE" ]; then
    cat > "$TAC_STATE_FILE" <<EOF
{
  "session_start": "$(date +%s)",
  "tool_calls": 0,
  "builds": 0,
  "verifies": 0,
  "core4_declarations": 0,
  "last_verify_at": 0,
  "thread": "base",
  "closed_loop": "on",
  "mode": "active"
}
EOF
fi

# ── jq-based operations ──────────────────────────────────────────────
# Single jq invocation per read/write. No python fork overhead.

# Increment a field by delta and update last_update_at (single jq call)
inc_field() {
    local key="$1"
    local delta="$2"
    local tmp
    tmp=$(mktemp)
    jq --arg k "$key" --argjson d "$delta" \
       '.[$k] = (.[$k] // 0) + $d | .last_update_at = (now | strftime("%Y-%m-%dT%H:%M:%S"))' \
       "$TAC_STATE_FILE" > "$tmp" && mv "$tmp" "$TAC_STATE_FILE"
}

# Set a numeric field to an exact value
set_field_num() {
    local key="$1"
    local value="$2"
    local tmp
    tmp=$(mktemp)
    jq --arg k "$key" --argjson v "$value" \
       '.[$k] = $v | .last_update_at = (now | strftime("%Y-%m-%dT%H:%M:%S"))' \
       "$TAC_STATE_FILE" > "$tmp" && mv "$tmp" "$TAC_STATE_FILE"
}

# Reset all counters
reset_state() {
    cat > "$TAC_STATE_FILE" <<EOF
{
  "session_start": "$(date +%s)",
  "tool_calls": 0,
  "builds": 0,
  "verifies": 0,
  "core4_declarations": 0,
  "last_verify_at": 0,
  "thread": "base",
  "closed_loop": "on",
  "mode": "active"
}
EOF
}

# ── Command dispatch ──────────────────────────────────────────────────

cmd="${1:-status}"

case "$cmd" in
    record)
        inc_field "tool_calls" 1
        new_count=$(jq -r '.tool_calls' "$TAC_STATE_FILE")
        last_verify=$(jq -r '.last_verify_at' "$TAC_STATE_FILE")
        builds=$(jq -r '.builds // 0' "$TAC_STATE_FILE")
        if [ "$builds" -gt 0 ] && [ "$new_count" -ge "$THRESHOLD" ] && [ "$last_verify" = "0" ]; then
            echo "[TAC] $new_count tool calls since last build. Consider /tac-verify."
        fi
        ;;

    build)
        inc_field "builds" 1
        new_builds=$(jq -r '.builds' "$TAC_STATE_FILE")
        echo "[TAC] Build recorded. (builds: $new_builds)"
        ;;

    verify)
        current_verifies=$(jq -r '.verifies' "$TAC_STATE_FILE")
        new_verifies=$(( current_verifies + 1 ))
        tmp=$(mktemp)
        jq --argjson v "$new_verifies" --argjson ts "$(date +%s)" \
           '.verifies = $v | .last_verify_at = $ts | .last_update_at = (now | strftime("%Y-%m-%dT%H:%M:%S"))' \
           "$TAC_STATE_FILE" > "$tmp" && mv "$tmp" "$TAC_STATE_FILE"
        echo "[TAC] Verify recorded. Closed loop maintained. (verifies: $new_verifies)"
        ;;

    core4)
        inc_field "core4_declarations" 1
        echo "[TAC] Core Four declaration recorded."
        ;;

    status)
        jq -r 'to_entries | .[] | "\(.key)=\(.value)"' "$TAC_STATE_FILE"
        ;;

    get)
        key="${2:-}"
        if [ -z "$key" ]; then
            echo "Usage: $0 get <field_name>" >&2
            exit 1
        fi
        jq -r --arg k "$key" '.[$k] // 0' "$TAC_STATE_FILE"
        ;;

    reset)
        reset_state
        echo "[TAC] State reset."
        ;;

    *)
        echo "Usage: $0 {record|build|verify|core4|status|get <key>|reset}" >&2
        exit 1
        ;;
esac

if [ "${TAC_STANDALONE:-0}" = "1" ]; then
    exit 0
fi