import YomkApi
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boot.Boot import Boot
YomkApi.boot(Boot([
    "/StockDataService", 
    "/DataBaseService", 
    "/VolumeRatioScanService", 
    "/TurnoverScanService", 
    "/InstitutionScanService", 
    "/ActivityScoreService"]))

def active_scan_by_code(code, frequency):
    name = code.replace(".", "_") + "_" + frequency
    res = YomkApi.request("/DataBaseService/connect_sqlite_db", 
                      {
                        "db_name": "../config/stock.db"
                      })
    print(res.msg)
    
    res = YomkApi.request("/DataBaseService/get_stock_data", 
                      {
                        "name": name,
                        "start": "2025-01-01",
                        "end": "2026-06-26"
                      })
    print(res.msg)
    print(res.data)
    
    df = res.data
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

    activity_resp = YomkApi.request("/ActivityScoreService/scan", {"df": df, "config": config})
    if activity_resp.status == YomkApi.ResStatus.eOk:
        print("ActivityScoreService test passed")
        print(activity_resp.data["config"])

active_scan_by_code("sz.002313", "d")
