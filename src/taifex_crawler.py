"""爬蟲
抓取股票資料
"""
import os
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
  if res.status_code == 200 :
    data_json = res.json()
    print(data_json)


