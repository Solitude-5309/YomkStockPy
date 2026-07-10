import YomkApi
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent / "src"
sys.path.append(str(src_dir))

from boot.Boot import Boot
YomkApi.boot(Boot(["/StockDataService", "/DataBaseService"]))

def get_stock_list():
    res = YomkApi.request("/DataBaseService/connect_sqlite_db", 
                      {
                        "db_name": "../config/stock.db"
                      })
    print(res.msg)
    
    res = YomkApi.request("/DataBaseService/get_stock_list", "")
    print(res.msg)
    print(res.data)

get_stock_list()
