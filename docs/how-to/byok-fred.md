# How to use optional FRED BYOK

The default macro chain needs no key. FRED is an optional bring-your-own-key source for users who
already have a FRED API key.

```bash
export FRED_API_KEY=...
```

Then construct/use the FRED source explicitly when you need it. The no-key default chain remains
World Bank → IMF DataMapper → DBnomics.

Rules:

- `vnfin` never ships a FRED key.
- Missing keys are treated as a normal source-unavailable condition.
- Error messages redact API keys, including exception context/traceback paths guarded by tests.
