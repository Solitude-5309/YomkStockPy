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


class VolumeRatioScanService(YomkApi.YomkService):
    def __init__(self, server):
        super().__init__(server)
        self.set_name("/VolumeRatioScanService")

    def init(self):
        self.install_func("/scan", self.scan)

    def scan(self, pkg: Any) -> YomkApi.YomkResponse:
        try:
            df = prepare_dataframe(extract_dataframe(pkg), {"date", "volume"})
            config = extract_config(pkg, "volume_ratio")
            lookback_days = max(1, int(config.get("lookback_days", 20)))
            target_ratio = max(0.01, float(config.get("target_ratio", 1.8)))

            previous_average = (
                df["volume"]
                .shift(1)
                .rolling(lookback_days, min_periods=lookback_days)
                .mean()
            )
            volume_ratio = (df["volume"] / previous_average).replace(
                [float("inf"), -float("inf")], pd.NA
            )

            rows = []
            for index, row in df.iterrows():
                ratio = volume_ratio.iloc[index]
                if pd.isna(ratio):
                    continue
                score = score_by_threshold(float(ratio), target_ratio)
                rows.append(
                    {
                        "date": row["date"].strftime("%Y-%m-%d"),
                        "position": int(index),
                        "score": round(score, 2),
                        "volume_ratio": round_number(ratio),
                        "volume": round_number(row["volume"], 2),
                        "previous_average_volume": round_number(previous_average.iloc[index], 2),
                        "is_breakout": bool(float(ratio) >= target_ratio),
                    }
                )

            return ok(
                "volume ratio scanned",
                {
                    "indicator": "volume_ratio",
                    "rows": rows,
                    "config": {
                        "lookback_days": lookback_days,
                        "target_ratio": target_ratio,
                    },
                },
            )
        except ValueError as exc:
            return invalid(str(exc))
        except Exception as exc:
            return error(f"volume ratio scan failed: {exc}")
