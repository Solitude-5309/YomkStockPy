import YomkApi
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
service_dir = current_dir.parent / "src/services"
sys.path.append(str(service_dir))
msgs_dir = current_dir.parent / "src/msgs"
sys.path.append(str(msgs_dir))
import StockDataService
import DataBaseService
import ActiveDateScanService

YomkApi.init(YomkApi.YomkServer(), ["YomkContext", "YomkFunctionPool", "YomkEventLoop"])
YomkApi.new_service(StockDataService.StockDataService, "/StockDataService")
YomkApi.new_service(DataBaseService.DataBaseService, "/DataBaseService")
YomkApi.new_service(ActiveDateScanService.ActiveDateScanService, "/ActiveDateScanService")

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
    
    resp = YomkApi.request(
        "/ActiveDateScanService/scan",
        {
            "df": res.data,
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
    print("ActiveDateScanService test passed")
    print(resp.data)

active_scan_by_code("sz.002313", "d")
