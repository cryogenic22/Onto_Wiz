# Acceptance gates

| Gate | Can-fail evidence required |
|---|---|
| G1 Contract | Candidate constants cannot be overridden; active/verified or approved artifacts reject; generated schemas match checked-in copies |
| G2 Workspace and slices | The scaffold is deterministic and adapter-neutral; strict validation passes the public BA/MR slices and covers normal/boundary/exception/conflict/missing/stale/abstain/tool-failure/adversarial classes |
| G3 Governed authoring and rights | Every canonical change comes from a confirmed full before/after proposal; crash recovery converges without persisting trust material; unclassified transfer or withdrawal blocks packaging |
| G4 Portable archives | Repeated/shuffled/EOL-varied `.owworkspace` and candidate-only `.owpack` builds are byte-identical; traversal, collision, device, link, undeclared-entry, and resource-bomb inputs reject |
| G5 Adapters, explorer, and examples | Codex-first and Claude-second scripted inputs yield the same canonical state and package digest; explorer renders only from the serialized context model; examples package through governed public APIs; neither adapter exposes evaluator commands |
| G6 Evaluation | Unapproved preregistration, unproven ACL isolation, invalid signatures, drift, wrong digest, incomplete trace/repetitions, unresolved scorer disagreement, or append conflict refuse without a score receipt; completed critical failures are immutably recorded with `gate_passed: false` |
| G7 Quality and source isolation | Targeted/full tests, complete archive/candidate/vault negative paths, lint, and strict typing pass; first-party statement/branch coverage cannot regress below 80.77%; the vendor and source-origin locks retain exact bytes and phase-one performs no source-repository write |

