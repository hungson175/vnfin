# #163 — proposed close comment (post on APPROVE + after push)

**Disposition:** CLOSE as completed (v1 corporate-action / cash-dividend primitives shipped).
Total-return helpers were scoped OUT of #163 at triage (event-data primitives IN; total-return/
backtest OUT) — noted as a separate future item, not a blocker for closing.

Post via `bin/gh-maintainer` only, AFTER the push lands on master and reviewer APPROVE. Watermark
stays the reviewer's (I do NOT advance `state/last_seen.txt` / rm `state/PENDING`).

---

## Draft GitHub close comment (maintainer; factual; no secrets)

> **Status: shipped in v1 — closing as completed.**
>
> A new `vnfin.corp_actions` domain now provides clean-room **cash-dividend event primitives** sourced
> from the official Vietnam depository announcement pages (`vsd.vn`), runtime-fetch-only, no
> redistribution of source rows:
>
> - **Per-event fields:** ticker, exchange, record date (Ngày ĐKCC), pay date, `cash_per_share` (VND),
>   and `ratio_pct` — each typed and carrying explicit provenance + freshness.
> - **Discovery:** a bounded multi-hop BFS over an issuer's same-org announcement graph, with
>   visited-dedup + cycle guard and never-silent coverage disclosure
>   (`coverage_truncated_at_max_fetch`, `corp_action_fetch_incomplete`, `corp_action_seed_not_found`).
> - **Honest gaps are warnings, never silent:** depository pages do **not** publish an ex-date, so
>   `ex_date_unavailable` is always surfaced; partial crawls and parse degradations are tokenized.
>
> **Deliberate v1 scope decision — net-vs-gross dividend ratios.** Depository announcements state the
> dividend ratio in free Vietnamese prose that is sometimes gross (before personal income tax) and
> sometimes net (after withholding), with no machine-readable marker. Rather than ship a fragile
> free-text classifier (which produced repeated silent-wrong-data edge cases), v1 **serves `ratio_pct`
> only from an unambiguously tax-free line**; any net/tax/withholding signal on the ratio line yields
> `ratio_pct=None` + a dedicated `vsdc_ratio_tax_deferred` warning (distinct from `vsdc_parse_degraded`,
> which signals a parse fault). This guarantees a net rate is **never** silently served as gross. The
> reliable, directly-parsed fields (cash-per-share in VND, record/pay dates) are always served. A
> net-vs-gross classifier is deferred to a future version behind a committed phrasing test corpus.
>
> **Out of scope here:** total-return / backtest helpers (tracked separately as a distinct feature, per
> the triage on this issue) and any blind third-party scraping.
>
> If you hit a dividend announcement that parses incorrectly, please open a new issue with the depository
> announcement id — every fix ships with a fail-first regression test.

---

## Reviewer A's one NOTE (English after-tax) — validated fold, ready to apply post-verdict
Reviewer A (APPROVE_WITH_NOTES) flagged the gate misses English `after-tax`/`after tax`/`net of tax`/
`withholding tax` — rated NOTE not BLOCKER (VSDC is a Vietnamese govt depository; English ratio
phrasing doesn't occur). **Pre-validated read-only (no tree change while Codex×2 reads `56cde90`):**
adding `"tax"` to `_RATIO_NET_NOUNS` catches all 4 English variants AND is **0-over-withhold** on the
full clean-VN corpus (incl. the `thực được nhận` residual, which correctly still serves — qualifies the
cash). **Converge with reviewer on the consolidated verdict:** fold-before-push (1-line noun-set add +
1 fail-first English-after-tax test, surgical like prior M1 folds) vs defer-to-v2 (document alongside
bare-`đã trừ` / `thực được nhận`). Do NOT touch `vsdc.py` until the verdict lands.

## Notes for me (post-APPROVE checklist)
- IF folding the English-tax note: apply `_RATIO_NET_NOUNS += {"tax"}` + 1 fail-first test, re-run full
  suite + #180/#188 + snapshot on merged tree, THEN push. (Tuple stays 44 — no new token.)
- Push the whole `corp_actions` feature: `git push origin master` (origin at `f3cd479`; lands the
  feature + de-scope + backlog/memory commits). Verify green merged tree first.
- Close #163 with the comment above via `bin/gh-maintainer`.
- Then: #182 (post `tasks/182-close-comment.md` per reviewer's source-close ruling) → #155 design gate.
- Update backlog: #163 DONE+PUSHED+CLOSED with the push range + review ref.
