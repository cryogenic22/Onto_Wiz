# Engineering operating contract

The repository uses spec-driven, gated vertical slices.

1. Read `docs/CONTRACT_DECISIONS.md` and the relevant acceptance rows before
   changing code.
2. Search before adding a second implementation of a contract or helper.
3. Write a can-fail test first and observe it fail for the intended reason.
4. Keep adapters thin: only `ontowiz_authoring` may mutate authoring state.
5. Never add protected held-out prompts, answers, rubrics, mappings, vault
   credentials, or private receipts to this repository or its test fixtures.
6. Never add an activation, approval, release, or runtime-serve path.
7. A slice is complete only when its targeted tests, full tests, type checks,
   lint, source-immutability check, and adversarial review pass.

For source provenance, read `locks/source-origin.json`. The recorded Onto_Wiz
paths are read-only reference material during phase one.

