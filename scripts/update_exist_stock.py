import YomkApi
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msgs.YomkMsgs import StockDataFrame
from boot.Boot import Boot
YomkApi.boot(Boot(["/StockDataService", "/DataBaseService"]))

def update_exist_stock():
    res = YomkApi.request("/DataBaseService/connect_sqlite_db", 
                      {
                        "db_name": "../config/stock.db"
                      })
    
    res = YomkApi.request("/DataBaseService/get_stock_list", "")
    
    for index, row in res.data.iterrows():
        code = row['code']
        res = YomkApi.request("/DataBaseService/get_stock_last_date", 
                          {
                            "name": code
                          })
        first_row = res.data.head(1).iloc[0]
        last_date = first_row['date']
        
        stock_code = code.split("_")[0] + "." + code.split("_")[1]
        frequency = code.split("_")[2]
        today = datetime.now().strftime("%Y-%m-%d")
        
        if last_date == today:
            print(f"{code} already up to date")
            continue
        
        res = YomkApi.request("/StockDataService/get_stock", 
                          {"code": stock_code, 
                           "start_date": last_date, 
                           "end_date": today,
                           "query_field": ["date","open","high","low","close","volume","turn"],
                           "frequency": frequency,
                           "adjustflag": "2"
                          })
        df = res.data
        name = code
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

update_exist_stock()
