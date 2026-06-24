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

YomkApi.init(YomkApi.YomkServer(), ["YomkContext", "YomkFunctionPool", "YomkEventLoop"])
YomkApi.new_service(StockDataService.StockDataService, "/StockDataService")
YomkApi.new_service(DataBaseService.DataBaseService, "/DataBaseService")

def get_stock_by_code(code, frequency):
    name = code.replace(".", "_") + "_" + frequency
    res = YomkApi.request("/DataBaseService/connect_sqlite_db", 
                      {
                        "db_name": "../config/stock.db"
                      })
    print(res.msg)
    
    res = YomkApi.request("/DataBaseService/get_stock_data", 
                      {
                        "name": name,
                        "start": "2015-01-01",
                        "end": "2015-01-31"
                      })
    print(res.msg)
    print(res.data)

get_stock_by_code("sz.002313", "d")
