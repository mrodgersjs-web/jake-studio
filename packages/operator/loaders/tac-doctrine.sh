#!/usr/bin/env bash
# TAC Doctrine Loader — Tactical Agentic Coding (IndyDevDan → RIG)
#
# Sources TAC doctrine into the Jake/Hermes/Claude/Codex session at startup.
# Auto-loads from ~/.hermes/jake/loaders/tac-doctrine.sh when sourced, OR
# can be invoked directly: ~/.hermes/jake/loaders/tac-doctrine.sh
#
# Doctrine precedence: RIG Unified > Convergence Core > Jake PAI > TAC

# When invoked directly (not sourced), print and exit cleanly.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    TAC_STANDALONE=1
fi

set -u

TAC_DOCTRINE_INDEX="${TAC_DOCTRINE_INDEX:-$HOME/.rig/agent-doctrine/TAC/TAC-DOCTRINE.md}"
TAC_DOCTRINE_FULL="${TAC_DOCTRINE_FULL:-$HOME/.rig/agent-doctrine/TAC/TAC-DOCTRINE-COMPLETE.md}"
TAC_CURSOR_RULE="${TAC_CURSOR_RULE:-$HOME/.cursor/rules/tac-doctrine.mdc}"
TAC_RAW_SOURCE="${TAC_RAW_SOURCE:-$HOME/Desktop/output/tac-doctrine}"

# Probe each artifact
tac_compact="missing";  [ -f "$TAC_DOCTRINE_INDEX" ] && tac_compact="loaded"
tac_full="missing";     [ -f "$TAC_DOCTRINE_FULL" ] && tac_full="loaded"
tac_cursor="missing";   [ -f "$TAC_CURSOR_RULE" ] && tac_cursor="loaded"
tac_raw="missing";      [ -d "$TAC_RAW_SOURCE" ] && tac_raw="loaded"

cat <<'EOF'

----------------------------------------------------------------
  TAC DOCTRINE  —  Tactical Agentic Coding (IndyDevDan → RIG)
----------------------------------------------------------------
  Role         : Tactical layer beneath RIG Unified + Jake PAI
  Mission      : Build the system that builds the system
  Prime Law    : Stop coding. Start templating. Earn ZTE trust.

  Core Four    : Context · Model · Prompt · Tools
  Leverage Pts : 12 leverage points (in-agent + through-agent)
  Tactics      : 8 core (Hello → Agentic Layer) + 6 Horizon (Context → Singularity)
  Threads      : Base · P · C · F · B · L · Z (progress → zero-touch)
  Closing Loop : Builder + Verifier · Confidence Ladder PERFECT→VERIFIED→PARTIAL→FEEDBACK→FAILED
  RIG Team     : Scout · Planner · Builder · Reviewer · Verifier · Documenter · Red Team

  Stack:
    RIG Unified  ──┐
    Convergence  ──┼── TAC ── Agent Team
    Jake PAI     ──┘

  Doctrine precedence: RIG Unified > Convergence > Jake PAI > TAC > Agent-specific
  TAC never overrides RIG prime directives (proof, gates, audit, anti-generic).

EOF

printf '  Status:\n'
printf '    compact     : %s  (%s)\n' "$tac_compact" "$TAC_DOCTRINE_INDEX"
printf '    full        : %s  (%s)\n' "$tac_full" "$TAC_DOCTRINE_FULL"
printf '    cursor rule : %s  (%s)\n' "$tac_cursor" "$TAC_CURSOR_RULE"
printf '    raw source  : %s  (%s)\n' "$tac_raw" "$TAC_RAW_SOURCE"

cat <<'EOF'

  Quick Refs:
    /jake tac                          Show this loader
    /jake tac status                   Probe doctrine presence
    cat ~/.rig/agent-doctrine/TAC/TAC-DOCTRINE.md
    cat ~/.rig/agent-doctrine/TAC/TAC-DOCTRINE-COMPLETE.md
    cat ~/.cursor/rules/tac-doctrine.mdc

  Doctrine loaded for this session. Stack with RIG Unified + Jake PAI.
----------------------------------------------------------------
EOF
# Always informational; never gate.
# Note: do NOT exit here — we're sourced from load.sh and must let the parent
# banner continue. Only exit when run standalone.
if [ "${TAC_STANDALONE:-0}" = "1" ]; then
    exit 0
fi