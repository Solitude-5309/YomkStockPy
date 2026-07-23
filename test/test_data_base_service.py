import YomkApi
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msgs.YomkMsgs import StockDataFrame
from boot.Boot import Boot

YomkApi.boot(Boot(["/DataBaseService"]))

res = YomkApi.request("/DataBaseService/connect_sqlite_db", 
                      {
                        "db_name": "../config/test_stock.db"
                      })
print(res.msg)

res = YomkApi.request("/DataBaseService/create_table", 
                      {
                        "name": "sz_002313_d"
                      })
print(res.msg)

sd = StockDataFrame()
sd.table_name = "sz_002313_d"
sd.df = pd.DataFrame({
    "date": ["2023-04-01", "2023-04-02"],
    "open": [10.0, 10.1],
    "high": [10.5, 10.6],
    "low": [9.5, 9.6],
    "close": [10.0, 10.1],
    "volume": [1000, 2000],
    "turn": [100000, 200000]
})
res = YomkApi.request("/DataBaseService/insert_stock_data", sd)
print(res.msg)

res = YomkApi.request("/DataBaseService/get_stock_list", "")
print(res.msg)
print(res.data)

res = YomkApi.request("/DataBaseService/get_stock_last_date", 
                      {
                        "name": "sz_002313_d"
                      })
print(res.msg)
print(res.data)

res = YomkApi.request("/DataBaseService/table_is_exists", 
                      {
                        "name": "sz_002313_d"
                      })
print(res.msg)
print(res.data)

res = YomkApi.request("/DataBaseService/get_stock_data", 
                      {
                        "name": "sz_002313_d",
                        "start": "2023-04-01",
                        "end": "2023-04-02"
                      })
print(res.msg)
print(res.data)
