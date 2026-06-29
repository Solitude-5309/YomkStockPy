import YomkApi
from typing import Any
import sqlite3, pandas as pd

class DataBaseService(YomkApi.YomkService):
    def __init__(self, server):
        super().__init__(server)
        self.set_name("/DataBaseService")
        self.sqlite_db_name = ""
        self.sqlite_conn = None
        self.sqlite_cursor = None

    def init(self):
        self.install_func("/create_table", self.create_table)
        self.install_func("/connect_sqlite_db", self.connect_sqlite_db)
        self.install_func("/get_stock_list", self.get_stock_list)
        self.install_func("/insert_stock_data", self.insert_stock_data)
        self.install_func("/get_stock_data", self.get_stock_data)
        self.install_func("/get_stock_last_date", self.get_stock_last_date)
        
    def get_stock_last_date(self, pkg: Any)->YomkApi.YomkResponse:
        name = pkg.get("name")
        query = f"""
            SELECT date FROM {name}
            ORDER BY date DESC
            LIMIT 1
        """
        df = pd.read_sql_query(query, self.sqlite_conn)
        return YomkApi.YomkResponse(YomkApi.ResStatus.eOk, self.get_name() + " exec /DataBaseService/get_stock_last_date success", df)
        
    def get_stock_data(self, pkg: Any)->YomkApi.YomkResponse:
        name = pkg.get("name")
        start = pkg.get("start")
        end = pkg.get("end")
        query = f"""
            SELECT * FROM {name}
            WHERE date >= ? AND date <= ?
            ORDER BY date ASC
        """
        df = pd.read_sql_query(query, self.sqlite_conn, params=(start, end))
        return YomkApi.YomkResponse(YomkApi.ResStatus.eOk, self.get_name() + " exec /DataBaseService/get_stock_data success", df)
        
    def insert_stock_data(self, pkg: Any)->YomkApi.YomkResponse:
        try:
            table_name = pkg.table_name
            df = pkg.df
            
            # 获取列名和占位符
            cols = list(df.columns)
            placeholders = ', '.join(['?' for _ in cols])
            col_names = ', '.join(cols)

            # 转换为 list of tuples
            data = [tuple(row) for row in df.to_numpy()]

            sql = f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"
            self.sqlite_cursor.executemany(sql, data)
            self.sqlite_conn.commit()
            
            return YomkApi.YomkResponse(YomkApi.ResStatus.eOk, self.get_name() + " exec /DataBaseService/insert_stock_data success")
        except sqlite3.Error as e:
            print(f"insert_stock_data failed: {e}")
            return YomkApi.YomkResponse(YomkApi.ResStatus.eErr, self.get_name() + f" exec /DataBaseService/insert_stock_data failed: {e}")
        
    def get_stock_list(self, pkg: Any)->YomkApi.YomkResponse:
        try:
            stock_list = pd.read_sql("SELECT * FROM stock_list", self.sqlite_conn)
            return YomkApi.YomkResponse(YomkApi.ResStatus.eOk, self.get_name() + " exec /DataBaseService/get_stock_list success", stock_list)
        except sqlite3.Error as e:
            print(f"get_stock_list failed: {e}")
            return YomkApi.YomkResponse(YomkApi.ResStatus.eErr, self.get_name() + f" exec /DataBaseService/get_stock_list failed: {e}")
        
    def connect_sqlite_db(self, pkg: Any)->YomkApi.YomkResponse:
        db_name = pkg.get("db_name")
        self.sqlite_db_name = db_name
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL
                )
            """)
            self.sqlite_conn = conn
            self.sqlite_cursor = cursor
        except sqlite3.Error as e:
            print(f"connect_sqlite_db {db_name} failed: {e}")
            return YomkApi.YomkResponse(YomkApi.ResStatus.eErr, self.get_name() + f" exec /DataBaseService/connect_sqlite_db failed: {e}")
        return YomkApi.YomkResponse(YomkApi.ResStatus.eOk, self.get_name() + " exec /DataBaseService/connect_sqlite_db success")

    def create_table(self, pkg: Any)->YomkApi.YomkResponse:
        table_name = pkg.get("name")
        type = table_name.split("_")[-1]
        try:
            if type == "d":
                create_table_sql = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        date    TEXT NOT NULL PRIMARY KEY,
                        open    REAL NOT NULL,
                        high    REAL NOT NULL,
                        low     REAL NOT NULL,
                        close   REAL NOT NULL,
                        volume  INTEGER NOT NULL,
                        turn    INTEGER NOT NULL
                    )
                    """
                self.sqlite_cursor.execute(create_table_sql)
            self.sqlite_cursor.execute("INSERT OR IGNORE INTO stock_list (code) VALUES (?)", (table_name,))
        except sqlite3.Error as e:
            print(f"create_table {table_name} failed: {e}")
            return YomkApi.YomkResponse(YomkApi.ResStatus.eErr, self.get_name() + f" exec /DataBaseService/create_table failed: {e}")
        
        return YomkApi.YomkResponse(YomkApi.ResStatus.eOk, self.get_name() + " exec /DataBaseService/create_table success")
