# Glossary

Internal names kept for compatibility, with what they mean in plain English.
Package and import names do not change; this page translates them.

| Internal name | Plain English | Where it lives |
| --- | --- | --- |
| jake | the operator layer: it routes a job to the right builder and verifier | this repository |
| L10 | the verification harness stack (levels of certainty checks) | `packages/l10` |
| chassis | the production runtime: harness registry, run packets, workflow state machine, state store, tool registry, policy engine | `packages/l10/src/chassis` |
| GEV | generator / evaluator / verifier: three separate roles so nothing reviews its own work | `packages/l10/src/chassis/gev.py` |
| nocturne | overnight batch runner (the nightly self-improvement loop) | `packages/l10/src/nocturne` |
| agent factory | deterministic agent stamp: builds agent definitions the same way every time | `packages/l10/src/agent_factory` |
| certainty engine | property testing, refutation, and small proof kernel | `packages/l10/src/certainty_engine` |
| cognition stack | taste scoring, multi-model council, strategy helpers | `packages/l10/src/cognition_stack` |
| ProofPacket | a sealed record of a run: goal, artifacts, transitions, verdict | `packages/l10/src/chassis/packet.py` |
| Builder / Verifier | the split between the agent that makes the change and the separate one that re-checks it | doctrine across this repo |
| TAC | coding-agent playbook (tactical agentic coding practices) | `packages/operator/loaders` |
| FDE | forward-deployed engineer: the operator running the loop on real jobs | docs and READMEs |
| steward score | repo health score used by internal tooling | not shipped in this repo |

Related reading: [architecture](architecture.md) for how the parts fit,
and `packages/l10/docs/chassis/spec.md` for the chassis contract.
