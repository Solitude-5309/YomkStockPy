from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import YomkApi

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from services.ActiveDateScanService import ActiveDateScanService


def build_stock_table() -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=90, freq="D")
    rows = []
    for idx, date in enumerate(dates):
        volume = 1000
        turn = 0.6
        if idx in (30, 65):
            volume = 2600
            turn = 2.4
        elif idx in (31, 32, 66, 67):
            volume = 2200
            turn = 2.0
        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "open": 10.0,
                "high": 10.5,
                "low": 9.8,
                "close": 10.2,
                "volume": volume,
                "turn": turn,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    YomkApi.init(YomkApi.YomkServer(), ["YomkContext", "YomkFunctionPool", "YomkEventLoop"])
    YomkApi.new_service(ActiveDateScanService, "/ActiveDateScanService")

    resp = YomkApi.request(
        "/ActiveDateScanService/scan",
        {
            "df": build_stock_table(),
            "config": {
                "lookback_days": 20,
                "inactive_days": 5,
                "volume_ratio_threshold": 1.8,
                "turnover_threshold": 2.0,
                "inactive_volume_ratio_max": 1.1,
                "inactive_turnover_max": 1.0,
                "min_score": 70,
                "cooldown_days": 10,
            },
        },
    )

    assert resp.res_status == YomkApi.ResStatus.eOk, resp.msg
    dates = [event["date"] for event in resp.data["events"]]
    assert dates == ["2020-01-31", "2020-03-06"], dates
    print("ActiveDateScanService test passed")
    print(resp.data)


if __name__ == "__main__":
    main()
