"""爬蟲
抓取股票資料
"""
import datetime
import sys
import time
import typing
import os

from loguru import logger
from pydantic import BaseModel
import requests
import pandas as pd

def taifex_header():
  return{
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "content-length": "135",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.taifex.com.tw",
    "referer": "https://www.taifex.com.tw/cht/3/futDailyMarketView",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
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
  TradingSession: int

def gen_date(start_date: str, end_date: str) -> typing.List[str]:
  start_date = (datetime.datetime.strptime(start_date, "%Y-%m-%d").date())
  end_date = (datetime.datetime.strptime(end_date, "%Y-%m-%d").date())
  days = (end_date-start_date).days + 1
  date_list = [ str(start_date + datetime.timedelta(days = day)) for day in range(days) ]
  return date_list

def column_zh2en(df: pd.DataFrame) -> pd.DataFrame:
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




def taifex_stock(date: str) -> pd.DataFrame:
  url = "https://www.taifex.com.tw/cht/3/futDataDown"
  payload_data = {
    "down_type": "1",
    "commodity_id": "all",
    "queryStartDate": date.replace("/", "-"),
    "queryEndDate": date.replace("/", "-"),
    "commodity_idt": "all",
  }
  
  res = requests.post(
    url,
    header = taifex_header(),
    date = payload_data
  )





def main(start_date: str, end_date: str) -> pd.DataFrame:
  date = gen_date(start_date, end_date)
