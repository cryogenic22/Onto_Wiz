# Gate 3 adversarial review — attempt 6

Status: **BLOCKED**

The reviewer confirmed all attempt-five cleanup, expiry-independent exact
recovery authentication, confirmation-session intent binding, external replay,
and handle-relative Windows lock findings were fixed.

One P1 remained: confirmation recovery required the prior session revision to
equal the transaction's current workspace revision. The live path correctly
accepts a digest-anchored session whose revision is older after intervening
non-session mutations. A crash after reserving such a valid confirmation became
unrecoverable.

Required disposition: mirror live session validation by rejecting only a future
prior-session revision, retain exact external session-digest/sequence/workspace
anchoring, and continue requiring the generated confirmation session to equal
the transaction's after revision with preserved stage/mission, current delta,
and empty questions. Add a crash-recovery case with a non-session mutation
between session update and confirmation.

Gate 4 remains unauthorized.
