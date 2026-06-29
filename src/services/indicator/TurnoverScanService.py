from __future__ import annotations

from typing import Any

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


class TurnoverScanService(YomkApi.YomkService):
    def __init__(self, server):
        super().__init__(server)
        self.set_name("/TurnoverScanService")

    def init(self):
        self.install_func("/scan", self.scan)

    def scan(self, pkg: Any) -> YomkApi.YomkResponse:
        try:
            df = prepare_dataframe(extract_dataframe(pkg), {"date", "turn"})
            config = extract_config(pkg, "turnover")
            target_turnover = max(0.01, float(config.get("target_turnover", 3.0)))

            rows = []
            for index, row in df.iterrows():
                turnover = float(row["turn"])
                score = score_by_threshold(turnover, target_turnover)
                rows.append(
                    {
                        "date": row["date"].strftime("%Y-%m-%d"),
                        "position": int(index),
                        "score": round(score, 2),
                        "turnover": round_number(turnover),
                        "is_breakout": bool(turnover >= target_turnover),
                    }
                )

            return ok(
                "turnover scanned",
                {
                    "indicator": "turnover",
                    "rows": rows,
                    "config": {
                        "target_turnover": target_turnover,
                    },
                },
            )
        except ValueError as exc:
            return invalid(str(exc))
        except Exception as exc:
            return error(f"turnover scan failed: {exc}")
