import YomkApi
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msgs.YomkMsgs import StockDataFrame

from boot.Boot import Boot
YomkApi.boot(Boot(["/StockDataService", "/DataBaseService"]))

def save_stock_by_code(code, frequency):
    res = YomkApi.request("/DataBaseService/connect_sqlite_db", 
                      {
                        "db_name": "../config/stock.db"
                      })
    print(res.msg)
    name = code.replace(".", "_") + "_" + frequency
    
    res = YomkApi.request("/DataBaseService/table_is_exists", 
                      {
                        "name": name
                      })
    print(res.msg)
    print(res.data)
    
    if res.data:
        print("Table already exists")
        return

    res = YomkApi.request("/DataBaseService/create_table", 
                        {
                            "name": name
                        })
    print(res.msg)
    
    res = YomkApi.request("/StockDataService/get_stock", 
                          {"code": code, 
                           "start_date": "1990-01-01", 
                           "end_date": "2026-12-31",
                           "query_field": ["date","open","high","low","close","volume","turn"],
                           "frequency": frequency,
                           "adjustflag": "2"
                          })
    df = res.data

    sd = StockDataFrame()
    sd.table_name = name
    sd.df = df
    res = YomkApi.request("/DataBaseService/insert_stock_data", sd)
    print(res.msg)

with open("../config/stock_code.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()
    print(line)
    save_stock_by_code(line, "d")
