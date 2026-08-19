# Gate 3 adversarial review — attempt 5

Status: **BLOCKED**

The reviewer confirmed that provider-side authoring high-water/replay defense,
reservation/finalization ordering, full proposal live checks, update-session
reference checks, and Windows handle-relative lock creation were materially
fixed. Three recovery P1s remained:

1. **Finalized cleanup was not crash-idempotent.** Recovery loaded every stage
   before inspecting provider-finalized state. A crash after deleting one stage
   but before deleting the journal could permanently block the workspace.
2. **Credential expiry was reapplied during exact recovery.** A credential valid
   when the provider atomically reserved a transaction could expire during
   downtime, preventing the exact pending or finalized transaction from
   recovering or cleaning up.
3. **Confirmation session transform was incomplete.** Recovery validated the
   target/proposal/actor/evidence but did not require the exact live confirmation
   session change, allowing a provider-attested journal to install a dangling or
   altered session.

Required disposition: branch on provider-finalized authorization before loading
stages; verify local after-state directly and make every cleanup unlink
idempotent with kill points; add a distinct provider recovery-authentication
contract that attests reserve-time credential validity without reapplying
current expiry; and require the exact default/before-to-confirmed session
transformation plus current references during confirmation recovery.

Gate 4 remains unauthorized.
