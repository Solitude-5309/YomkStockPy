from __future__ import annotations

from typing import Any

import pandas as pd
import YomkApi

def ok(msg: str, data: Any) -> YomkApi.YomkResponse:
    return YomkApi.YomkResponse(YomkApi.ResStatus.eOk, msg, data)


def invalid(msg: str) -> YomkApi.YomkResponse:
    return YomkApi.YomkResponse(YomkApi.ResStatus.eInvalid, msg, None)


def error(msg: str) -> YomkApi.YomkResponse:
    return YomkApi.YomkResponse(YomkApi.ResStatus.eNo, msg, None)


def extract_dataframe(pkg: Any) -> pd.DataFrame:
    if isinstance(pkg, pd.DataFrame):
        return pkg
    if isinstance(pkg, dict):
        for key in ("df", "data", "table"):
            value = pkg.get(key)
            if isinstance(value, pd.DataFrame):
                return value
            if isinstance(value, list):
                return pd.DataFrame(value)
    raise ValueError("pkg must be a DataFrame or a dict containing df/data/table")


def extract_config(pkg: Any, service_key: str | None = None) -> dict[str, Any]:
    if not isinstance(pkg, dict):
        return {}
    config = dict(pkg.get("config") or {})
    if service_key and isinstance(config.get(service_key), dict):
        nested = dict(config.get(service_key) or {})
        merged = dict(config)
        merged.update(nested)
        return merged
    return config


def prepare_dataframe(df: pd.DataFrame, required_columns: set[str]) -> pd.DataFrame:
    if df.empty:
        raise ValueError("input DataFrame is empty")

    missing = sorted(required_columns - set(df.columns))
    if missing:
        raise ValueError(f"input DataFrame missing columns: {', '.join(missing)}")

    prepared = df.copy()
    prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
    for column in required_columns - {"date"}:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared = prepared.dropna(subset=list(required_columns))
    prepared = prepared.sort_values("date").reset_index(drop=True)
    if prepared.empty:
        raise ValueError("input DataFrame has no valid rows")
    return prepared


def score_by_threshold(value: float, threshold: float) -> float:
    if threshold <= 0:
        return 0.0
    return max(0.0, min(float(value) / float(threshold) * 100.0, 100.0))


def round_number(value: Any, digits: int = 4) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), digits)
