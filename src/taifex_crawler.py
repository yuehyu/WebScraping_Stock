"""爬蟲
抓取股票資料
"""
import datetime
import sys
import time
import typing
import os
import io


from loguru import logger
from pydantic import BaseModel
import requests
import pandas as pd

def taifex_header():
  return{
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Content-Length": "135",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.taifex.com.tw",
    "Referer": "https://www.taifex.com.tw/cht/3/futDailyMarketView",
    "Sec-fetch-dest": "document",
    "Sec-fetch-mode": "navigate",
    "Sec-fetch-site": "same-origin",
    "Sec-fetch-user": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
  }

class TaiwanFuturesDaily(BaseModel):
  date: str
  FuturesID: str
  ContractDate: str
  Open : float
  Max: float
  Min: float
  Close: float
  Change: float
  ChangePer: float
  Volume: float
  SettlementPrice: float
  OpenInterest: int
  TradingSession: str

def gen_date(start_date: str, end_date: str) -> typing.List[str]:
  start_date = (datetime.datetime.strptime(start_date, "%Y-%m-%d").date())
  end_date = (datetime.datetime.strptime(end_date, "%Y-%m-%d").date())
  days = (end_date-start_date).days + 1
  date_list = [ str(start_date + datetime.timedelta(days = day)) for day in range(days) ]
  return date_list

def colname_zh2en(df: pd.DataFrame) -> pd.DataFrame:
  """
  利用字典（Dictionary）將 DataFrame 的所有欄位名稱（Columns）批次進行更名或轉換。
  """
  colname_dict = {
    "交易日期": "date",
    "契約": "FuturesID",
    "到期月份(週別)": "ContractDate",
    "開盤價": "Open",
    "最高價": "Max",
    "最低價": "Min",
    "收盤價": "Close",
    "漲跌價": "Change",
    "漲跌%": "ChangePer",
    "成交量": "Volume",
    "結算價": "SettlementPrice",
    "未沖銷契約數": "OpenInterest",
    "交易時段":"TradingSession"
  }
  df = df.drop(
    [
      "最後最佳買價",
      "最後最佳賣價",
      "歷史最高價",
      "歷史最低價",
      "是否因訊息面暫停交易",
      "價差對單式委託成交量"
    ],
    axis=1
  )
  df.columns = [
    colname_dict[col] for col in df.columns
  ]
  return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
  df["date"] = df["date"].str.replace("/", "-")
  df["ChangePer"] = df["ChangePer"].str.replace("%", "")
  df["ContractDate"] = df["ContractDate"].astype(str).str.replace(" ", "")
  if "TradingSession" in df.columns:
    df["TradingSession"] = df["TradingSession"].map(
      {
        "一般": "Position",
        "盤後": "AfterMarket"
      }
    )
  else:
    df["TradingSession"] ="Position"
  for col in [
    "Open",
    "Max",
    "Min",
    "Close",
    "Change",
    "ChangePer",
    "Volume",
    "SettlementPrice",
    "OpenInterest",
  ]:
    df[col] = (df[col].replace("-", "0").astype(float))
  df = df.fillna(0)
  return df

def check_schema(df: pd.DataFrame) -> pd.DataFrame:
  df_dict = df.to_dict("records")
  df_schema = [TaiwanFuturesDaily(**dd).__dict__ for dd in df_dict]
  df = pd.DataFrame(df_schema)
  return df


def taifex_stock(date: str) -> pd.DataFrame:
  url = "https://www.taifex.com.tw/cht/3/futDataDown"
  payload_data = {
    "down_type": "1",
    "commodity_id": "all",
    "queryStartDate": date.replace("-", "/"),
    "queryEndDate": date.replace("-", "/"),
  }
  time.sleep(10)
  resp = requests.post(
    url,
    headers = taifex_header(),
    data = payload_data
  )
  if resp.ok:
    if resp.content:
      df = pd.read_csv(
        io.StringIO(
          resp.content.decode(
            "big5"
          )
        ),
        index_col= False
      )
  else:
    return pd.DataFrame
  return df

def main(start_date: str, end_date: str) -> pd.DataFrame:
  date_list= gen_date(start_date, end_date)
  for date in date_list:
    logger.info(date)
    df = taifex_stock(date)
    if len(df) > 0:
      df = colname_zh2en(df.copy())
      df = clean_data(df.copy())
      df = check_schema(df.copy())
      use_file = __file__
      filename = os.path.basename(use_file).split("_")[0]
      df.to_csv(
        f"data/{filename}/Taiwan_Stock_Price_{filename}_{date}.csv", index=False
      )

if __name__ == "__main__":
  start_date, end_date = sys.argv[1:]
  main(start_date, end_date)