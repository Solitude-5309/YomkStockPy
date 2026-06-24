import YomkApi
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
service_dir = current_dir.parent / "src/services"
sys.path.append(str(service_dir))
import StockDataService
YomkApi.init(YomkApi.YomkServer(), ["YomkContext", "YomkFunctionPool", "YomkEventLoop"])
YomkApi.new_service(StockDataService.StockDataService, "/StockDataService")
res = YomkApi.request("/StockDataService/get_stock", 
                      {"code": "sz.002313", 
                       "start_date": "2020-01-01", 
                       "end_date": "2020-12-31",
                       "query_field": ["date","open","high","low","close","volume","turn"],
                       "frequency": "d",
                       "adjustflag": "2"
                      })
df = res.data
print(df[["date","open","high","low","close","volume","turn"]].head())