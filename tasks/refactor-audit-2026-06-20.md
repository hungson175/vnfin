# Phase R0 — post-knowledge refactor audit (2026-06-20)

Audit-only (no source/test edits, no GitHub actions, no push) per the tech-lead directive
`~/tools/vnfin-oss-reviewer/reviews/review-202606200812-post-knowledge-refactor-directive.md`.
Audited against the distilled bug-knowledge invariants (provider-parser contract, failover-
result contract, financial-data integrity) and the new `docs/architecture/` docs.

## Baseline gates (before audit)

```
git status --short --branch         -> ## master  (clean tree, no changes)
python -m pytest -q                 -> 2705 passed
python -m pytest \
  tests/test_public_api_surface.py \
  tests/test_docs_contract.py \
  tests/test_no_secrets.py -q       -> passed (public-API + docs-contract + no-secrets)
git diff --check                    -> clean (no whitespace/conflict markers)
```

## Files inspected (read + pattern-swept)

- Architecture docs: `docs/architecture/{system-overview,provider-contracts,failover-and-validation,data-domains,maintainer-workflow}.md`.
- Contract layer: `vnfin/_contracts/{fields,keys,rows,results,timeseries,errors}.py`.
- Adapters/clients swept for ad-hoc parsing: `vnfin/fx/{vietcombank,open_er_api}.py`,
  `vnfin/sources/{udf,ssi}.py`, `vnfin/gold/{vn,gold_api,stooq,failover}.py`,
  `vnfin/funds/fmarket.py`, `vnfin/crypto/{binance,coinbase}.py`,
  `vnfin/macro/{worldbank,imf,dbnomics,fred}.py`, `vnfin/fundamentals/{vndirect,cafef,models}.py`,
  `vnfin/{client,crypto/client,validation,coerce,transport}.py`, `vnfin/news/alpha_vantage.py`,
  `vnfin/{diagnostics,liquidity}.py`.
- Sweeps: `.get(...) or` truthiness-collapse; broad `str(raw).strip()`; raw `int(`/`float(`;
  `date.fromisoformat`/`strptime`; per-domain duplicated validators; transport secret/redaction.

## Headline finding

The major provider-contract refactor (Phases 0–6) is complete and **no distilled-invariant
violations remain**: every malformed-shape path traced in the sweep is already rejected or
fail-soft-skipped (e.g. UDF volume `is_integer()` guard #120; gold `_price` bool+try guard;
Vietcombank CurrencyCode `_VCB_CCY.fullmatch` + duplicate seen-set #28; cafef/vndirect keys via
`canonical_provider_key`). The remaining candidates are **consistency / single-source-of-truth**
improvements, not correctness gaps. Per the directive (no blind rewrites; slice only on invariant
violation), the recommendation is **defer most; no `do-now` required**.

## Candidate refactor slices

| # | Candidate | Where | Invariant violated? | Risk | Benefit | Rec |
|---|-----------|-------|--------------------|------|---------|-----|
| C1 | FX domain not on `_contracts`; duplicated currency-code validation | `fx/vietcombank.py` (`(get("CurrencyCode") or "").strip().upper()` + `_VCB_CCY`), `fx/open_er_api.py` (`_normalize_ccy`) | No — malformed codes are skipped/validated; just ad-hoc + duplicated | Low–Med (FX is well-tested) | DRY: one shared `canonical_currency_code` (ISO-4217 3-letter) used by both FX adapters; aligns FX with every other domain on the contract layer | **defer** (optional small slice; functionally correct today) |
| C2 | `sources/ssi.py` `parsed.get("data") or {}` truthiness on the data container | `sources/ssi.py:70` | No — downstream validates the parsed shape | Low | Minor: present-`null` `data` collapses to `{}` then fails downstream; a `require_object`/explicit guard would localize the error | **defer** |
| C3 | `gold/stooq.py` `float(raw)` raw coercion (opt-in source) | `gold/stooq.py:124` | No — wrapped in the source's parse/except path | Low | Consistency with `parse_provider_float`; stooq is opt-in/non-default so low reach | **defer** |
| C4 | CafeF line-item **name** fallback uses `str(code).strip()` | `fundamentals/cafef.py:539,543` | No — display NAME fallback, not an identity key (the Code key is canonical) | Low | Cosmetic only | **do-not-do** |
| C5 | `StatementType`/`Period` public coercion via `str(x).strip().lower()/upper()` | `fundamentals/models.py:31,46` | No — intentional public enum coercion (accepts enum or its value) | — | Changing it risks the documented public coercion contract | **do-not-do** |
| C6 | Error-envelope message extraction `get("msg") or get("code")` etc. | `crypto/binance.py:265`, `crypto/coinbase.py:306`, `funds/fmarket.py:464`, `macro/worldbank.py:243-245` | No — builds a human error string, never an identity/value | — | None (these are correct uses of `or` for a fallback message) | **do-not-do** |

## Guard tests for the only plausible `do-now` (C1), IF later approved

A future FX contract slice (one logical commit, focused tests) would be guarded by:
- `tests/test_fx.py`: Vietcombank present-null/blank/non-3-letter/duplicate `CurrencyCode`
  rejected-or-skipped (unchanged behavior); OpenER `_normalize_ccy` malformed codes; both
  adapters route through the shared `canonical_currency_code`.
- a `tests/test_contract_keys.py` matrix for the new `canonical_currency_code` (accept `USD`/
  `vnd`→`VND`; reject ``, `US`, `USDX`, `12A`, internal space/punct, non-string, control chars).
- gates: full suite + public-API snapshot (if a new public helper) + no-secrets; FX behavior
  must stay byte-equal except fail-closed.

## R0 confirmation

- No source or test files were modified during R0. The only new file is this report
  (`tasks/refactor-audit-2026-06-20.md`); `git status` otherwise matches the clean baseline.
- Recommendation to tech-lead: **accept the audit; no `do-now` refactor is required.** C1 (FX
  currency-code contract) is the single small slice worth considering — convert to an
  implementation spec only if the consistency/DRY benefit is judged worth the change; C2/C3
  defer; C4/C5/C6 do-not-do.
