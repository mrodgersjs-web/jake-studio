# jake-studio

> Local-first operator layer that routes work across people, models, tools, and verification gates — with the L10 self-evolving harness as the cognition/certainty substrate.

![status](https://img.shields.io/badge/status-public-studio-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![l10](https://img.shields.io/badge/L10-38%2F38%20tests-brightgreen)

## Employer summary

Jake Studio is how an FDE runs governed agent work on a real workstation: route the job, close the Builder+Verifier loop, and refuse "done" without proof. L10 provides certainty/cognition modules and scenario tests.

## Proof in 60 seconds

```bash
cd packages/l10
# if console scripts installed from this tree:
#   rig-l10-test
#   rig-l10 doctor
python3 -m compileall -q src 2>/dev/null || python3 -m compileall -q .
```

## Packages

| Path | Role |
|---|---|
| `packages/l10` | L10 harness — certainty, cognition, nocturne, agent_factory |
| `packages/operator` | Public operator loader scripts (TAC doctrine helpers) |
| `docs/operator` | Operator overview |
| `examples/closed-loop-builder-verifier` | Closed-loop pattern notes |

## Architecture

```text
Human goal
   │
   ▼
Jake operator routing (context, model, tools)
   │
   ├─► Builder agent
   │      │
   │      ▼
   └─► Verifier (read-only) ── fail → feedback loop (max 3)
              │
              ▼
         L10 certainty / scenarios
              │
              ▼
         ProofPacket / gate receipt
```

## Public boundary

Private mission payloads, GTM senders, family/minor flows, cookies, and client monorepos are excluded. See [docs/public-boundary.md](docs/public-boundary.md).

## Related

- [doctrine](https://github.com/mrodgersjs-web/doctrine)
- [proof-studio](https://github.com/mrodgersjs-web/proof-studio)
- [fde-portfolio](https://github.com/mrodgersjs-web/fde-portfolio)
