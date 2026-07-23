import YomkApi
from typing import Any
import baostock as bs
import pandas as pd

class StockDataService(YomkApi.YomkService):
    def __init__(self, server):
        super().__init__(server)
        self.set_name("/StockDataService")

    def init(self):
        self.install_func("/get_stock", self.get_stock)

    def get_stock(self, pkg: Any)->YomkApi.YomkResponse:
        code = pkg.get("code")
        start_date = pkg.get("start_date")
        end_date = pkg.get("end_date")
        query_field = pkg.get("query_field")
        frequency = pkg.get("frequency")
        adjustflag = pkg.get("adjustflag")
        
        bs.login()

        rs = bs.query_history_k_data_plus(
            code,
            ",".join(query_field),
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            adjustflag=adjustflag
        )

        rows = []
        while rs.next():
            rows.append(rs.get_row_data())

        if rows:
            df = pd.DataFrame(rows, columns=rs.fields)
        else:
            df = pd.DataFrame(columns=rs.fields)

        bs.logout()

        return YomkApi.YomkResponse(YomkApi.ResStatus.eOk, self.get_name() + " exec /StockDataService/get_stock success", df)
