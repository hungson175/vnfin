# #191 — harden 2 non-blocking gaps in the #187 midnight-recovery test matrix (SPEC)

**Scope:** TEST-ONLY, `tests/test_indices.py`. No `vnfin/` change, no new token, snapshot frozen,
`_WARNING_TOKENS_180` unchanged. TDD: each hardened test must **fail-first against the mutation it
targets** (verify by hand-mutating the relevant `vnfin/` line, seeing the test go red, reverting).

Source: #187 Codex×2 review (`reviews/review-202606211004-187-midnight-recovery-codex-x2.md`). The #187
fix is correct + shipped (`ac7ca65`); this only makes future mutations caught DIRECTLY.

## (A) Equity-unaffected test exercises invariant-7 only indirectly
`test_equity_exact_timestamp_duplicate_unaffected_by_midnight_recovery` currently uses TWO identical
**VN-midnight** timestamps — so it proves "equity exact-timestamp keying is unaffected by recovery" only
*incidentally* (the midnight coincidence is the very thing recovery keys on).

**Harden:** rewrite the fixture to use a duplicate equity timestamp that is **NOT VN-midnight** (e.g. two
identical `09:00 +07` bars, or an open-only diff at a non-midnight time). The test must prove the equity
path **poisons** the duplicate (the #186 behavior) regardless of the clock — directly exercising
invariant-7 (recovery is gated to `dedup_by_date=True`, which is `False` for equities).
**Fail-first:** mutating the recovery gate so it also fires for equities must flip this test red.

## (B) `considered -= 1` back-out has no isolated kill
`test_index_recovered_date_not_charged_to_failover_threshold` is non-vacuous, but the **failover floor
dominates that fixture** — removing the `considered -= 1` back-out is NOT isolated-killed (the floor
already keeps the assertion true).

**Harden:** craft a fixture where the `considered -= 1` back-out is the **SOLE** reason the date serves —
the denominator change (not the floor) is what holds the failover fraction below the trip threshold. So
removing the back-out alone flips the served result to `InvalidData`.
**Fail-first:** deleting the `considered -= 1` line must flip this test red.

## Done
Both tests rewritten, full suite green, each verified fail-first against its target mutation. Report the
two mutations you used + that the suite is green. No `vnfin/` edit ships.
