# Gate 7 independent coverage-scope audit

Final verdict: **PASS**

The initial proposal to lower the local 90% gate to a round 80% target was
rejected as post-hoc goalpost movement. The reviewer found that excluding the
byte-locked pinned v0.1 vendor namespace was legitimate, but Revision 2's
domain-evaluation coverage language could not justify changing Python code
coverage.

The reviewer required all of the following:

1. admit that 90% was a local unsupported precommit and retain the failed
   77.79% result;
2. separate domain evaluation-matrix coverage from Python code coverage;
3. exclude exactly the locked vendor namespace and no first-party/generated
   control code;
4. retain branch measurement, full tests, complete archive/candidate/vault
   negative-path gates, vendor lock, lint, and strict typing; and
5. use the measured first-party result as a non-regression ratchet.

The exact first-party measurement was 80.7671601615074%. A first attempt at
`fail_under = 80.76` was also rejected: at two-decimal precision it allowed a
small regression. The settled configuration uses `precision = 2` and
`fail_under = 80.77`, which Coverage.py compares at the measured displayed
baseline.

The reviewer reread the final configuration, Gate 7, and C14 and returned
**PASS**. Lowering the ratchet now requires another explicit reviewed contract
decision.
