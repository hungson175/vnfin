# How to use caching and retries

`vnfin` does not persist provider data. Runtime requests are fetched from providers, and offline tests
use synthetic fixtures.

## Reuse clients

The simplest and safest optimization is to reuse one domain client for related calls:

```python
import vnfin

fx = vnfin.fx.client()
usd = fx.get_rate("USD")
eur = fx.get_rate("EUR")  # shares the FX source's daily response cache where supported
```

## Transport options for advanced users

Sources are built on a shared transport that supports injectable HTTP, timeout, bounded retries,
and optional in-memory caching. Public factories expose `http_get` and `timeout`; source classes can
also be constructed directly with advanced transport kwargs when you need tests or custom behavior.

Guidelines:

- Use small retry budgets. Retries help transient timeouts/429/5xx; they do not fix bad requests.
- Keep cache TTLs short for market data unless you explicitly want stale-tolerant reads.
- Secret query/header values are redacted from errors and represented by hashes inside cache keys.
- Do not build a public data redistribution service on top of cached provider responses unless you
  have the provider's license.
