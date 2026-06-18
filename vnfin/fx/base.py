"""Common base for FX sources.

A source fetches the current rate set and returns :class:`FXRate` objects in the canonical
unit **VND per 1 unit of base**. The base class owns validation (supported quote, ISO-code
shape, positive/finite rate) and the per-rate construction so each adapter only implements
``get_rates``. ``unit`` declares the convention *family* for the failover unit-homogeneity guard.
"""
from __future__ import annotations

import math
from datetime import datetime

from ..exceptions import EmptyData, InvalidData
from ..transport import HttpDataSource
from .models import FXRate


class FXSource(HttpDataSource):
    NAME = "fx"
    QUOTE = "VND"
    #: convention family for the unit-homogeneity guard (all FX sources quote VND-per-foreign-unit)
    unit = "VND-per-foreign-unit"

    @property
    def name(self) -> str:
        return self.NAME

    # --- to be implemented by concrete adapters --------------------------- #
    def get_rates(self, quote: str = "VND") -> tuple[FXRate, ...]:  # pragma: no cover - abstract
        raise NotImplementedError

    # --- shared entry + validation ---------------------------------------- #
    def get_rate(self, base: str, quote: str = "VND") -> FXRate:
        b = self._normalize_ccy(base)
        self._check_quote(quote)
        for r in self.get_rates(quote):
            if r.base == b:
                return r
        raise EmptyData(f"{self.name}: no rate for {b}/{self.QUOTE}")

    def _check_quote(self, quote: str) -> None:
        if self._normalize_ccy(quote) != self.QUOTE:
            raise InvalidData(
                f"{self.name}: only quote {self.QUOTE} is supported in v0.2, got {quote!r}"
            )

    def _normalize_ccy(self, code) -> str:
        if not isinstance(code, str) or not code.strip().isalpha():
            raise InvalidData(f"{self.name}: invalid currency code {code!r}")
        return code.strip().upper()

    def _rate_unit(self, base: str) -> str:
        return f"{self.QUOTE} per 1 {base}"

    def _build_rate(
        self, base: str, rate: float, as_of_utc: datetime, *, bid=None, ask=None
    ) -> FXRate:
        if not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate <= 0:
            raise InvalidData(f"{self.name}: non-positive/invalid rate {rate!r} for {base}")
        return FXRate(
            base=base,
            quote=self.QUOTE,
            rate=float(rate),
            unit=self._rate_unit(base),
            as_of_utc=as_of_utc,
            source=self.name,
            bid=bid,
            ask=ask,
        )
