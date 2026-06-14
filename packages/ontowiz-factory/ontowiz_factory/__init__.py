"""ontowiz-factory — the secret sauce (Tier B, INTERNAL ONLY).

NEVER packaged into a client artifact. Submodules (ported F2–F4):

    mining/    — SpecOmagic's 9 extractors + new code/SQL rule miner   (Loop 1)
    forge/     — Domain Forge missions, scoring, InterviewAgent        (Loop 3)
    steward/   — signal→action curation loops, EWMA reliability        (Loop 2/5)
    evals/     — eval gate, agent-lift benchmark                       (Loop 4)
    compiler/  — governed artifacts → compiled CTX Domain Packs        (the product)

The compiler is the only path that produces what crosses the A/B boundary. The
runtime (Tier A) consumes its output; it never imports this.
"""

__version__ = "0.1.0"
