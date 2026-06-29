import YomkApi
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent / "src"
sys.path.append(str(src_dir))

from services.data.StockDataService import StockDataService
from services.data.DataBaseService import DataBaseService
from msgs.StockDataFrame import StockDataFrame

YomkApi.init(YomkApi.YomkServer(), ["YomkContext", "YomkFunctionPool", "YomkEventLoop"])
YomkApi.new_service(StockDataService, "/StockDataService")
YomkApi.new_service(DataBaseService, "/DataBaseService")

def save_stock_by_code(code, frequency):
    res = YomkApi.request("/StockDataService/get_stock", 
                          {"code": code, 
                           "start_date": "1990-01-01", 
                           "end_date": "2026-12-31",
                           "query_field": ["date","open","high","low","close","volume","turn"],
                           "frequency": frequency,
                           "adjustflag": "2"
                          })
    df = res.data
    
    res = YomkApi.request("/DataBaseService/connect_sqlite_db", 
                      {
                        "db_name": "../config/stock.db"
                      })
    print(res.msg)
    name = code.replace(".", "_") + "_" + frequency

    res = YomkApi.request("/DataBaseService/create_table", 
                        {
                            "name": name
                        })
    print(res.msg)

    sd = StockDataFrame()
    sd.table_name = name
    sd.df = df
    res = YomkApi.request("/DataBaseService/insert_stock_data", sd)
    print(res.msg)

save_stock_by_code("sz.002313", "d")