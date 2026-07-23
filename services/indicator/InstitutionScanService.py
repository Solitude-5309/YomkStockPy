from __future__ import annotations

from typing import Any

import pandas as pd
import YomkApi

from utils.utils import (
    error,
    extract_config,
    extract_dataframe,
    invalid,
    ok,
    prepare_dataframe,
    round_number,
    score_by_threshold,
)


class InstitutionScanService(YomkApi.YomkService):
    DEFAULT_COLUMNS = (
        "institution_net_buy",
        "institution_net_inflow",
        "main_net_inflow",
        "net_inflow",
    )

    def __init__(self, server):
        super().__init__(server)
        self.set_name("/InstitutionScanService")

    def init(self):
        self.install_func("/scan", self.scan)

    def scan(self, pkg: Any) -> YomkApi.YomkResponse:
        try:
            raw_df = extract_dataframe(pkg)
            config = extract_config(pkg, "institution")
            institution_column = self._find_institution_column(raw_df, config)
            if institution_column:
                return self._scan_institution_column(raw_df, institution_column, config)
            return self._scan_proxy(raw_df, config)
        except ValueError as exc:
            return invalid(str(exc))
        except Exception as exc:
            return error(f"institution scan failed: {exc}")

    def _find_institution_column(self, df: pd.DataFrame, config: dict[str, Any]) -> str | None:
        configured = config.get("institution_column")
        if configured and configured in df.columns:
            return str(configured)
        for column in self.DEFAULT_COLUMNS:
            if column in df.columns:
                return column
        return None

    def _scan_institution_column(
        self,
        df: pd.DataFrame,
        column: str,
        config: dict[str, Any],
    ) -> YomkApi.YomkResponse:
        prepared = prepare_dataframe(df, {"date", column})
        target_value = max(0.01, float(config.get("target_value", 1.0)))

        rows = []
        for index, row in prepared.iterrows():
            value = max(0.0, float(row[column]))
            score = score_by_threshold(value, target_value)
            rows.append(
                {
                    "date": row["date"].strftime("%Y-%m-%d"),
                    "position": int(index),
                    "score": round(score, 2),
                    "institution_value": round_number(row[column], 4),
                    "institution_column": column,
                    "data_source": "column",
                    "is_breakout": bool(value >= target_value),
                }
            )
        return ok(
            "institution scanned",
            {
                "indicator": "institution",
                "rows": rows,
                "config": {
                    "institution_column": column,
                    "target_value": target_value,
                    "data_source": "column",
                },
            },
        )

    def _scan_proxy(self, df: pd.DataFrame, config: dict[str, Any]) -> YomkApi.YomkResponse:
        prepared = prepare_dataframe(df, {"date", "open", "close", "volume"})
        lookback_days = max(1, int(config.get("lookback_days", 20)))
        volume_ratio_threshold = max(0.01, float(config.get("volume_ratio_threshold", 1.8)))
        price_gain_threshold = max(0.01, float(config.get("price_gain_threshold", 3.0)))

        previous_average = (
            prepared["volume"]
            .shift(1)
            .rolling(lookback_days, min_periods=lookback_days)
            .mean()
        )
        volume_ratio = (prepared["volume"] / previous_average).replace(
            [float("inf"), -float("inf")], pd.NA
        )
        price_gain_pct = (prepared["close"] - prepared["open"]) / prepared["open"] * 100.0

        rows = []
        for index, row in prepared.iterrows():
            ratio = volume_ratio.iloc[index]
            if pd.isna(ratio):
                continue
            price_gain = max(0.0, float(price_gain_pct.iloc[index]))
            volume_score = score_by_threshold(float(ratio), volume_ratio_threshold)
            price_score = score_by_threshold(price_gain, price_gain_threshold)
            score = volume_score * 0.5 + price_score * 0.5
            rows.append(
                {
                    "date": row["date"].strftime("%Y-%m-%d"),
                    "position": int(index),
                    "score": round(score, 2),
                    "volume_ratio": round_number(ratio),
                    "price_gain_pct": round_number(price_gain),
                    "data_source": "price_volume_proxy",
                    "is_breakout": bool(
                        float(ratio) >= volume_ratio_threshold
                        and price_gain >= price_gain_threshold
                    ),
                }
            )
        return ok(
            "institution proxy scanned",
            {
                "indicator": "institution",
                "rows": rows,
                "config": {
                    "lookback_days": lookback_days,
                    "volume_ratio_threshold": volume_ratio_threshold,
                    "price_gain_threshold": price_gain_threshold,
                    "data_source": "price_volume_proxy",
                },
            },
        )
