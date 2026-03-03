"""Utility for JSON encoding of MySQL query results.

The QWeather spider stores a variety of Python types in MySQL:
- `date` / `datetime` for forecast dates and update timestamps
- `timedelta` (rare, but may appear in calculations)
- `Decimal` for precise numeric fields such as precipitation
These types are not JSON‑serialisable by the default `json` module.

The module provides:
1. `encode_obj` – a small helper that converts a single object to a JSON‑compatible
   primitive (str, int, float).
2. `MySQLJSONEncoder` – a `json.JSONEncoder` subclass that delegates to
   `encode_obj` for unknown types, falling back to the default behaviour.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any


def encode_obj(obj: Any) -> Any:
    """Convert non‑JSON types produced by MySQL queries to JSON‑compatible values.

    * ``date`` and ``datetime`` → ISO‑8601 string (e.g. ``"2026-03-03"``).
    * ``timedelta`` → total seconds as ``int``.
    * ``Decimal`` → ``float`` when possible, otherwise ``str``.
    Raises ``TypeError`` for unsupported types.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, timedelta):
        return int(obj.total_seconds())
    if isinstance(obj, Decimal):
        # Preserve precision when possible; JSON numbers are float, so we try to
        # cast to float but fall back to string if the conversion would lose data.
        try:
            return float(obj)
        except (ValueError, OverflowError):
            return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class MySQLJSONEncoder(json.JSONEncoder):
    """JSONEncoder that knows how to handle MySQL‑specific Python types.

    Used by FastAPI ``JSONResponse`` to ensure the response body can be
    serialised without manual conversion of each field.
    """

    def default(self, o: Any) -> Any:  # noqa: D401 (docstring inherited)
        try:
            return encode_obj(o)
        except TypeError:
            return super().default(o)
