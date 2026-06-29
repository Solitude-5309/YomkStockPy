import YomkApi
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent / "src"
sys.path.append(str(src_dir))
from services.data.StockDataService import StockDataService
YomkApi.init(YomkApi.YomkServer(), ["YomkContext", "YomkFunctionPool", "YomkEventLoop"])
YomkApi.new_service(StockDataService, "/StockDataService")

# frequency:
# "d" 日K
# "w" 周K
# "m" 月K  
# "5" 5分钟K
# "15" 15分钟K
# "30" 30分钟K
# "60" 60分钟K

# adjustflag:
# "1" 后复权
# "2" 前复权
# "3" 不复权

res = YomkApi.request("/StockDataService/get_stock", {
                        "code": "sz.002313", 
                        "start_date": "2020-01-01", 
                        "end_date": "2020-12-31",
                        "query_field": ["date","open","high","low","close","volume","turn"],
                        "frequency": "d",
                        "adjustflag": "2"})
df = res.data
print(df[["date","open","high","low","close","volume","turn"]].head())