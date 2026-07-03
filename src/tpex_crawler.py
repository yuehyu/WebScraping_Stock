import datetime
import sys
import time
import typing
import os


from loguru import logger
import pandas as pd
import requests
from pydantic import BaseModel


class TaiwanStockPrice(BaseModel):
  StockID: str
  TradeVolume: int
  Transaction: int
  TradeValue: int
  Open: float
  Max: float
  Min: float
  Close: float
  Change: float
  date: str

def tpex_header():
  return{
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-encoding": "gzip, deflate",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://www.tpex.org.tw/zh-tw/mainboard/trading/info/mi-pricing.html?type=",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
  }

def set_colname(df: pd.DataFrame, colname: typing.List[str]) -> pd.DataFrame:
  taiwan_stock_price = {
    "代號": "StockID",
    "名稱": "",
    "收盤 ": "Close",
    "漲跌": "Change",
    "開盤 ": "Open",
    "最高 ": "Max",
    "最低": "Min",
    "成交股數  ": "TradeVolume",
    " 成交金額(元)": "TradeValue",
    " 成交筆數 ": "Transaction",
    "最後買價": "",
    "最後買量<br>(張數)": "",
    "最後賣價": "",
    "最後賣量<br>(張數)": "",
    "發行股數 ": "",
    "次日漲停價 ": "",
    "次日跌停價": "",
  }
  df.columns = [ taiwan_stock_price[col] for col in colname ]
  df = df.drop([""], axis=1)
  return df

def clear_data(df: pd.DataFrame) -> pd.DataFrame:
  df = df.fillna("")
  for col in [
    "TradeVolume",
    "Transaction",
    "TradeValue",
    "Open",
    "Max",
    "Min",
    "Close",
    "Change",
  ]:
    df[col] = (df[col].astype(str).str.replace(",", "").str.replace("X", "").str.replace("+", "").str.replace("----", "0").str.replace("---", "0").str.replace("--", "0").str.replace(" ", "").str.replace("除權息", "0").str.replace("除息", "0").str.replace("除權", "0"))
  return df

def convert_date(date: str) -> str:
  year, month, day = date.split("-")
  return f"{year}/{month}/{day}"

def check_schema(df: pd.DataFrame) -> pd.DataFrame:
  df_dict = df.to_dict("records")
  df_schema = [TaiwanStockPrice(**dd).__dict__ for dd in df_dict]
  df = pd.DataFrame(df_schema)
  return df

def gen_data_list(start_date: str, end_date: str) -> typing.List[str]:
  start_date = (datetime.datetime.strptime(start_date, "%Y-%m-%d").date())
  end_date = (datetime.datetime.strptime(end_date, "%Y-%m-%d").date())
  days = (end_date-start_date).days + 1
  date_list = [ str(start_date + datetime.timedelta(days = day)) for day in range(days) ]
  return date_list

def tpex_stock(date: str) -> pd.DataFrame:
  url = ("https://www.tpex.org.tw/www/zh-tw/afterTrading/otc")
  date = convert_date(date)
  payload_data = {
    "date": date,
    "type": "AL",
    "response": "json"
  }
  
  time.sleep(10)
  res = requests.post(url,  params= payload_data)
  if res.status_code == 200:
    data_json = res.json()['tables'][0]
    df = pd.DataFrame(
      data_json["data"]
    )
    colname = data_json["fields"]
  else:
    return pd.DataFrame()
  print(len(df))
  if len(df) == 0:
    return pd.DataFrame()
  df = set_colname(df.copy(), colname)
  df["date"]=date
  return df


def main(start_date: str, end_date: str):
  date_list = gen_data_list(start_date, end_date)
  for date in date_list:
    logger.info(date)
    df = tpex_stock(date)
    if len(df) > 0:
      df = clear_data(df.copy())
      df = check_schema(df.copy())
      use_file = __file__
      filename = os.path.basename(use_file).split("_")[0]
      df.to_csv(f"data/{filename}/Taiwan_Stock_Price_{filename}_{date}.csv", index=False)

if __name__ == "__main__":
  start_date, end_date = sys.argv[1:]
  main(start_date, end_date)