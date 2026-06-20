"""Private provider-boundary + typed-result contract layer (#refactor).

This package centralizes the malformed-provider-data policy that adapters and
failover result validators previously implemented ad hoc. It is **private**
(underscore) on purpose: no public API surface is added during the refactor, and
the internals may iterate without SemVer burden. Public ``vnfin.validation``
stays stable.

Phase 1 (this commit) ships only the provider-boundary *primitives* — field
access, key/enum canonicalization, object/list/duplicate guards — with tests and
**no adapter behavior change**. Later phases build provider-contract classes and
typed-result rule lists on top.

See ``tasks/refactor-provider-contracts.md`` for the full plan.
"""
from __future__ import annotations

from .errors import contract_error
from .fields import (
    MISSING,
    has_present_key,
    optional_present,
    optional_present_non_empty_str,
    require_non_empty_str,
    require_present,
)
from .keys import (
    canonical_country_iso3,
    canonical_crypto_asset,
    canonical_crypto_pair,
    canonical_enum_tag,
    canonical_fund_code,
    canonical_provider_key,
    canonical_security_symbol,
)
from .index_registry import is_known_index, is_value_history_index
from .results import non_empty_reason, result_type_reason
from .rows import reject_duplicate, require_list, require_object
from .timeseries import (
    row_object_and_aware_datetime_reason,
    row_object_and_plain_date_reason,
    strictly_ascending_reason,
)

__all__ = [
    "contract_error",
    "MISSING",
    "has_present_key",
    "require_present",
    "optional_present",
    "require_non_empty_str",
    "optional_present_non_empty_str",
    "canonical_provider_key",
    "canonical_enum_tag",
    "canonical_security_symbol",
    "canonical_fund_code",
    "canonical_country_iso3",
    "canonical_crypto_asset",
    "canonical_crypto_pair",
    "require_object",
    "require_list",
    "reject_duplicate",
    "result_type_reason",
    "non_empty_reason",
    "row_object_and_plain_date_reason",
    "row_object_and_aware_datetime_reason",
    "strictly_ascending_reason",
]
