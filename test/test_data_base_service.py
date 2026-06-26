import YomkApi
import pandas as pd
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
service_dir = current_dir.parent / "src/services"
sys.path.append(str(service_dir))
msgs_dir = current_dir.parent / "src/msgs"
sys.path.append(str(msgs_dir))
import DataBaseService
import StockDataFrame

YomkApi.init(YomkApi.YomkServer(), ["YomkContext", "YomkFunctionPool", "YomkEventLoop"])
YomkApi.new_service(DataBaseService.DataBaseService, "/DataBaseService")

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

sd = StockDataFrame.StockDataFrame()
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

res = YomkApi.request("/DataBaseService/get_stock_data", 
                      {
                        "name": "sz_002313_d",
                        "start": "2023-04-01",
                        "end": "2023-04-02"
                      })
print(res.msg)
print(res.data)
