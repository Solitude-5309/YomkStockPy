import YomkApi
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent / "src"
sys.path.append(str(src_dir))
from services.data.StockDataService import StockDataService
from services.data.DataBaseService import DataBaseService
from msgs.StockDataFrame import StockDataFrame
from services.strategy.ActivityScoreService import ActivityScoreService
from services.indicator.InstitutionScanService import InstitutionScanService
from services.indicator.TurnoverScanService import TurnoverScanService
from services.indicator.VolumeRatioScanService import VolumeRatioScanService

YomkApi.init(YomkApi.YomkServer(), ["YomkContext", "YomkFunctionPool", "YomkEventLoop"])
YomkApi.new_service(StockDataService, "/StockDataService")
YomkApi.new_service(DataBaseService, "/DataBaseService")
YomkApi.new_service(ActivityScoreService, "/ActivityScoreService")
YomkApi.new_service(VolumeRatioScanService, "/VolumeRatioScanService")
YomkApi.new_service(TurnoverScanService, "/TurnoverScanService")
YomkApi.new_service(InstitutionScanService, "/InstitutionScanService")

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
    if activity_resp.res_status == YomkApi.ResStatus.eOk:
        print("ActivityScoreService test passed")
        print(activity_resp.data["config"])

active_scan_by_code("sz.002313", "d")
