import YomkApi
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boot.Boot import Boot
YomkApi.boot(Boot(["/StockDataService", "/DataBaseService"]))

def get_stock_by_code(code, frequency, start, end):
    name = code.replace(".", "_") + "_" + frequency
    res = YomkApi.request("/DataBaseService/connect_sqlite_db", 
                      {
                        "db_name": "../config/stock.db"
                      })
    print(res.msg)
    
    res = YomkApi.request("/DataBaseService/get_stock_data", 
                      {
                        "name": name,
                        "start": start,
                        "end": end
                      })
    print(res.msg)
    print(res.data)

get_stock_by_code("sh.600222", "d", "2026-01-01", "2026-01-31")
