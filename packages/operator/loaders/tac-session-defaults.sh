#!/usr/bin/env bash
# TAC Session Defaults — sets the operating mode for every session.
# Sourced from ~/.hermes/jake/load.sh. Auto-fires on every Jake invocation.
# Makes TAC the default mode. No opt-in required.
#
# NOTE: do NOT use `set -u` here. When sourced from load.sh (which has set -u),
# the source inherits strict mode.

# When invoked directly (not sourced), print and exit cleanly.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    TAC_STANDALONE=1
fi

# Default thread type (Base = prompt → tools → review)
export TAC_MODE="${TAC_MODE:-active}"
export TAC_DEFAULT_THREAD="${TAC_DEFAULT_THREAD:-base}"

# Default agent role (most tasks: Builder + Verifier closed loop)
export TAC_DEFAULT_AGENT="${TAC_DEFAULT_AGENT:-builder+verifier}"
export TAC_CLOSED_LOOP="${TAC_CLOSED_LOOP:-on}"

# Default verification cadence (auto-suggest /tac-verify after N tool calls)
export TAC_VERIFY_THRESHOLD="${TAC_VERIFY_THRESHOLD:-3}"

# Default context (Core Four declaration requirement)
export TAC_REQUIRE_CORE4="${TAC_REQUIRE_CORE4:-on}"

# State file path (used by tracker and report — we NEVER write to it here)
TAC_STATE_DIR="${TAC_STATE_DIR:-$HOME/.jake/state/tac}"
TAC_STATE_FILE="$TAC_STATE_DIR/current.json"
mkdir -p "$TAC_STATE_DIR" 2>/dev/null || true

# Initialize state file ONLY if it doesn't exist (tracker owns the file)
if [ ! -f "$TAC_STATE_FILE" ]; then
    cat > "$TAC_STATE_FILE" <<EOF
{
  "session_start": "$(date +%s)",
  "tool_calls": 0,
  "builds": 0,
  "verifies": 0,
  "core4_declarations": 0,
  "last_verify_at": 0,
  "thread": "$TAC_DEFAULT_THREAD",
  "closed_loop": "$TAC_CLOSED_LOOP",
  "mode": "$TAC_MODE"
}
EOF
fi

# Print session contract (visible in every session banner)
if [ "${TAC_QUIET:-0}" != "1" ]; then
cat <<'EOF'

[TAC SESSION CONTRACT — ACTIVE]
  Mode    : active (no opt-in)
  Thread  : Base (default). Escalate to P/C/F/B/L/Z as needed.
  Agents  : Builder + Verifier (closed loop, on).
  Core 4  : declaration required at start of each major task.
  Verify  : auto-suggested after 3 tool calls without /tac-verify.
  Track   : compliance reported at session end → Obsidian.
EOF
fi

# Standalone exit
if [ "${TAC_STANDALONE:-0}" = "1" ]; then
    exit 0
fi