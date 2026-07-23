from __future__ import annotations

import pandas as pd
import YomkApi
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from boot.Boot import Boot

def build_stock_table() -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=90, freq="D")
    rows = []
    for idx, date in enumerate(dates):
        volume = 1000
        turn = 0.6
        close = 10.1
        if idx in (30, 65):
            volume = 2600
            turn = 2.4
            close = 10.6
        elif idx in (31, 32, 66, 67):
            volume = 2200
            turn = 2.0
            close = 10.4
        rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "open": 10.0,
                "high": 10.8,
                "low": 9.8,
                "close": close,
                "volume": volume,
                "turn": turn,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    YomkApi.boot(Boot([
        "/VolumeRatioScanService", 
        "/TurnoverScanService", 
        "/InstitutionScanService", 
        "/ActivityScoreService"]))
    df = build_stock_table()
    config = {
        "volume_ratio": {
            "lookback_days": 20,
            "target_ratio": 1.8,
        },
        "turnover": {
            "target_turnover": 2.0,
        },
        "institution": {
            "lookback_days": 20,
            "volume_ratio_threshold": 1.8,
            "price_gain_threshold": 3.0,
        },
        "weights": {
            "volume_ratio": 0.45,
            "turnover": 0.35,
            "institution": 0.20,
        },
        "active_score_threshold": 70,
        "inactive_score_threshold": 45,
        "inactive_days": 5,
        "cooldown_days": 10,
    }

    volume_resp = YomkApi.request("/VolumeRatioScanService/scan", {"df": df, "config": config})
    assert volume_resp.status == YomkApi.ResStatus.eOk, volume_resp.msg
    assert any(row["date"] == "2020-01-31" and row["is_breakout"] for row in volume_resp.data["rows"])

    turnover_resp = YomkApi.request("/TurnoverScanService/scan", {"df": df, "config": config})
    assert turnover_resp.status == YomkApi.ResStatus.eOk, turnover_resp.msg
    assert any(row["date"] == "2020-01-31" and row["is_breakout"] for row in turnover_resp.data["rows"])

    institution_resp = YomkApi.request("/InstitutionScanService/scan", {"df": df, "config": config})
    assert institution_resp.status == YomkApi.ResStatus.eOk, institution_resp.msg
    assert institution_resp.data["config"]["data_source"] == "price_volume_proxy"

    activity_resp = YomkApi.request("/ActivityScoreService/scan", {"df": df, "config": config})
    assert activity_resp.status == YomkApi.ResStatus.eOk, activity_resp.msg
    dates = [event["date"] for event in activity_resp.data["events"]]
    assert dates == ["2020-01-31", "2020-03-06"], dates
    print("ActivityScoreService test passed")
    print(activity_resp.data["events"])


if __name__ == "__main__":
    main()
