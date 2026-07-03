import datetime
import sys
import time
import typing
import os


import pandas as pd
import requests
from loguru import logger
from pydantic import BaseModel

# Requests Header
def tws_header():
  return {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.twse.com.tw/zh/trading/historical/mi-index.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
  }



# 清洗資料
# ['00400A', '主動國泰動能高息', '69,490,689', '9,673', '1,047,293,219', '15.08', '15.15', '14.91', '15.08', '<p style= color:red>+</p>', '0.28', '15.08', '293', '15.09', '177', '0.00']
def clear_date(df:pd.DataFrame) -> pd.DataFrame:
  df["Dir"] = (df["Dir"].str.split(">").str[1].str.split("<").str[0])
  df["Change"] = (df["Dir"] + df["Change"])
  df["Change"] = (df["Change"].str.replace(" ","").str.replace("X","").astype(float))
  df = df.fillna("")
  df = df.drop(["Dir"], axis=1)
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
    df[col] = (df[col].astype(str).str.replace(",", "").str.replace("X", "").str.replace("+", "").str.replace("----", "0").str.replace("---", "0").str.replace("--", "0"))
  return df


# 資料欄位轉成英文
def colname_zh2en(df: pd.DataFrame, colname: typing.List[str]) -> pd.DataFrame:
  taiwan_stock_price = {
    "證券代號": "StockID",
    "證券名稱": "",
    "成交股數": "TradeVolume",
    "成交筆數": "Transaction",
    "成交金額": "TradeValue",
    "開盤價": "Open",
    "最高價": "Max",
    "最低價": "Min",
    "漲跌(+/-)": "Dir",
    "收盤價": "Close",
    "漲跌價差": "Change",
    "最後揭示買價": "",
    "最後揭示買量": "",
    "最後揭示賣價": "",
    "最後揭示賣量": "",
    "本益比": ""
  }
  df.columns = [ taiwan_stock_price[col] for col in colname]
  df = df.drop([""], axis=1)
  return df 

def twse_stock(data: str) -> pd.DataFrame:
  url = ("https://www.twse.com.tw/zh/exchangeReport/MI_INDEX?date={data}&type=ALL&response=json")
  url = url.format(data=data.replace("-",""))
  time.sleep(10)
  res = requests.get(url, headers= tws_header())
  data_json = res.json()["tables"]
  # print(data_json)
  if (res.json()["stat"]=="很抱歉，沒有符合條件的資料!"):
    return pd.DataFrame()
  try:
    if data_json[9]:
      df = pd.DataFrame(
        data_json[9]["data"]
      )
      colname = data_json[9]["fields"]
    elif data_json[8]:
      # ['00400A', '主動國泰動能高息', '69,490,689', '9,673', '1,047,293,219', '15.08', '15.15', '14.91', '15.08', '<p style= color:red>+</p>', '0.28', '15.08', '293', '15.09', '177', '0.00']
      df = pd.DataFrame(
        data_json[8]["data"]
      )
      colname = data_json[8]["fields"]
    elif res.json()["stat"] in [
      "查詢日期小於 93/2/11 請重新查詢",
      "很抱歉，沒有符合條件的資料"
    ]:
      return pd.DataFrame()
  except BaseException:
    return pd.DataFrame()
  print(len(df))
  if len(df) == 0:
    return pd.DataFrame()
  df = colname_zh2en(df.copy(), colname)
  df["data"]=data
  return df

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
  data: str

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

def main(start_date: str, end_date: str):
  date_list = gen_data_list(start_date, end_date)
  for data in date_list:
    logger.info(data)
    df = twse_stock(data)
    # ['00400A', '主動國泰動能高息', '69,490,689', '9,673', '1,047,293,219', '15.08', '15.15', '14.91', '15.08', '<p style= color:red>+</p>', '0.28', '15.08', '293', '15.09', '177', '0.00']
    if len(df) > 0:
      df = clear_date(df.copy())
      df = check_schema(df.copy())
      use_file = __file__
      filename = os.path.basename(use_file).split("_")[0]
      print(filename)
      df.to_csv(f"data/{filename}/Taiwan_Stock_Price_{filename}_{data}.csv", index=False)



if __name__ == "__main__":
  start_date, end_date =sys.argv[1:]
  main(start_date, end_date)