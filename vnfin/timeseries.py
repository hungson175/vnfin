"""Shared time-series result base/mixin for every vnfin domain.

Before this module each domain's result container (``PriceHistory``,
``CryptoHistory``, ``NavHistory``, ``GoldHistory``, ``IndicatorSeries``) carried
its own near-identical ``__len__`` / ``__iter__`` / ``to_dataframe`` plus the same
provenance fields (``source`` / ``fetched_at_utc`` / ``warnings``). They differed
only in (a) which attribute holds the row tuple, (b) how a single row maps to a
DataFrame record, and (c) which metadata to stamp onto ``df.attrs``.

``TimeSeriesResult`` is a small **mixin** (not a deep dataclass hierarchy — the
domain containers stay plain frozen dataclasses) that factors the shared logic.
A concrete result class declares three things and gets ``__len__`` / ``__iter__``
/ ``to_dataframe`` for free:

* ``_items_attr`` — name of the field holding the row tuple
  (e.g. ``"bars"`` / ``"points"`` / ``"funds"``).
* ``_row_record(item)`` — map ONE row object to a flat ``dict`` for the DataFrame.
* ``_df_attrs()`` — the metadata dict stamped onto ``df.attrs``.

It also defines the index column name via ``_index_column`` (the field used as the
DataFrame index, e.g. ``"time"`` / ``"date"``) and the explicit column order via
``_df_columns``. Domains keep full control of their schema; the mixin only removes
the boilerplate.

This is intentionally minimal: it never touches the typed row models, never adds
required fields, and never changes any existing public behavior — every existing
result class produces byte-identical DataFrames after adopting it.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .exceptions import InvalidData

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd


class TimeSeriesResult:
    """Mixin supplying ``__len__`` / ``__iter__`` / ``to_dataframe`` for a series.

    Subclasses (concrete frozen dataclasses) must set the class attributes
    ``_items_attr``, ``_index_column``, ``_df_columns`` and implement
    ``_row_record`` and ``_df_attrs``. See the module docstring.
    """

    # --- subclass contract (override) ------------------------------------- #
    #: Name of the instance attribute holding the row tuple.
    _items_attr: str = "items"
    #: DataFrame index column name (a key produced by ``_row_record``).
    _index_column: str = "time"
    #: Full ordered list of DataFrame columns (including the index column).
    _df_columns: tuple[str, ...] = ()

    def _row_record(self, item) -> dict:  # pragma: no cover - overridden
        """Map one row object to a flat dict keyed by ``_df_columns``."""
        raise NotImplementedError

    def _df_attrs(self) -> dict:  # pragma: no cover - overridden
        """Return the metadata dict stamped onto ``df.attrs``."""
        raise NotImplementedError

    # --- shared behavior -------------------------------------------------- #
    @property
    def _items(self) -> tuple:
        return getattr(self, self._items_attr)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def to_dataframe(self) -> "pd.DataFrame":
        """Return a pandas DataFrame indexed by ``_index_column``.

        Metadata from :meth:`_df_attrs` is attached to ``df.attrs`` so downstream
        code keeps provenance after a merge/concat.

        Raises :class:`~vnfin.exceptions.InvalidData` if the index contains duplicate
        keys, because duplicate observations are a provider contract violation that
        should trigger failover rather than silently dropping or duplicating rows.
        """
        import pandas as pd

        rows = [self._row_record(item) for item in self._items]
        df = pd.DataFrame(rows, columns=list(self._df_columns))
        if not df.empty:
            index_col = self._index_column
            if df[index_col].duplicated().any():
                dups = df[index_col][df[index_col].duplicated()].unique().tolist()
                raise InvalidData(f"duplicate observation keys in series: {dups}")
            df = df.set_index(index_col)
        df.attrs.update(self._df_attrs())
        return df
