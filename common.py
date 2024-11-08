import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import streamlit as st
import io
import sys
import requests
import time
import glob
import os
import os.path
import pandas as pd
import json
import copy
import re
import math
import decimal
import yfinance as yf
import psycopg2, psycopg2.extras
import config
import logging
import matplotlib.ticker as mtick
import numpy as np
import metpy.calc as mpcalc
from copy import deepcopy
from matplotlib import pyplot as plt
from selenium.common.exceptions import TimeoutException as ste
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from chromedriver_py import binary_path
#from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import date, timedelta
from datetime import datetime as dt
#from yahoo_earnings_calendar import YahooEarningsCalendar
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from dateutil import rrule
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import xml.etree.ElementTree as ET
#from zipfile import ZipFile

import pandas_ta as ta
from tqdm import tqdm
import plotly.graph_objects as go
from plotly.subplots import make_subplots

isWindows = False

if(sys.platform == 'win32'):
  isWindows = True

############################
# Data Retrieval Functions #
############################

def get_page(url):
  # When website blocks your request, simulate browser request: https://stackoverflow.com/questions/56506210/web-scraping-with-python-problem-with-beautifulsoup
  header={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36'}
  #header = { 
  #  'User-Agent'      : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36', 
  #  'Accept'          : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
  #  'Accept-Language' : 'en-US,en;q=0.5',
  #  'DNT'             : '1', # Do Not Track Request Header 
  #  'Connection'      : 'close'
  #}
  page = requests.get(url=url,headers=header)

  #import pdb; pdb.set_trace()
  try:
      page.raise_for_status()
  except requests.exceptions.HTTPError as e:
      # Whoops it wasn't a 200
      raise Exception("Http Response (%s) Is Not 200: %s" % (url, str(page.status_code)))

  return page

def get_page_selenium(url,wait_until_element_id=None, no_sandbox=False):

  #Selenium Browser Emulation Tool
  chrome_options = Options()
  chrome_options.add_argument("--headless") 

  if(no_sandbox):
    chrome_options.add_argument('--no-sandbox')  

  chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; Microsoft; Lumia 640 XL LTE) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Mobile Safari/537.36 Edge/12.10166")
  #try:

# 1. pip install chromedriver_py --upgrade
  svc = webdriver.ChromeService(executable_path=binary_path)
  driver = webdriver.Chrome(service=svc, options=chrome_options)
  #driver = webdriver.Chrome(ChromeDriverManager().install())
  html = ''
  #TODO: https://stackoverflow.com/questions/22130109/cant-use-chrome-driver-for-selenium
  #driver = webdriver.Chrome(executable_path=CHROME_EXECUTABLE_PATH,options=chrome_options)
  #driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)
  #driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=chrome_options)
  #except ZipFile.BadZipFile as e:
  #TODO: Follow Instructions to Use manually installed driver
  #TODO: Have a look at chromedrivermanager: https://pypi.org/project/webdriver-manager/
  try:
    driver.get(url)
    driver.implicitly_wait(10)  

    if(wait_until_element_id):
      elem = WebDriverWait(driver, 30).until(
      EC.presence_of_element_located((By.ID, wait_until_element_id)))  

    time.sleep(15)
    html = driver.page_source
    driver.close()
  except ste as e:    
    print(f'Selenium Timed Out for {url}')
    #TODO: ADD LOGGER
    #logger.exception(f'Selenium Timed Out for {url}')

  return html


def get_yf_historical_stock_data(ticker, interval, start, end):
  data = yf.download(  # or pdr.get_data_yahoo(...
    # tickers list or string as well
    tickers = ticker,

    start=start, 
    end=end, 

    # use "period" instead of start/end
    # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    # (optional, default is '1mo')
    period = "ytd",

    # fetch data by interval (including intraday if period < 60 days)
    # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
    # (optional, default is '1d')
    interval = interval,

    # group by ticker (to access via data['SPY'])
    # (optional, default is 'column')
    group_by = 'ticker',

    # adjust all OHLC automatically
    # (optional, default is False)
    auto_adjust = True,

    # download pre/post regular market hours data
    # (optional, default is False)
    prepost = True,

    # use threads for mass downloading? (True/False/Integer)
    # (optional, default is True)
    threads = True,

    # proxy URL scheme use use when downloading?
    # (optional, default is None)
    proxy = None
  )

  df_yf = data.reset_index()
  df_yf = df_yf.rename(columns={"Date": "DATE"})

  return df_yf

def get_yf_analysis(ticker):
  company = yf.Ticker(ticker)
  #import pdb; pdb.set_trace()
  # get stock info
  company.info

  # get historical market data
  hist = company.history(period="max")

  # show actions (dividends, splits)
  company.actions

  # show dividends
  company.dividends

  # show splits
  company.splits

  # show financials
  company.financials
  company.quarterly_financials

  # show major holders
  company.major_holders

  # show institutional holders
  company.institutional_holders

  # show balance sheet
  company.balance_sheet
  company.quarterly_balance_sheet

  # show cashflow
  company.cashflow
  company.quarterly_cashflow

  # show earnings
  company.earnings
  company.quarterly_earnings

  # show sustainability
  company.sustainability

  # show analysts recommendations
  company.recommendations

  # show next event (earnings, etc)
  company.calendar

  # show all earnings dates
  company.earnings_dates

  # show ISIN code - *experimental*
  # ISIN = International Securities Identification Number
  company.isin

  # show options expirations
  company.options

  # show news
  company.news

  # get option chain for specific expiration
  opt = company.option_chain('YYYY-MM-DD')
  # data available via: opt.calls, opt.puts

def set_yf_key_stats(df_tickers, logger):
  success = False
  for index, row in df_tickers.iterrows():
    ticker = row['Ticker']  

    logger.info(f'Getting YF Key Stats for {ticker}')
    statsDict = {}

    df_company_data = pd.DataFrame()
    url = "https://finance.yahoo.com/quote/%s/key-statistics?p=%s" % (ticker, ticker)
    try:
      page = get_page(url)
      
      soup = BeautifulSoup(page.content, 'html.parser')

      tables = soup.find_all('table')
      #try:
      for table in tables:
        table_rows = table.find_all('tr', recursive=True)
        emptyDict = {}

        #Get rows of data.
        for tr in table_rows:
          tds = tr.find_all('td')
          boolKey = True
          keyValueSet = False

          for td in tds:
              if boolKey:
                  key = td.text.strip()
                  boolKey = False                
              else:
                  value = td.text.strip()
                  boolKey = True
                  keyValueSet = True                

              if keyValueSet:
                  emptyDict[key] = value
                  keyValueSet = False
        statsDict.update(emptyDict)
    except Exception as e:
      #For some reason YF page did not load. Continue on and handle the exception below
      pass
    #import pdb; pdb.set_trace()
    try:
      df_company_data.loc[ticker, 'MARKET_CAP'] = statsDict['Market Cap (intraday)']
      df_company_data.loc[ticker, 'EV'] = statsDict['Enterprise Value']
      df_company_data.loc[ticker, 'AVG_VOL_3M'] = statsDict['Avg Vol (3 month) 3']
      df_company_data.loc[ticker, 'AVG_VOL_10D'] = statsDict['Avg Vol (10 day) 3']
      df_company_data.loc[ticker, '50_DAY_MOVING_AVG'] = statsDict['50-Day Moving Average 3']
      df_company_data.loc[ticker, '200_DAY_MOVING_AVG'] = statsDict['200-Day Moving Average 3']
      df_company_data.loc[ticker, 'EV_REVENUE'] = statsDict['Enterprise Value/Revenue']
      df_company_data.loc[ticker, 'EV_EBITDA'] = statsDict['Enterprise Value/EBITDA']
      df_company_data.loc[ticker, 'PRICE_BOOK'] = statsDict['Price/Book (mrq)']

      df_company_data = dataframe_convert_to_numeric(df_company_data, '50_DAY_MOVING_AVG', logger)
      df_company_data = dataframe_convert_to_numeric(df_company_data, '200_DAY_MOVING_AVG', logger)

      logger.info(f'Successfully Retrieved YF Key Stats for {ticker}')
    except KeyError as e:
      logger.info(f'Did not return YF stock data for {ticker}')      

    # get ticker cid
    cid = sql_get_cid(ticker)
    if(cid):
      # write records to database
      rename_cols = {"50_DAY_MOVING_AVG": "MOVING_AVG_50D", "200_DAY_MOVING_AVG": "MOVING_AVG_200D"}
      add_col_values = {"cid": cid}
      conflict_cols = "cid"

      success = sql_write_df_to_db(df_company_data, "CompanyMovingAverage", rename_cols, add_col_values, conflict_cols)
      logger.info(f'Successfully Saved YF Key Stats for {ticker}')     

  return success


def set_yf_historical_data(etfs, logger):
  data = {'DATE': []}

  # Convert the dictionary into DataFrame
  df_etf_data = pd.DataFrame(data)

  #get date range
  todays_date = date.today()
  date_str = "%s-%s-%s" % (todays_date.year, todays_date.month, todays_date.day)

  for etf in etfs:
    logger.info(f'Getting YF Historical Data for {etf}')
    #if(etf == 'SPSM'):
    #  import pdb; pdb.set_trace()

    df_etf = get_yf_historical_stock_data(etf, "1d", "2007-01-01", date_str)

    #Remove unnecessary columns and rename columns
    df_etf = df_etf.drop(['Open', 'High', 'Low', 'Volume'], axis=1)
    df_etf = df_etf.rename(columns={"Close": etf})

    df_etf_data = combine_df_on_index(df_etf_data, df_etf, 'DATE')

  # Fill NA values by propegating values before
  df_etf_data = df_etf_data.fillna(method='ffill')

  #df_original = convert_excelsheet_to_dataframe(excel_file_path, sheet_name, True)
  #TODO: Write to database
  #TODO: Will need to rename some of the columns before writing to database (ie. Prefix with YF_)
  #import pdb; pdb.set_trace()
  # write records to database
  #rename_cols = {"50_DAY_MOVING_AVG": "MOVING_AVG_50D", "200_DAY_MOVING_AVG": "MOVING_AVG_200D"}

  rename_cols = {
    "DATE":"series_date",    
    "DX-Y.NYB":"DX_Y_NYB",
    "GC=F":"GC_F",
    "EXH1.DE":"EXH1_DE",
    "EXH2.DE":"EXH2_DE",
    "EXH3.DE":"EXH3_DE",
    "EXH4.DE":"EXH4_DE",
    "EXH5.DE":"EXH5_DE",
    "EXH6.DE":"EXH6_DE",
    "EXH7.DE":"EXH7_DE",
    "EXH8.DE":"EXH8_DE",
    "EXH9.DE":"EXH9_DE",
    "EXI5.DE":"EXI5_DE",
    "EXSA.DE":"EXSA_DE",
    "EXV1.DE":"EXV1_DE",
    "EXV2.DE":"EXV2_DE",
    "EXV3.DE":"EXV3_DE",
    "EXV4.DE":"EXV4_DE",
    "EXV5.DE":"EXV5_DE",
    "EXV6.DE":"EXV6_DE",
    "EXV7.DE":"EXV7_DE",
    "EXV8.DE":"EXV8_DE",
    "EXV9.DE":"EXV9_DE",
    "000300.SS":"YF_000300_SS",
    "0P0001GY56.F":"YF_0P0001GY56_F",
    "^AXJO":"_AXJO",
    "^BSESN":"_BSESN",
    "^DJI":"_DJI",
    "^FCHI":"_FCHI",
    "^FTSE":"_FTSE",
    "^GDAXI":"_GDAXI",
    "^GSPC":"_GSPC",
    "^GSPTSE":"_GSPTSE",
    "^HSI":"_HSI",
    "^IBEX":"_IBEX",
    "^IXIC":"_IXIC",
    "^MXX":"_MXX",
    "^N225":"_N225",
    "^NSEI":"_NSEI",
    "^NYA":"_NYA",
    "^STOXX50E":"_STOXX50E"
  }

  #add_col_values = {}
  conflict_cols = "series_date"

  success = sql_write_df_to_db(df_etf_data, "Macro_YFHistoricalETFData", rename_cols=rename_cols, conflict_cols=conflict_cols)
  logger.info(f'Successfully Saved YF Historical Data')     

  return success

def calculate_annual_etf_performance(df_etf_data,logger):

  df_etf_data = df_etf_data.rename(columns={'series_date': 'DATE'})

  data = {'DATE': []}
  etfs = [ 'RXI','XLP','XLY','XLE','XLF','XLV','XLI','XLK','XLB','XLRE','XLC','XLU','SPY','USO','QQQ','IWM','IBB','EEM','HYG','VNQ','MDY','SPSM','EFA','TIP','AGG','DJP','BIL','GC_F','DX_Y_NYB']

  # Convert the dictionary into DataFrame
  df_percentage_change = pd.DataFrame(data)

  for etf in etfs:
    logger.info(f'Calculating Yearly Performance for {etf}')

    #groupby year and determine the daily percent change by year, and add it as a column to df
    df_etf_data['%s_pct_ch' % (etf.lower(),)] = df_etf_data.groupby(df_etf_data.DATE.dt.year, group_keys=False)[etf.lower()].apply(pd.Series.pct_change)

    #Drop unnecessary columns
    df_etf_data = df_etf_data.drop(columns=etf.lower(), axis=1)

    # groupby year and aggregate sum of pct_ch to get the yearly return
    #df_yearly_pct_ch = df_etf_data.groupby(df_etf_data.DATE.dt.year)['%s_pct_ch' % (etf,)].sum().mul(100).reset_index().rename(columns={'%s_pct_ch' % (etf,): etf})
    df_yearly_pct_ch = df_etf_data.groupby(df_etf_data.DATE.dt.year, group_keys=False)['%s_pct_ch' % (etf.lower(),)].sum().reset_index().rename(columns={'%s_pct_ch' % (etf.lower(),): etf.lower()})

    df_percentage_change = combine_df_on_index(df_percentage_change, df_yearly_pct_ch, 'DATE')

  #import pdb; pdb.set_trace()

  # Write to database
  rename_cols = {
    "DATE":"series_date",    
  }

  #Clear out old data
  sql_delete_all_rows('Macro_ETFAnnualData')

  success = sql_write_df_to_db(df_percentage_change, "Macro_ETFAnnualData",rename_cols=rename_cols)
  logger.info(f'Successfully Calculated Annual Asset Class Performance Data')     

  return success

def calculate_etf_performance(df_etf_data, logger):

  selected_etfs = [
      'rxi',
      'xlp',
      'xly',
      'xle',
      'xlf',
      'xlv',
      'xli',
      'xlk',
      'xlb',
      'xlre',
      'xlc',
      'xlu',
      'spy',
      'uso',
      'qqq',
      'iwm',
      'ibb',
      'eem',
      'hyg',
      'vnq',
      'mdy',
      'spsm',
      'efa',
      'tip',
      'agg',
      'djp',
      'bil',
      'gc_f',
      'dx_y_nyb',
      '_dji',
      '_gspc',
      '_ixic',
      '_nya',
      '_gsptse',
      '_mxx',		
      '_stoxx50e',
      '_ftse',
      '_gdaxi',
      '_fchi',
      '_ibex',
      '_n225',
      '_hsi',
      'yf_000300_ss',
      '_axjo',
      'yf_0p0001gy56_f',
      '_bsesn',
      '_nsei',      
  ]

  all_columns = selected_etfs.copy()
  all_columns.insert(0,'series_date')

  df_historical_data_subset = df_etf_data[all_columns].copy()

  data = {'asset': [], 'last_date': [],'last_value': [],'ytd_value': [], 'ytd_pct': [], 'last_5_days_value': [], 'last_5_days_pct': [], 'last_month_value': [], 'last_month_pct': [], 'last_3_months_value': [], 'last_3_months_pct': [], 'last_5_years_value': [], 'last_5_years_pct': []}
  
  # Convert the dictionary into DataFrame
  df_percentage_change = pd.DataFrame(data)

  for etf in selected_etfs:
    df_series = df_historical_data_subset.loc[0:len(df_historical_data_subset),['series_date',etf]]    

    asset, last_date, last_value, ytd_value, ytd_pct, last_5_days_value, last_5_days_pct, last_month_value, last_month_pct, last_3_months_value, last_3_months_pct, last_5_years_value, last_5_years_pct = calculate_asset_percentage_changes(df_series) 

    df_temp = pd.DataFrame([[asset,last_date,last_value,ytd_value,ytd_pct,last_5_days_value,last_5_days_pct,last_month_value,last_month_pct,last_3_months_value,last_3_months_pct,last_5_years_value,last_5_years_pct]], columns=['asset', 'last_date','last_value', 'ytd_value', 'ytd_pct', 'last_5_days_value', 'last_5_days_pct', 'last_month_value', 'last_month_pct', 'last_3_months_value', 'last_3_months_pct', 'last_5_years_value', 'last_5_years_pct'])

    df_percentage_change = pd.concat([df_percentage_change, df_temp], axis=0)

  df_percentage_change['last_date'] = pd.to_datetime(df_percentage_change['last_date'],format='%Y-%m-%d')

  #Clear out old data
  sql_delete_all_rows('Macro_ETFPerformance')

  success = sql_write_df_to_db(df_percentage_change, "Macro_ETFPerformance")
  logger.info(f'Successfully Calculated ETF Performance Data')     

  return success

def calculate_asset_percentage_changes(df_series):
  asset = df_series.columns.values.tolist()[1]
  last_date = df_series.iloc[:, 0][len(df_series)-1].date()
  last_value = df_series.iloc[:, 1][len(df_series)-1]

  # Calculate % changes for 
  # YTD Date
  rd = relativedelta(years=+1)
  ytd_date = last_date - rd
  df_ytd = util_return_date_values(df_series,ytd_date)
  # Calculate % change from last value
  ytd_value = df_ytd[asset].values[0]
  ytd_pct = (last_value - df_ytd[asset].values[0]) / df_ytd[asset].values[0]
  
  # Last 5 days		
  td = timedelta(days=5)
  last_5_days_date = last_date - td
  df_last_5_days = util_return_date_values(df_series,last_5_days_date)
  last_5_days_value = df_last_5_days[asset].values[0]
  last_5_days_pct = (last_value - df_last_5_days[asset].values[0]) / df_last_5_days[asset].values[0]

  # Last Month		
  rd = relativedelta(months=+1)
  last_month_date = last_date - rd
  df_last_month = util_return_date_values(df_series,last_month_date)
  last_month_value = df_last_month[asset].values[0]
  last_month_pct = (last_value - df_last_month[asset].values[0]) / df_last_month[asset].values[0]

  # Last 3 months		
  rd = relativedelta(months=+3)
  last_3_months_date = last_date - rd
  df_last_3_months = util_return_date_values(df_series,last_3_months_date)
  last_3_months_value = df_last_3_months[asset].values[0]
  last_3_months_pct = (last_value - df_last_3_months[asset].values[0]) / df_last_3_months[asset].values[0]

  # Last 5 years	
  rd = relativedelta(years=+5)
  last_5_years_date = last_date - rd
  df_last_5_years = util_return_date_values(df_series,last_5_years_date)
  try:
    last_5_years_value = df_last_5_years[asset].values[0]
  except IndexError as e:
    df_last_5_years = 0

  try:
    last_5_years_pct = (last_value - df_last_5_years[asset].values[0]) / df_last_5_years[asset].values[0]
  except (ZeroDivisionError, TypeError) as e:
    df_last_5_years = 0

  return asset, last_date, last_value, ytd_value, ytd_pct, last_5_days_value, last_5_days_pct, last_month_value, last_month_pct, last_3_months_value, last_3_months_pct, last_5_years_value, last_5_years_pct


def util_return_date_values(df_series, temp_date):
  df_return_row = pd.DataFrame()

  column_headers = list(df_series.columns.values)

  if(temp_date.isoweekday() in [1,2,3,4,5]):
    df_return_row = df_series.loc[df_series['series_date'] == temp_date.isoformat()]

  if df_return_row.shape[0] == 0:
    #Get next weekday and try and get series data again 
    next_weekday = util_calculate_next_weekday(temp_date)

    df_return_row = df_series.loc[df_series['series_date'] == next_weekday.isoformat()]

  if df_return_row.shape[0] == 0:
    #Get next weekday and try and get series data again 
    next_weekday = util_calculate_next_weekday(next_weekday)
    df_return_row = df_series.loc[df_series['series_date'] == next_weekday.isoformat()]

  return df_return_row

def util_calculate_next_weekday(temp_date):
  # Calculate next weekday
  r = rrule.rrule(rrule.DAILY,
                  byweekday=[rrule.MO, rrule.TU, rrule.WE, rrule.TH, rrule.FR],
                  dtstart=temp_date)

  # Create a rruleset
  rs = rrule.rruleset()
  rs.rrule(r)
  next_weekday = rs[0].date()

  return next_weekday

def get_yf_price_action(ticker,logger):
  
# Replace with the following:
# https://financialmodelingprep.com/api/v3/profile/MSFT?apikey=14afe305132a682a2742743df532707d

  json_yf_module_summaryProfile = {}
  json_yf_module_financialData = {}
  json_yf_module_summaryDetail = {}
  json_yf_module_price = {}
  json_yf_module_defaultKeyStatistics = {}

  yf_error = False

  modules = ['summaryProfile','financialData','summaryDetail','price','defaultKeyStatistics']
  #import pdb; pdb.set_trace()

  try:
    json_yf_module_summaryProfile = json.loads(get_page("https://query1.finance.yahoo.com/v6/finance/quoteSummary/%s?modules=%s" % (ticker,modules[0])).content)
  except Exception as e:
    yf_error = True
    logger.exception('Failed to load data from python: %s', e)

  try:
    json_yf_module_financialData = json.loads(get_page("https://query1.finance.yahoo.com/v6/finance/quoteSummary/%s?modules=%s" % (ticker,modules[1])).content)
  except Exception as e:
    logger.exception('Failed to load data from python: %s', e)

  try:
    json_yf_module_summaryDetail = json.loads(get_page("https://query1.finance.yahoo.com/v6/finance/quoteSummary/%s?modules=%s" % (ticker,modules[2])).content)
  except Exception as e:
    logger.exception('Failed to load data from python: %s', e)

  try:
    json_yf_module_price = json.loads(get_page("https://query1.finance.yahoo.com/v6/finance/quoteSummary/%s?modules=%s" % (ticker,modules[3])).content)
  except Exception as e:
    logger.exception('Failed to load data from python: %s', e)

  try:
    json_yf_module_defaultKeyStatistics = json.loads(get_page("https://query1.finance.yahoo.com/v6/finance/quoteSummary/%s?modules=%s" % (ticker,modules[4])).content)
  except Exception as e:
    logger.exception('Failed to load data from python: %s', e)

  #url_yf_modules = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/%s?modules=summaryProfile,financialData,summaryDetail,price,defaultKeyStatistics" % (ticker)

  return json_yf_module_summaryProfile, json_yf_module_financialData,json_yf_module_summaryDetail,json_yf_module_price,json_yf_module_defaultKeyStatistics, yf_error

def get_financialmodelingprep_price_action(ticker,logger):
  
  url_profile = 'https://financialmodelingprep.com/api/v3/profile/%s?apikey=%s' % (ticker,config.API_KEY_FMP) 
  url_quote = 'https://financialmodelingprep.com/api/v3/quote/%s?apikey=%s' % (ticker,config.API_KEY_FMP)

  url_company_outlook = 'https://financialmodelingprep.com/api/v4/company-outlook?symbol=%s&apikey=%s' % (ticker,config.API_KEY_FMP)
  url_balance_sheet = 'https://financialmodelingprep.com/api/v3/balance-sheet-statement/%s?period=annual&apikey=%s' % (ticker,config.API_KEY_FMP)
  url_key_metrics = 'https://financialmodelingprep.com/api/v3/key-metrics/%s?period=annual&apikey=%s' % (ticker,config.API_KEY_FMP)
  url_price_target_summary = 'https://financialmodelingprep.com/api/v4/price-target-summary?symbol=%s&apikey=%s' % (ticker,config.API_KEY_FMP)
  url_key_metrics_ttm = 'https://financialmodelingprep.com/api/v3/key-metrics-ttm/%s?apikey=%s' % (ticker,config.API_KEY_FMP)
  url_company_core_information = 'https://financialmodelingprep.com/api/v4/company-core-information?symbol=%s&apikey=%s' % (ticker,config.API_KEY_FMP)
  url_company_income_statement = 'https://financialmodelingprep.com/api/v3/income-statement/%s?period=annual&apikey=%s'% (ticker,config.API_KEY_FMP)

  error = False

  json_module_company_outlook = {}
  json_module_profile = {}
  json_module_quote = {}
  json_module_balance_sheet = {}
  json_module_key_metrics = {}
  json_module_price_target_summary = {}
  json_module_key_metrics_ttm = {}
  json_module_company_core_information = {}
  json_module_company_income_statement = {}

  try:
    json_module_company_outlook = json.loads(get_page(url_company_outlook).content)
    json_module_profile = json.loads(get_page(url_profile).content)
    json_module_quote = json.loads(get_page(url_quote).content)
    json_module_balance_sheet = json.loads(get_page(url_balance_sheet).content)
    json_module_key_metrics = json.loads(get_page(url_key_metrics).content)
    json_module_price_target_summary = json.loads(get_page(url_price_target_summary).content)
    json_module_key_metrics_ttm = json.loads(get_page(url_key_metrics_ttm).content)
    json_module_company_core_information = json.loads(get_page(url_company_core_information).content)
    json_module_company_income_statement = json.loads(get_page(url_company_income_statement).content)

  except Exception as e:
    error = True
    logger.exception('Failed to load data from financial modeling prep: %s', e)

  return json_module_profile, json_module_quote, json_module_balance_sheet, json_module_key_metrics, json_module_company_outlook, json_module_price_target_summary,json_module_key_metrics_ttm, json_module_company_core_information, json_module_company_income_statement, error

def set_financialmodelingprep_dcf(df_tickers,logger):
  success = False

  for index, row in df_tickers.iterrows():
    ticker = row['symbol'] 

    url_dcf_url = 'https://financialmodelingprep.com/api/v3/discounted-cash-flow/%s?apikey=%s' % (ticker,config.API_KEY_FMP)
    json_module_dcf_inputs = json.loads(get_page(url_dcf_url).content)
    try:
      dcf = json_module_dcf_inputs[0]['dcf']
      stock_price =  json_module_dcf_inputs[0]['Stock Price']
      is_close = ""
      valued = ""
      # calculate how far current price is from dcf value
      if(np.isclose(dcf,stock_price,rtol=0.10)):
        is_close = "fair price"
      elif(np.isclose(dcf,stock_price,rtol=0.20)):
        is_close = "moderate"
      else:
        is_close = "grossly"
      if(float(dcf) < float(stock_price)):
        valued = "overvalued"
      else:
        valued = "undervalued"

      #print(f'DCF: {dcf}')
      #print(f'Stock Price: {stock_price}')
      #print()
      if(is_close == 'fair price'):
        under_over = f'{is_close}'
      else:
        under_over = f'{is_close} {valued}'

      list_dcf = [stock_price, dcf, under_over]
      #Create DF containing this data
      data = {'stock_price': [], 'dcf': [], 'under_over': []}

      # Convert the dictionary into DataFrame
      df_dcf = pd.DataFrame(data)
      df_dcf.loc[len(df_dcf.index)] = list_dcf
      # get ticker cid
      cid = sql_get_cid(ticker)
      if(cid):
        rename_cols = {}
        add_col_values = {"cid": cid}
        conflict_cols = "cid"

        success = sql_write_df_to_db(df_dcf, "CompanyStockValueDCF", rename_cols, add_col_values, conflict_cols)

        logger.info(f'Successfully Saved Stock Value DCF for {ticker}')

    except IndexError as e:
      logger.error(f'Could Not Save Stock Value DCF for {ticker}: {e}')    

  return success

def write_zacks_ticker_data_to_db(df_tickers, logger):
  #create new df using columns from old df
  df_tickers_updated = pd.DataFrame(columns=df_tickers.columns)
  connection, cursor = sql_open_db()

  for index, row in df_tickers.iterrows():
      symbol = row["Ticker"]
      company = row["Company Name"] 
      sector = row["Sector"] 
      industry = row["Industry"] 
      exchange = row["Exchange"] 

      # Get market cap as well, because we want to use it in the earnings calendar
      market_cap = row["Market Cap (mil)"] 
      exchanges = ['NYSE', 'NSDQ']
      # Check that Company is not empty, and only add to the master ticker file if company is not empty
      if(company != '' and exchange in exchanges):
          try:
              shares_outstanding = float(row["shares_outstanding"])
              #shares_outstanding = shares_outstanding *1000000                    
          except Exception as e:
              shares_outstanding = 0
          logger.info(f'Loading Zacks stock data for {symbol}')
      try:
          # Write to database        
          sqlCmd = """INSERT INTO company (symbol, company_name, sector, industry, exchange, market_cap, shares_outstanding) VALUES
              ('{}','{}','{}','{}','{}','{}','{}')
              ON CONFLICT (symbol)
              DO
                  UPDATE SET company_name=excluded.company_name,sector=excluded.sector,industry=excluded.industry,exchange=excluded.exchange,market_cap=excluded.market_cap,shares_outstanding=excluded.shares_outstanding;
          """.format(sql_escape_str(symbol), sql_escape_str(company), sql_escape_str(sector), sql_escape_str(industry), sql_escape_str(exchange), market_cap, shares_outstanding)
          cursor.execute(sqlCmd)

          #Make the changes to the database persistent
          connection.commit()
          df_tickers_updated = df_tickers_updated.append(row)

          logger.info(f'Successfully Written Zacks data into database {symbol}')
      except AttributeError as e:
          logger.exception(f'Most likely an ETF and therefore not written to database, removed from df_tickers: {symbol}')

  success = sql_close_db(connection, cursor)

  return df_tickers_updated, success


def set_finwiz_stock_data(df_tickers, logger):
  success = False

  # Load finwiz exclusion list
  csv_file_path = '/data/finwiz_exclusion_list.csv'
  df_exclusion_list = convert_csv_to_dataframe(csv_file_path)

  for index, row in df_tickers.iterrows():
    ticker = row['Ticker']  
    
    if(df_exclusion_list['Ticker'].str.contains(ticker).any() == False):   
      logger.info(f'Getting finwiz stock data for {ticker}')

      df_company_data = pd.DataFrame()
      url_finviz = "https://finviz.com/quote.ashx?t=%s" % (ticker)
      try:
        page = get_page(url_finviz)

        soup = BeautifulSoup(page.content, 'html.parser')

        table = soup.find_all('table')
        table_rows = table[9].find_all('tr', recursive=False)

        emptyDict = {}

        #Get rows of data.
        for tr in table_rows:
            tds = tr.find_all('td')
            boolKey = True
            keyValueSet = False
            for td in tds:
                if boolKey:
                    key = td.text.strip()
                    boolKey = False                
                else:
                    value = td.text.strip()
                    boolKey = True
                    keyValueSet = True                

                if keyValueSet:
                    emptyDict[key] = value
                    keyValueSet = False

        df_company_data.loc[ticker, 'PE'] = emptyDict['P/E']
        df_company_data.loc[ticker, 'EPS_TTM'] = emptyDict['EPS (ttm)']
        df_company_data.loc[ticker, 'PE_FORWARD'] = emptyDict['Forward P/E']
        df_company_data.loc[ticker, 'EPS_Y1'] = emptyDict['EPS next Y']
        df_company_data.loc[ticker, 'PEG'] = emptyDict['PEG']
        df_company_data.loc[ticker, 'EPS_Y0'] = emptyDict['EPS this Y']
        df_company_data.loc[ticker, 'PRICE_BOOK'] = emptyDict['P/B']
        df_company_data.loc[ticker, 'PRICE_BOOK'] = emptyDict['P/B']
        df_company_data.loc[ticker, 'PRICE_SALES'] = emptyDict['P/S']
        df_company_data.loc[ticker, 'TARGET_PRICE'] = emptyDict['Target Price']
        df_company_data.loc[ticker, 'ROE'] = emptyDict['ROE']
        df_company_data.loc[ticker, '52W_RANGE'] = emptyDict['52W Range']
        df_company_data.loc[ticker, 'QUICK_RATIO'] = emptyDict['Quick Ratio']
        df_company_data.loc[ticker, 'GROSS_MARGIN'] = emptyDict['Gross Margin']
        df_company_data.loc[ticker, 'CURRENT_RATIO'] = emptyDict['Current Ratio']

        # get ticker cid
        cid = sql_get_cid(ticker)
        if(cid):
          #TODO: write records to database
          rename_cols = {"52W_RANGE": "RANGE_52W"}
          add_col_values = {"cid": cid}
          conflict_cols = "cid"

          success = sql_write_df_to_db(df_company_data, "CompanyRatio", rename_cols, add_col_values, conflict_cols)

          logger.info(f'Successfully Saved finwiz stock data for {ticker}')

      except Exception as e:
        logger.exception(f'Did not return finwiz stock data for {ticker}: {e}')    

  return success

def set_stockrow_stock_data(df_tickers, logger):
  success = False
  failed_tickers = []
  for index, row in df_tickers.iterrows():
    ticker = row['Ticker']  
    count = index

    logger.info(f'Getting stockrow data for ({index}) {ticker}')

    df = pd.DataFrame()
    df2 = pd.DataFrame()

    try:
      page = get_page_selenium('https://stockrow.com/%s' % (ticker))
    except TimeoutError as e:
      failed_tickers.append(ticker)
      logger.exception(f'Timed Out for {ticker} from stockrow')
    except ste as e:
      failed_tickers.append(ticker)
      logger.exception(f'Selenium Timed Out for {ticker} from stockrow')

    soup = BeautifulSoup(page, 'html.parser')

    #Only execute if the stockrow page has a table containing data about the ticker
    if(soup.find_all('table')):
      try:
        table = soup.find_all('table')[0]
        table_rows = table.find_all('tr', recursive=True)
        table_rows_header = table.find_all('tr')[0].find_all('th')

        index = 0

        for header in table_rows_header:
          df.insert(index,header.text,[],True)
          index+=1
        #print("did we get any rows?")
        #print(table_rows)
        #Get rows of data.
        for tr in table_rows:
          if(tr.find_all('td')):
            #print(tr.find_all('td')[len(tr.find_all('td'))-1].text.strip())
            row_heading = tr.find_all('td')[len(tr.find_all('td'))-1].text.strip().replace("Created with Highcharts 8.2.2foo","")   
            if(row_heading in ['Revenue','EBT','Net Income','PE Ratio','Earnings/Sh','Total Debt','Cash Flow/Sh','Book Value/Sh','FCF']):
              tds = tr.find_all('td', recursive=True)
              if(tds):
                temp_row = []
                for td in tds:
                  temp_row.append(td.text.strip().replace("Created with Highcharts 8.2.2foo",""))        

                df.loc[len(df.index)] = temp_row
      except IndexError as e:
        failed_tickers.append(ticker)
        logger.exception(f'Did not load table for {ticker} from stockrow')

    #Only execute the following if we have a dataframe that contains data
    if(len(df) > 0):
      try:
        df.rename(columns={ df.columns[13]: "YEAR" }, inplace = True)

        # get a list of columns
        cols = list(df)

        # move the column to head of list using index, pop and insert
        cols.insert(0, cols.pop(cols.index('YEAR')))

        # reorder
        df = df.loc[:, cols]
      except IndexError as e:
        failed_tickers.append(ticker)
        logger.exception(f'No YEAR column for {ticker} from stockrow')

    #Get WSJ Data
    try:
      page = get_page_selenium("https://www.wsj.com/market-data/quotes/%s/financials/annual/income-statement" % (ticker))
    except TimeoutError as e:
      failed_tickers.append(ticker)
      logger.exception(f'Timed Out for {ticker} from wsj')
    except ste as e:
      failed_tickers.append(ticker)
      logger.exception(f'Selenium Timed Out for {ticker} from wsj')
       
    soup = BeautifulSoup(page, 'html.parser')
    tables = soup.find_all('table')
    try:
      table_rows = tables[0].find_all('tr', recursive=True)

      table_rows_header = tables[0].find_all('tr')[0].find_all('th')

      #TODO: Get EBITDA from table
      
      index = 0
      for header in table_rows_header:
        if(index == 0):
          df2.insert(0,"YEAR",[],True)
        else:
          #import pdb; pdb.set_trace()
          if(header.text.strip()):
            df2.insert(index,header.text.strip(),[],True)
          else:
            #No header exists, so put in a NULL value for the header so that we can remove it later
            df2.insert(index,'NULL',[],True)
        index+=1
      
      #drop the last column has it does not contain any data but rather is a graphic of the trend
      df2 = df2.iloc[: , :-1]
      
      #Insert New Row. Format the data to show percentage as float

      for tr in table_rows:

        if(tr.find_all('td')):
          if(tr.find_all('td')[0].text in ['EBITDA']):
            temp_row = []

            td = tr.find_all('td')
            for obs in td:
              if(len(obs.text.strip()) > 0):
                text = obs.text
                temp_row.append(text)        
            try:
              df2.loc[len(df2.index)] = temp_row
            except ValueError as e:
              #Handling when the html of the table is incorrect and results in an additional element in the row
              logger.exception(f'Mismatched df2 row for {ticker}')
              pass
            break
      #print(df2)
      #df2.drop([" "], axis=1) #Hack: Drop any null columns. Better to just remove them upstream
    except IndexError as e:
      failed_tickers.append(ticker)
      logger.exception(f'Did not load table for {ticker} from wsj')
       
    #Only proceed to format the data and write to database if we have data about the ticker at this point
    if(df.empty == False):      
      #Lets drop all NULL columns from df2
      if('NULL' in df2):
        df2 = df2.drop(['NULL'],axis=1)  

      df = df.append(df2,ignore_index = True)    
      df_transposed = transpose_df(df)
      #import pdb; pdb.set_trace()
      #Clean the table by dropping any rows that do not have Revenue data
      df_transposed = df_transposed[df_transposed['Revenue'].notna()]    
      df_transposed = df_transposed[df_transposed['Revenue'] != '–']
  
      #if(ticker == 'AB'):
      #  import pdb; pdb.set_trace()
      #df_transposed = df.T
      #new_header = df_transposed.iloc[0] #grab the first row for the header
      #df_transposed = df_transposed[1:] #take the data less the header row
      #df_transposed.columns = new_header #set the header row as the df header

      df_transposed = df_transposed.rename(columns={
        "Revenue":"SALES",          
        "EBT":"EBIT",               
        "Net Income":"NET_INCOME",        
        "PE Ratio":"PE_RATIO",          
        "Earnings/Sh":"EARNINGS_PER_SHARE",       
        "Cash Flow/Sh":"CASH_FLOW_PER_SHARE",      
        "Book Value/Sh":"BOOK_VALUE_PER_SHARE",     
        "Total Debt":"TOTAL_DEBT",        
        "EBITDA": "EBITDA",        
        "FCF": "FCF"           
        })  

      if('EBITDA' in df_transposed.columns):
        df_transposed = dataframe_convert_to_numeric(df_transposed, 'EBITDA', logger)
        
      if('SALES' in df_transposed.columns):
        df_transposed = dataframe_convert_to_numeric(df_transposed, 'SALES', logger)

      if('EBIT' in df_transposed.columns):
        df_transposed = dataframe_convert_to_numeric(df_transposed, 'EBIT', logger)

      if('NET_INCOME' in df_transposed.columns):
        df_transposed = dataframe_convert_to_numeric(df_transposed, 'NET_INCOME', logger)

      if('PE_RATIO' in df_transposed.columns):
        df_transposed = dataframe_convert_to_numeric(df_transposed, 'PE_RATIO', logger)

      if('EARNINGS_PER_SHARE' in df_transposed.columns):
        df_transposed = dataframe_convert_to_numeric(df_transposed, 'EARNINGS_PER_SHARE', logger)

      if('CASH_FLOW_PER_SHARE' in df_transposed.columns):
        df_transposed = dataframe_convert_to_numeric(df_transposed, 'CASH_FLOW_PER_SHARE', logger)

      if('BOOK_VALUE_PER_SHARE' in df_transposed.columns):
        df_transposed = dataframe_convert_to_numeric(df_transposed, 'BOOK_VALUE_PER_SHARE', logger)

      if('TOTAL_DEBT' in df_transposed.columns):
        df_transposed = dataframe_convert_to_numeric(df_transposed, 'TOTAL_DEBT', logger)

      if('FCF' in df_transposed.columns):
        df_transposed = dataframe_convert_to_numeric(df_transposed, 'FCF', logger)

      #import pdb; pdb.set_trace()
      todays_date = date.today()
      one_year_ago = dt(todays_date.year - 1, 12, 31)
      two_year_ago = dt(todays_date.year - 2, 12, 31)
      three_year_ago = dt(todays_date.year - 3, 12, 31)
      one_year_future = dt(todays_date.year + 1, 12, 31)
      two_year_future = dt(todays_date.year + 2, 12, 31)

      list_dates = []
      list_dates.append(str(three_year_ago.year))
      list_dates.append(str(two_year_ago.year))
      list_dates.append(str(one_year_ago.year))
      list_dates.append(str(todays_date.year))
      list_dates.append(str(one_year_future.year))
      list_dates.append(str(two_year_future.year))
      #import pdb; pdb.set_trace()

      #Remove any rows that have dates that are too old or to new
      df_transposed = df_transposed.reset_index()
      df_transposed = df_transposed.loc[df_transposed['index'].isin(list_dates)]
      df_transposed = df_transposed.reset_index(drop=True)
      df_transposed = df_transposed.rename_axis(None, axis=1)
      df_transposed = df_transposed.rename(columns={'index':'YEAR'})
      #import pdb; pdb.set_trace()
      #df_transposed = df_transposed.loc[list_dates]

      #st.write(f'Data for ({count}) {ticker}')
      #st.write(df_transposed)    

      # get ticker cid
      cid = sql_get_cid(ticker)
      if(cid):
        # write records to database
        rename_cols = {"YEAR": "FORECAST_YEAR"}
        add_col_values = {"cid": cid}
        conflict_cols = "cid, forecast_year"
        success = sql_write_df_to_db(df_transposed, "CompanyForecast", rename_cols, add_col_values, conflict_cols)
        logger.info(f'Successfully Saved stockrow data for {ticker}')
      else:
        failed_tickers.append(ticker)
        logger.exception(f'COULD NOT save stockrow data for {ticker} ({cid}) because there was no cid')

  # to remove duplicated from list 
  failed_tickers = list(set(failed_tickers))         
  logger.exception(f'Failed Tickers: {failed_tickers}')
  return success

def set_stlouisfed_data(series_codes, logger):
  success = False
  for series_code in series_codes:
    url = "https://api.stlouisfed.org/fred/series/observations?series_id=%s&api_key=8067a107f45ff78491c1e3117245a0a3&file_type=json" % (series_code,)
    try:
      resp = get_page(url)

      json = resp.json() 
      
      df = pd.DataFrame(columns=["DATE",series_code])

      for i in range(len(json["observations"])):
        if(json["observations"][i]["value"] == '.'):
          obs = '0.00'
        else:
          obs = json["observations"][i]["value"]
        df = df.append({"DATE": json["observations"][i]["date"], series_code: obs}, ignore_index=True)

      df['DATE'] = pd.to_datetime(df['DATE'],format='%Y-%m-%d')
      df[series_code] = df[series_code].astype('float64') 

      # write records to database
      rename_cols = {'DATE':'series_date'}
      conflict_cols = 'series_date'
      success = sql_write_df_to_db(df, "Macro_StLouisFed", rename_cols=rename_cols, conflict_cols=conflict_cols)

      logger.info("Retrieved Data for Series %s" % (series_code,))
      success = True
    except Exception as e:
      #import pdb; pdb.set_trace()
      logger.error("Could Not get Data for Series %s" % (series_code,))

  return success


def set_zacks_balance_sheet_shares(df_tickers, logger):
  success = False
  for index, row in df_tickers.iterrows():
    ticker = row['Ticker']  
    logger.info(f'Getting zacks balance sheet for {ticker}')
    df_balance_sheet_annual = pd.DataFrame()
    df_balance_sheet_quarterly = pd.DataFrame()

    #only balance sheet that shows treasury stock line item
    page = get_page('https://www.zacks.com/stock/quote/%s/balance-sheet' % (ticker))

    soup = BeautifulSoup(page.content, 'html.parser')
    try:
      table = soup.find_all('table')

      table_annual = table[4]
      table_quarterly = table[7]

      df_balance_sheet_annual = convert_html_table_to_df(table_annual,False)
      df_balance_sheet_quarterly = convert_html_table_to_df(table_quarterly,False)

      df_balance_sheet_annual = transpose_df(df_balance_sheet_annual)

      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns={"Preferred Stock":"PREFERRED_STOCK"})                        
      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns={"Common Stock (Par)":"COMMON_STOCK_PAR"})                          
      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns={"Capital Surplus":"CAPITAL_SURPLUS"})                             
      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns={"Retained Earnings":"RETAINED_EARNINGS"})                           
      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns={"Other Equity":"OTHER_EQUITY"})                                
      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns={"Treasury Stock":"TREASURY_STOCK"})                              
      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns={"Total Shareholder's Equity":"TOTAL_SHAREHOLDERS_EQUITY"})                  
      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns={"Total Liabilities & Shareholder's Equity":"TOTAL_LIABILITIES_SHAREHOLDERS_EQUITY"})    
      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns={"Total Common Equity":"TOTAL_COMMON_EQUITY"})                         
      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns={"Shares Outstanding":"SHARES_OUTSTANDING"})                          
      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns={"Book Value Per Share":"BOOK_VALUE_PER_SHARE"})  
      #import pdb; pdb.set_trace()

      df_balance_sheet_annual = dataframe_convert_to_numeric(df_balance_sheet_annual,'PREFERRED_STOCK', logger)
      df_balance_sheet_annual = dataframe_convert_to_numeric(df_balance_sheet_annual,'COMMON_STOCK_PAR', logger)
      df_balance_sheet_annual = dataframe_convert_to_numeric(df_balance_sheet_annual,'CAPITAL_SURPLUS', logger)
      df_balance_sheet_annual = dataframe_convert_to_numeric(df_balance_sheet_annual,'RETAINED_EARNINGS', logger)
      df_balance_sheet_annual = dataframe_convert_to_numeric(df_balance_sheet_annual,'OTHER_EQUITY', logger)
      df_balance_sheet_annual = dataframe_convert_to_numeric(df_balance_sheet_annual,'TREASURY_STOCK', logger)
      df_balance_sheet_annual = dataframe_convert_to_numeric(df_balance_sheet_annual,'TOTAL_SHAREHOLDERS_EQUITY', logger)
      df_balance_sheet_annual = dataframe_convert_to_numeric(df_balance_sheet_annual,'TOTAL_LIABILITIES_SHAREHOLDERS_EQUITY', logger)
      df_balance_sheet_annual = dataframe_convert_to_numeric(df_balance_sheet_annual,'TOTAL_COMMON_EQUITY', logger)
      df_balance_sheet_annual = dataframe_convert_to_numeric(df_balance_sheet_annual,'SHARES_OUTSTANDING', logger)
      df_balance_sheet_annual = dataframe_convert_to_numeric(df_balance_sheet_annual,'BOOK_VALUE_PER_SHARE', logger)
      #import pdb; pdb.set_trace()

      df_balance_sheet_annual.reset_index(inplace=True)
      df_balance_sheet_annual = df_balance_sheet_annual.rename(columns = {'index':'DATE'})
      df_balance_sheet_annual['DATE'] = pd.to_datetime(df_balance_sheet_annual['DATE'],format='%m/%d/%Y')
      df_balance_sheet_annual = df_balance_sheet_annual.rename_axis(None, axis=1)

      df_balance_sheet_quarterly = transpose_df(df_balance_sheet_quarterly)
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns={"Preferred Stock":"PREFERRED_STOCK"})                        
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns={"Common Stock (Par)":"COMMON_STOCK_PAR"})                          
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns={"Capital Surplus":"CAPITAL_SURPLUS"})                             
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns={"Retained Earnings":"RETAINED_EARNINGS"})                           
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns={"Other Equity":"OTHER_EQUITY"})                                
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns={"Treasury Stock":"TREASURY_STOCK"})                              
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns={"Total Shareholder's Equity":"TOTAL_SHAREHOLDERS_EQUITY"})                  
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns={"Total Liabilities & Shareholder's Equity":"TOTAL_LIABILITIES_SHAREHOLDERS_EQUITY"})    
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns={"Total Common Equity":"TOTAL_COMMON_EQUITY"})                         
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns={"Shares Outstanding":"SHARES_OUTSTANDING"})                          
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns={"Book Value Per Share":"BOOK_VALUE_PER_SHARE"})  
      df_balance_sheet_quarterly = dataframe_convert_to_numeric(df_balance_sheet_quarterly,'PREFERRED_STOCK', logger)
      df_balance_sheet_quarterly = dataframe_convert_to_numeric(df_balance_sheet_quarterly,'COMMON_STOCK_PAR', logger)
      df_balance_sheet_quarterly = dataframe_convert_to_numeric(df_balance_sheet_quarterly,'CAPITAL_SURPLUS', logger)
      df_balance_sheet_quarterly = dataframe_convert_to_numeric(df_balance_sheet_quarterly,'RETAINED_EARNINGS', logger)
      df_balance_sheet_quarterly = dataframe_convert_to_numeric(df_balance_sheet_quarterly,'OTHER_EQUITY', logger)
      df_balance_sheet_quarterly = dataframe_convert_to_numeric(df_balance_sheet_quarterly,'TREASURY_STOCK', logger)
      df_balance_sheet_quarterly = dataframe_convert_to_numeric(df_balance_sheet_quarterly,'TOTAL_SHAREHOLDERS_EQUITY', logger)
      df_balance_sheet_quarterly = dataframe_convert_to_numeric(df_balance_sheet_quarterly,'TOTAL_LIABILITIES_SHAREHOLDERS_EQUITY', logger)
      df_balance_sheet_quarterly = dataframe_convert_to_numeric(df_balance_sheet_quarterly,'TOTAL_COMMON_EQUITY', logger)
      df_balance_sheet_quarterly = dataframe_convert_to_numeric(df_balance_sheet_quarterly,'SHARES_OUTSTANDING', logger)
      df_balance_sheet_quarterly = dataframe_convert_to_numeric(df_balance_sheet_quarterly,'BOOK_VALUE_PER_SHARE', logger)
      df_balance_sheet_quarterly.reset_index(inplace=True)
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename(columns = {'index':'DATE'})
      df_balance_sheet_quarterly['DATE'] = pd.to_datetime(df_balance_sheet_quarterly['DATE'],format='%m/%d/%Y')
      df_balance_sheet_quarterly = df_balance_sheet_quarterly.rename_axis(None, axis=1)

      # get ticker cid
      cid = sql_get_cid(ticker)
      if(cid):
        #TODO: write records to database
        rename_cols = {"DATE": "DT"}
        add_col_values_annually = {"REPORTING_PERIOD": "annual", "cid": cid}
        conflict_cols = "cid, DT, REPORTING_PERIOD"

        success = sql_write_df_to_db(df_balance_sheet_annual, "BalanceSheet", rename_cols, add_col_values_annually, conflict_cols)

        add_col_values_quarterly = {"REPORTING_PERIOD": "quarterly", "cid": cid}
        success = sql_write_df_to_db(df_balance_sheet_quarterly, "BalanceSheet", rename_cols, add_col_values_quarterly, conflict_cols)

        logger.info(f'Successfully Saved zacks balance sheet data for {ticker}')
      
    except IndexError as e:
      logger.exception(f'No balance sheet for {ticker}')
      pass

  return success

def set_zacks_peer_comparison(df_tickers, logger):
  success = False
  for index, row in df_tickers.iterrows():
    ticker = row['Ticker']  

    logger.info(f'Getting zacks peer comparison for {ticker}')

    df_peer_comparison = pd.DataFrame()
    url = "https://www.zacks.com/stock/research/%s/industry-comparison" % (ticker)

    page = get_page(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    table = soup.find_all('table')

    try:
      table_peer_comparison = table[2]
      df_peer_comparison = convert_html_table_to_df(table_peer_comparison,True)
      new = df_peer_comparison["Symbol"].str.split(' ',n=1,expand=True)
      df_peer_comparison["Ticker"] = new[0]
      df_peer_comparison = df_peer_comparison.drop(['Zacks Rank', 'Symbol'], axis=1)
      df_peer_comparison = df_peer_comparison[df_peer_comparison.Ticker != ticker]

      df_peer_comparison = df_peer_comparison.iloc[:4,:]

      df_peer_comparison = df_peer_comparison.rename(columns={df_peer_comparison.columns[0]: 'PEER_COMPANY'})
      df_peer_comparison = df_peer_comparison.rename(columns={df_peer_comparison.columns[1]: 'PEER_TICKER'})

      # get ticker cid
      cid = sql_get_cid(ticker)
      if(cid):
        # write records to database
        rename_cols = None
        add_col_values = {"cid": cid}
        conflict_cols = "cid, peer_ticker"
        success = sql_write_df_to_db(df_peer_comparison, "CompanyPeerComparison", rename_cols, add_col_values, conflict_cols)
        logger.info(f'Successfully Saved Zacks Peer Comparison for {ticker}')
    except IndexError as e:
      logger.exception(f'Did not return Zacks Peer Comparison for {ticker}')      
    except AttributeError as e:
      logger.exception(f'Did not return Zacks Peer Comparison for {ticker}')      
    except KeyError as e:
      logger.exception(f'Did not return Zacks Peer Comparison for {ticker}')      

  return success

def set_zacks_earnings_surprises(df_tickers, logger):
  success = False
  for index, row in df_tickers.iterrows():
    ticker = row['Ticker']  
    logger.info(f'Getting zacks earnings surprises for {ticker}')

    df_earnings_release_date = pd.DataFrame()
    df_earnings_surprises = pd.DataFrame()
    df_sales_surprises = pd.DataFrame()

    url = "https://www.zacks.com/stock/research/%s/earnings-calendar" % (ticker)

    page = get_page(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    new_df_earnings = pd.DataFrame()
    
    #Get Earnings Release Date
    try:
      table_earnings_release_date = soup.find_all('table')[2]
      df_earnings_release_date = convert_html_table_to_df(table_earnings_release_date,True)
      df_earnings_release_date['Release Date'] = df_earnings_release_date['Report Date'].str[:10]
      df_earnings_release_date = df_earnings_release_date.drop(['Zacks Consensus Estimate', 'Earnings ESP','Report Date'], axis=1)
      df_earnings_release_date['Release Date'] = pd.to_datetime(df_earnings_release_date['Release Date'],format='%m/%d/%Y')
    except (IndexError,AttributeError) as e:
      logger.exception(f'No earnings date for {ticker}. It is probably an ETF')
      pass
    except (ValueError, KeyError) as e:
      logger.exception(f'Earnings Date is NA for {ticker}')

    try:
      #javascript tag contains an object with all the data
      scripts = soup.find_all('script')[20]
 
      match_pattern = re.compile(r'(?<=\= ).*\}')
      match_string = scripts.text.strip().replace('\n','')
      matches = match_pattern.findall(match_string)

      #Extract the overall string that should contain the earnings and sales data
      match_string = matches[0]

      #Extra formatting that needs to be cleaned up
      match_string = match_string.replace('<div class=\\"right pos positive pos_icon showinline up\\">','')
      match_string = match_string.replace('<div class=\\"right neg negative neg_icon showinline down\\">','')
      match_string = match_string.replace('<div class=\\"right pos_na showinline\\">','')
      match_string = match_string.replace('</div>','')

      # regex needs to be tighter: "earnings_announcements_earnings_table" : <START>[[ ]]</END>
      match_pattern_earnings = re.compile(r'"earnings_announcements_earnings_table"[\s]*:[\s]*\[[\s]*\[[\s"0-9/,$.+%A-Za-z\]\[-]*][\s]*\]') ## NEED TO FIX
      match_pattern_sales = re.compile(r'"earnings_announcements_sales_table"[\s]*:[\s]*\[[\s]*\[[\s"0-9/,$.+%A-Za-z\]\[-]*][\s]*\]') ## NEED TO FIX

      #Extract list for earnings and sales from script contents
      list_earnings_announcements_earnings = match_pattern_earnings.findall(match_string)[0]
      list_earnings_announcements_sales = match_pattern_sales.findall(match_string)[0]
 
      # Convert strings into 2 lists 
      # - list_earnings_announcements_earnings
      # - list_earnings_announcements_sales

      list_earnings_announcements_earnings = "{" + list_earnings_announcements_earnings + "}"
      list_earnings_announcements_sales = "{" + list_earnings_announcements_sales + "}"

      json_object_earnings = json.loads(list_earnings_announcements_earnings)
      json_object_sales = json.loads(list_earnings_announcements_sales)

      list_earnings_announcements_earnings = json_object_earnings['earnings_announcements_earnings_table']
      list_earnings_announcements_sales = json_object_sales['earnings_announcements_sales_table']

      #Add column names and format data
      df_earnings_surprises = convert_list_to_df(list_earnings_announcements_earnings)
      df_earnings_surprises = df_earnings_surprises.drop(df_earnings_surprises.iloc[:, 4:7],axis = 1)
      df_earnings_surprises.rename(columns={ df_earnings_surprises.columns[0]: "DATE",df_earnings_surprises.columns[1]: "PERIOD",df_earnings_surprises.columns[2]: "EPS_ESTIMATE",df_earnings_surprises.columns[3]: "EPS_REPORTED" }, inplace = True)
      df_earnings_surprises['DATE'] = pd.to_datetime(df_earnings_surprises['DATE'],format='%m/%d/%y')
      df_earnings_surprises = dataframe_convert_to_numeric(df_earnings_surprises,'EPS_ESTIMATE', logger)
      df_earnings_surprises = dataframe_convert_to_numeric(df_earnings_surprises,'EPS_REPORTED', logger)

      df_sales_surprises = convert_list_to_df(list_earnings_announcements_sales)
      df_sales_surprises = df_sales_surprises.drop(df_sales_surprises.iloc[:, 4:7],axis = 1)
      df_sales_surprises.rename(columns={ df_sales_surprises.columns[0]: "DATE",df_sales_surprises.columns[1]: "PERIOD",df_sales_surprises.columns[2]: "SALES_ESTIMATE",df_sales_surprises.columns[3]: "SALES_REPORTED" }, inplace = True)
      df_sales_surprises['DATE'] = pd.to_datetime(df_sales_surprises['DATE'],format='%m/%d/%y')
      df_sales_surprises = dataframe_convert_to_numeric(df_sales_surprises,'SALES_ESTIMATE', logger)
      df_sales_surprises = dataframe_convert_to_numeric(df_sales_surprises,'SALES_REPORTED', logger)

      new_df_earnings = pd.merge(df_earnings_surprises, df_sales_surprises,  how='left', left_on=['DATE','PERIOD'], right_on = ['DATE','PERIOD'])

      new_df_earnings = new_df_earnings.iloc[:4,:]

      # get ticker cid
      cid = sql_get_cid(ticker)
      if(cid):
        #TODO: write records to database
        rename_cols = {"DATE": "DT", "PERIOD": "REPORTING_PERIOD"}
        add_col_values = {"cid": cid}
        conflict_cols = "cid, DT, REPORTING_PERIOD"

        success = sql_write_df_to_db(new_df_earnings, "EarningsSurprise", rename_cols, add_col_values, conflict_cols)

        logger.info(f'Successfully Saved Zacks Earnings Surprises for {ticker}')

    except json.decoder.JSONDecodeError as e:
      logger.exception(f'JSON Loading error in Zacks Earnings Surprises for {ticker}')
      pass

    except IndexError as e:
      logger.exception(f'Did not load earnings or sales surprises for {ticker}')

  return success

def set_zacks_product_line_geography(df_tickers, logger):
  success = False
  for index, row in df_tickers.iterrows():
    ticker = row['Ticker']  
    table_product_line_geography = []
    table_rows = []

    logger.info(f'Getting zacks product line and geography for {ticker}')

    df_product_line = pd.DataFrame()
    df_geography = pd.DataFrame()
    pd.set_option('display.max_colwidth', None)

    url = "https://www.zacks.com/stock/research/%s/key-company-metrics-details" % (ticker)

    page = get_page(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    table = soup.find_all('table')

    try:
      table_product_line_geography = soup.find_all('table')[2]
      table_rows = table_product_line_geography.find_all('tr')
    except IndexError as e:
      logger.exception(f'Did not load Zacks Geography for {ticker}')

    file_dict = {}
    df = pd.DataFrame()

    #Insert New Row. Format the data to show percentage as float
    for tr in table_rows:
      temp_row = []
      table_rows_header = tr.find_all('th')

      if(len(table_rows_header) > 0):
        if(df.shape[0] > 0):
          file_dict[header_text] = copy.copy(df)     
          df = pd.DataFrame()
        index = 0

        for header in table_rows_header:
          df.insert(index,str(header.text).strip(),[],True)
          index+=1
        header_text = table_rows_header[0].text
        table_rows_header = []
      else:
        td = tr.find_all('td')
        for obs in td:      
          if(obs.p):
            text = obs.p.attrs['title']
          else:
            text = str(obs.text).strip()
          temp_row.append(text)        

        if(len(temp_row) == len(df.columns)):
          df.loc[len(df.index)] = temp_row
    #import pdb; pdb.set_trace()
    if(file_dict):
      try:
        df_product_line = file_dict['Revenue - Line of Business Segments']
        # Clean up dataframes
        df_product_line = df_product_line.drop(columns='YR Estimate', axis=1)
        df_product_line = df_product_line.iloc[:, 0:2]
        colname = df_product_line.columns[1]
        df_product_line = dataframe_convert_to_numeric(df_product_line,colname, logger)
        df_product_line = df_product_line.iloc[:4,:]

        df_product_line = df_product_line.rename(columns={df_product_line.columns[0]: 'BUSINESS_SEGMENT'})
        df_product_line = df_product_line.rename(columns={df_product_line.columns[1]: 'REVENUE'})

        logger.info(f'Successfully retrieved Zacks Product Line for {ticker}')

      except KeyError as e:
        logger.exception(f'Did not load Zacks Product Line for {ticker}')
        pass

      try:
        df_geography = file_dict['Revenue - Geographic Segments']
        df_geography = df_geography.drop(columns='YR Estimate', axis=1)
        df_geography = df_geography.iloc[:, 0:2]
        colname = df_geography.columns[1]
        df_geography = dataframe_convert_to_numeric(df_geography,colname, logger)
        df_geography = df_geography.iloc[:4,:]
        df_geography = df_geography.rename(columns={df_geography.columns[0]: 'REGION'})
        df_geography = df_geography.rename(columns={df_geography.columns[1]: 'REVENUE'})

        # get ticker cid
        cid = sql_get_cid(ticker)
        if(cid):
          #TODO: write records to database
          rename_cols = {}
          add_col_values = {"cid": cid}
          conflict_cols = "cid, REGION"

          success = sql_write_df_to_db(df_geography, "CompanyGeography", rename_cols, add_col_values, conflict_cols)

          logger.info(f'Successfully Saved Zacks Geography for {ticker}')

      except KeyError as e:
        logger.exception(f'Failed to retrieve Zacks Geography for {ticker}')
        pass
  
  return success

def set_earningswhispers_earnings_calendar(df_us_companies, logger):
  logger.info("Getting data from Earnings Whispers")

  df = pd.DataFrame()
  # Calculate next weekday
  r = rrule.rrule(rrule.DAILY,
                  byweekday=[rrule.MO, rrule.TU, rrule.WE, rrule.TH, rrule.FR],
                  dtstart=date.today())

  # Create a rruleset
  rs = rrule.rruleset()
  rs.rrule(r)
  next_weekday = rs[0].date()

  start_date = next_weekday   # start date
  end_date = next_weekday + relativedelta(weeks=+2)  # end date
  dt_index_dates = pd.date_range(start_date,end_date-timedelta(days=1),freq='d')
  list_dates = dt_index_dates.strftime('%Y-%m-%d').tolist()

  #TODO: Scrape data from yahoo finance
  df = scrape_yf_earnings_dates(list_dates, start_date, end_date, df_us_companies)

  # Get earnings calendar for the next fortnight
  #for x in range(1, 16):
  #    print("Day %s" % x)
  #    earnings_whispers_day_df = scrape_earningswhispers_day(x, df_us_companies)
  #    df = df.append(earnings_whispers_day_df, ignore_index=True)

  df = df.drop_duplicates(subset='Ticker', keep="first")
  df['Market Cap (Mil)'] = pd.to_numeric(df['Market Cap (Mil)'])
  df = df.sort_values(by=['Market Cap (Mil)'], ascending=False)
  df = df[:10].reset_index(drop=True)

  df['Date'] = pd.to_datetime(df['Date'],format='%Y-%m-%d')

  #Clear out old data
  sql_delete_all_rows('Macro_EarningsCalendar')

  #Write new data into table
  rename_cols = {'Date':'dt','Ticker':'ticker','Company Name':'company_name','Market Cap (Mil)':'market_cap_mil'}
  add_col_values = None
  conflict_cols = None

  success = sql_write_df_to_db(df, "Macro_EarningsCalendar", rename_cols, add_col_values, conflict_cols)

  logger.info("Successfully scraped data from Earnings Whispers")

  return success

def scrape_yf_earnings_dates(list_dates, start_date, end_date, df_us_companies):

  df = pd.DataFrame()
  
  # Add Date, Time, CompanyName, Ticker headers to dataframe
  df.insert(0,"Date",[],True)
  df.insert(1,"Ticker",[],True)
  df.insert(2,"Company Name",[],True)
  df.insert(3,"Market Cap (Mil)",[],True)

  for x in list_dates:

    url = "https://finance.yahoo.com/calendar/earnings?from=%s&to=%s&day=%s" % (start_date, end_date, x)
    page = get_page_selenium(url)
    soup = BeautifulSoup(page, 'html.parser')
    try:
      #TODO: Scrape company data and add to df
      date_str = x
      earnings_table = soup.find_all('table')[0]
      earnings_df = convert_html_table_to_df(earnings_table, contains_th=False)
      cols_drop = ["Event Name", "Earnings Call Time", "EPS Estimate", "Reported EPS", "Surprise(%)"]
      earnings_df = earnings_df.drop(cols_drop, axis=1)

      for index, row in earnings_df.iterrows():
        ticker_str = row['Symbol']
        #print("%s - %s" % (date_str, ticker_str))
        df_retrieved_company_data = df_us_companies.loc[df_us_companies['Ticker'] == ticker_str.strip().upper()].reset_index(drop=True)
        # Only if company exists on US stocks list, we add to df
        if(df_retrieved_company_data.shape[0] > 0):
          company_name_str = row['Company']

          temp_row1 = []
          temp_row1.append(date_str)
          temp_row1.append(ticker_str)
          temp_row1.append(company_name_str)

          # Get market cap from US Stocks list
          temp_row1.append(df_retrieved_company_data['Market Cap (mil)'].iloc[0])
          df.loc[len(df.index)] = temp_row1

    except IndexError as e:
      pass

  return df


#OBSOLETE
def scrape_earningswhispers_day(day, df_us_companies):
  url = "https://www.earningswhispers.com/calendar?sb=c&d=%s&t=all" % (day,)

  page = get_page_selenium(url)
  
  #soup = BeautifulSoup(page.content, 'html.parser')
  soup = BeautifulSoup(page, 'html.parser')

  date_str = soup.find('div', attrs={"id":"calbox"})
  date_str = date_str.text.strip().replace('for ','')

  eps_cal_table = soup.find('ul', attrs={"id":"epscalendar"})

  table_rows = eps_cal_table.find_all('li')

  df = pd.DataFrame()
  
  # Add Date, Time, CompanyName, Ticker headers to dataframe
  df.insert(0,"Date",[],True)
  df.insert(1,"Time",[],True)
  df.insert(2,"Ticker",[],True)
  df.insert(3,"Company Name",[],True)
  df.insert(4,"Market Cap (Mil)",[],True)

  skip_first = True

  for tr in table_rows:        
      temp_row = []

      td = tr.find_all('div')

      # Just Extract Date, Time, CompanyName, Ticker, EPS, Revenue, Expected Revenue
      for obs in td:  
          text = str(obs.text).strip()
          temp_row.append(text)    

      #import pdb; pdb.set_trace()
      time_str = temp_row[4]
      company_name_str = temp_row[2]
      ticker_str = temp_row[3]

      if(time_str.find(' ET') != -1):
          # Only if company exists on US stocks list, we add to df
          df_retrieved_company_data = df_us_companies.loc[df_us_companies['Ticker'] == ticker_str].reset_index(drop=True)
          if(df_retrieved_company_data.shape[0] > 0):
              temp_row1 = []
              temp_row1.append(date_str)
              temp_row1.append(time_str)
              temp_row1.append(ticker_str)
              temp_row1.append(company_name_str)

              # Get market cap from US Stocks list
              temp_row1.append(df_retrieved_company_data['Market Cap (mil)'].iloc[0])

              if not skip_first:   
                  df.loc[len(df.index)] = temp_row1

      skip_first = False

  return df

def set_marketscreener_economic_calendar(logger):

  logger.info("Getting Economic Calendar from Market Screener")

  url = "https://www.marketscreener.com/stock-exchange/calendar/economic/"

  page = get_page(url)
  soup = BeautifulSoup(page.content, 'html.parser')
  df = pd.DataFrame()

  tables = soup.find_all('table', recursive=True)

  try:
    table = tables[1]
  except IndexError as e:   
    table = tables[0]

  table_rows = table.find_all('tr')

  table_header = table_rows[0]
  td = table_header.find_all('th')
  index = 0

  for obs in td:        
      text = str(obs.text).strip()

      if(len(text)==0):
          text = "Date"
      df.insert(index,text,[],True)
      index+=1

  index = 0
  skip_first = True
  session = ""

  for tr in table_rows:        
      temp_row = []
      #import pdb; pdb.set_trace()
      td = tr.find_all('td')
      #class="card--shadowed"
      if not skip_first:
          td = tr.find_all('td')
          th = tr.find('th') #The time is stored as a th
          if(th):
              temp_row.append(th.text)        

          if(len(td) == 4):
              session = str(td[0].text).strip()

          for obs in td:  

              text = str(obs.text).strip()
              text = text.replace('\n','').replace('  ','')

              if(text == ''):
                  flag_class = obs.i.attrs['class'][2]
                  #Maybe this is the country field, which means that the country is represented by a flag image
                  if(flag_class == 'flag__us'):
                      text = "US"
                  elif(flag_class == 'flag__uk'): 
                      text = "UK"

                  elif(flag_class == 'flag__eu'): 
                      text = "European Union"

                  elif(flag_class == 'flag__de'): 
                      text = "Germany"

                  elif(flag_class == 'flag__jp'): 
                      text = "Japan"

                  elif(flag_class == 'flag__cn'): 
                      text = "China"
                  else:
                      text = "OTHER"
  
              temp_row.append(text)        


          pos1, pos2  = 1, 2

          if(len(temp_row) == len(df.columns)):
              temp_row = swapPositions(temp_row, pos1-1, pos2-1)
          else:
              temp_row.insert(0,session)
              #print(temp_row)
              #import pdb; pdb.set_trace()

          df.loc[len(df.index)] = temp_row
      else:
          skip_first = False

  #Remove Duplicates (Country, Events)
  df = df.drop_duplicates(subset=['Country', 'Events'])

  #Remove OTHER Countries
  df = df[df.Country != 'OTHER'].reset_index(drop=True)

  # Updated the date columns
  df['Date'] = df['Date'].apply(clean_dates)
  
  #Clear out old data
  sql_delete_all_rows('Macro_EconomicCalendar')

  #Write new data into table
  rename_cols = {'Date':'dt','Time':'dt_time','Country':'country','Events':'economic_event','Previous period':'previous'}
  add_col_values = None
  conflict_cols = None

  success = sql_write_df_to_db(df, "Macro_EconomicCalendar", rename_cols, add_col_values, conflict_cols)

  logger.info("Successfully Scraped Economic Calendar from Market Screener")

  return success

def set_whitehouse_news(logger):
  logger.info("Getting Whitehouse news")

  url = "https://www.whitehouse.gov/briefing-room/statements-releases/"
  page = get_page(url)
  soup = BeautifulSoup(page.content, 'html.parser')

  data = {'dt': [], 'post_title':[], 'post_url':[]}

  df = pd.DataFrame(data)

  articles = soup.find_all('article', recursive=True)

  for article in articles:
    temp_row = []

    # Extract Date, Title and Link and put them into a df
    article_title = article.find('a', attrs={'class':'news-item__title'})
    article_date = article.find('time', attrs={'class':'posted-on'})

    post_title = str(article_title.text).strip().replace('\xa0', ' ')
    post_date = article_date.text
    dt_date = pd.to_datetime(post_date,format='%B %d, %Y')
    post_url = article_title.attrs['href']

    temp_row.append(dt_date)
    temp_row.append(post_title)
    temp_row.append(post_url)

    if(len(temp_row) == len(df.columns)):
      df.loc[len(df.index)] = temp_row

  #Clear out old data
  sql_delete_all_rows('Macro_WhitehouseAnnouncement')

  #Write new data into table
  rename_cols = {'Date':'dt','Time':'dt_time','Country':'country','Events':'economic_event','Previous period':'previous'}
  add_col_values = None
  conflict_cols = None

  success = sql_write_df_to_db(df, "Macro_WhitehouseAnnouncement", rename_cols, add_col_values, conflict_cols)

  logger.info("Successfully Scraped Whitehouse news")

  return success

def set_geopolitical_calendar(logger):
  logger.info("Getting Geopolitical Calendar")

  url = "https://www.controlrisks.com/our-thinking/geopolitical-calendar"
  page = get_page(url)
  soup = BeautifulSoup(page.content, 'html.parser')
  df = pd.DataFrame()

  table = soup.find('table', recursive=True)

  table_rows = table.find_all('tr', recursive=True)

  table_rows_header = table.find_all('tr')[0].find_all('th')
  df = pd.DataFrame()

  index = 0

  for header in table_rows_header:
    df.insert(index,str(header.text).strip(),[],True)
    index+=1

  #Insert New Row. Format the data to show percentage as float
  for tr in table_rows:
    temp_row = []

    td = tr.find_all('td')
    for obs in td:
      text = str(obs.text).strip()
      temp_row.append(text)        

    if(len(temp_row) == len(df.columns)):
      df.loc[len(df.index)] = temp_row

  #Drop the last column because it is empty
  df = df.iloc[: , :-1]

  #Rename columns so that they match the database table
  df.rename(columns={ df.columns[0]: "event_date",df.columns[1]: "event_name",df.columns[2]: "event_location" }, inplace = True)

  #Clear out old data
  sql_delete_all_rows('Macro_GeopoliticalCalendar')

  #Write new data into table
  rename_cols = None
  add_col_values = None
  conflict_cols = None

  success = sql_write_df_to_db(df, "Macro_GeopoliticalCalendar", rename_cols, add_col_values, conflict_cols)

  logger.info("Successfully Scraped Geopolitical Calendar")

  return success

def set_price_action_ta(df_tickers, logger):
  is_success = False

  downloaded_data = download_yf_data_as_csv(df_tickers)
  success_yf_price_action = set_yf_price_action(df_tickers, logger)
  success_ta_patterns = set_ta_pattern_stocks(df_tickers, logger)

  if(downloaded_data & success_yf_price_action & success_ta_patterns):  
    is_success = True

  return is_success

def set_yf_price_action(df_tickers, logger):
  data = {'cid': [], 'last_volume':[], 'vs_avg_vol_10d':[], 'vs_avg_vol_3m':[], 'outlook':[], 'percentage_sold':[], 'last_close':[]}
  df_yf_price_action = pd.DataFrame(data)

  logger.info(f"Downloading price action from Yahoo Finance")

  for index, row in df_tickers.iterrows():
    ticker = row['symbol'] 
    # Get shares outstanding and make sure it is the full amount
    shares_outstanding = row['shares_outstanding'] 
    df = get_ticker_price_summary(ticker, shares_outstanding, logger)
    data = [df_yf_price_action, df]
    df_yf_price_action = pd.concat(data, ignore_index=True)
    logger.info(f"Successfully retrieved price action for: {ticker}")

  #Clear out old data
  sql_delete_all_rows('CompanyPriceAction')

  #Write new data into table
  rename_cols = None
  add_col_values = None
  conflict_cols = None
  
  success = sql_write_df_to_db(df_yf_price_action, "CompanyPriceAction", rename_cols, add_col_values, conflict_cols)

  logger.info(f"Successfully Scraped Price Action")

  return success

def get_ticker_price_summary(ticker, shares_outstanding, logger):
  df = pd.DataFrame()
  data = {'cid': [], 'last_volume':[], 'vs_avg_vol_10d':[], 'vs_avg_vol_3m':[], 'outlook':[], 'percentage_sold':[], 'last_close':[]}
  df_price_action_summary = pd.DataFrame(data)
  
  temp_row = []

  filename = "{}.csv".format(ticker)
  
  logger.info(f"Getting data from {ticker} file")
  try:
    df = pd.read_csv('data/daily_prices/{}'.format(filename))
    df['Date'] = pd.to_datetime(df['Date'],format='%Y-%m-%d')

    df_10d = df.tail(10)
    df_3m = df.tail(30)

    avg_vol_10d = df_10d['Volume'].mean()
    avg_vol_3m = df_3m['Volume'].mean()
    last_volume = df.tail(1)['Volume'].values[0]

    prev_close = df[-2:-1]['Adj Close'].values[0]
    last_close = df[-1:]['Adj Close'].values[0]
    #import pdb; pdb.set_trace()
    #if(ticker == 'DLO'):
    #  import pdb; pdb.set_trace()

    #Create calculated metrics
    if(math.isnan(shares_outstanding) == False):
      if(last_volume > 0 and shares_outstanding > 0):
          percentage = last_volume/shares_outstanding
          percentage = "{:.4f}".format(percentage)
      else:
          percentage = 0
    else:
      percentage = 0

    if(last_volume > 0 and avg_vol_10d > 0):
        vs_avg_vol_10d = last_volume/avg_vol_10d
    else:
        vs_avg_vol_10d = 0

    if(last_volume > 0 and avg_vol_3m > 0):
        vs_avg_vol_3m = last_volume/avg_vol_3m
    else:
        vs_avg_vol_3m = 0

    if(last_close > prev_close):
        outlook = 'bullish'
    else:
        outlook = 'bearish'

    #Write the following into the database

    cid = sql_get_cid(ticker)
    if(cid):
      logger.info(f"Retrieved {cid} for {ticker}")
      temp_row.append(str(cid))
      temp_row.append(last_volume)
      temp_row.append(vs_avg_vol_10d)
      temp_row.append(vs_avg_vol_3m)
      temp_row.append(outlook)
      temp_row.append(percentage)
      temp_row.append(last_close)

      df_price_action_summary.loc[len(df_price_action_summary.index)] = temp_row
  except IndexError as e:
     logger.exception(f"Indexerror for {ticker}")

  return df_price_action_summary

def set_ta_pattern_stocks(df_tickers, logger):
  #data =  {'symbol': [],'company': [], 'sector': [], 'industry': [] , 'last': []}
  data = {'ticker': [], 'pattern': []}
  df_consolidating = pd.DataFrame(data)
  df_breakout = pd.DataFrame(data)
  df_sma_breakout = pd.DataFrame(data)

  for index, row in df_tickers.iterrows():
      filename = "{}.csv".format(row['symbol'])

      df = pd.read_csv('data/daily_prices/{}'.format(filename))
      symbol = row['symbol']
      if(row['exchange'] in ['NYSE','NSDQ']):
        #Some industries are investment funds rather than companies. We want to exclude them.
        if(row['industry'] not in config.EXCLUDED_INDUSTRIES_TA): 
          #TODO: CALCULATE TA PATTERNS BASED ON ADAM KHOO RECOMMENDATIONS. IE. USING SMA50, SMA150 ETC.
          #print("Ticker: %s" % (symbol,))
          df_intersections, bool_is_breaking_sma_50_150_last_14_days = is_breaking_sma(df,50,150,14)

          if bool_is_breaking_sma_50_150_last_14_days:
            df_sma_breakout.loc[len(df_sma_breakout.index)] = [symbol, 'sma_breakout_50_150_14']

          if is_consolidating(df, percentage=2.5):
              df_consolidating.loc[len(df_consolidating.index)] = [symbol, 'consolidating']

          if is_breaking_out(df):
              df_breakout.loc[len(df_breakout.index)] = [symbol, 'breakout']

  data = [df_consolidating, df_breakout, df_sma_breakout]
  df_patterns = pd.concat(data, ignore_index=True)

  #Clear out old data
  sql_delete_all_rows("TA_Patterns")

  #Write new data into table
  rename_cols = None
  add_col_values = None
  conflict_cols = None

  success = sql_write_df_to_db(df_patterns, "TA_Patterns", rename_cols, add_col_values, conflict_cols)

  logger.info("Successfully Scraped TA Patterns")

  return success

def is_breaking_sma(df, lower, upper,last_x_days):

  # Calculate the 50-day simple moving average
  sma_lower = df['Close'].rolling(lower).mean()
  suffix_lower = '_sma%s' % (lower)
  # Print the DataFrame containing the closing prices and the SMA50
  df = df.join(sma_lower, rsuffix=suffix_lower)

  # Calculate the 150-day simple moving average
  sma_upper = df['Close'].rolling(upper).mean()
  suffix_upper = '_sma%s' % (upper)
  # Print the DataFrame containing the closing prices and the SMA150
  df = df.join(sma_upper, rsuffix=suffix_upper)
  df['Date'] = df['Date'].str.replace("-","").astype(int)

  col_lower = 'Close%s' % (suffix_lower)
  col_upper = 'Close%s' % (suffix_upper)

  df_intersections = calc_intersections_date(df['Date'].ravel(),df[col_lower].ravel(),df[col_upper].ravel())

  # Get current date and put it tinto a df
  data = {'dt': []}
  df_current_date = pd.DataFrame(data)
  current_date_str = dt.now().strftime('%Y-%m-%d')  
  temp_row1 = []
  temp_row1.append(current_date_str)
  df_current_date.loc[len(df_current_date.index)] = temp_row1
  df_current_date['dt'] = pd.to_datetime(df_current_date['dt'],format='%Y-%m-%d')
  temp_days = df_current_date['dt'] - df_intersections.tail(1).reset_index(drop=True)['x']
  str_days = temp_days.to_string()

  # Extract days and see if it is less than a week. If less than a week, return TRUE
  # Process df and return TRUE where appropriate (ie. 50-150 crossover happened in the last week)

  pattern_select = re.compile(r'([^0\s]+[0-9]+)')
  matches = pattern_select.findall(str_days)

  try:
    days = int(matches[0])
  except(ValueError, IndexError) as e:
    days = 1000

  if(days <= last_x_days):
    return df_intersections.tail(1).reset_index(drop=True), True
  else:
    return df_intersections.tail(1).reset_index(drop=True), False

def calc_intersections_date(x, y1, y2):

  xi_all, yi_all = mpcalc.find_intersections(x,y1,y2)

  xi_list = xi_all.to_tuple()[0].tolist()
  yi_list = yi_all.to_tuple()[0].tolist()

  #clean the lists to remove nan values
  xi_list = [x for x in xi_list if str(x) != 'nan']
  yi_list = [x for x in yi_list if str(x) != 'nan']

  # xi_list contains a date. Need to convert it into a date
  for i in range(len(xi_list)):
    date_str = str(xi_list[i]).split('.')[0]
    try:
      xi_list[i] = dt.strptime(date_str, '%Y%m%d').date()  
    except ValueError as e:
      xi_list[i] = dt.strptime('19000101', '%Y%m%d').date()  
    
  #create a df containing the date, and the value of the intersection 
  df_intersections = pd.DataFrame({"x": [],"y": []})
  df_intersections['x'] = xi_list
  df_intersections['y'] = yi_list
  try:
    df_intersections['x'] = pd.to_datetime(df_intersections['x'],format='%Y-%m-%d')
  except ValueError as e:
    pass

  # Order by Date DESC
  df_intersections.sort_values(by='x', inplace = True)

  return df_intersections

def is_consolidating(df, percentage=2):
  try:
    recent_candlesticks = df[-15:]

    max_close = recent_candlesticks['Close'].max()
    min_close = recent_candlesticks['Close'].min()

    threshold = 1 - (percentage / 100)
    if min_close > (max_close * threshold):
        return True        
  except IndexError as e:
     pass

  return False

def is_breaking_out(df, percentage=2.5):
  try:
    last_close = df[-1:]['Close'].values[0]

    if is_consolidating(df[:-1], percentage=percentage):
        recent_closes = df[-16:-1]

        if last_close > recent_closes['Close'].max():
            return True
  except IndexError as e:
     pass

  return False

############
#  GETTERS #
############

def get_api_json_data(url, filename):

    #check if current file has todays system date, and if it does load from current file. Otherwise, continue to call the api
    file_path = "%s/JSON/%s" % (sys.path[0],filename)
    data_list = []

    todays_date = date.today()
    try:
      file_mod_date = time.ctime(os.path.getmtime(file_path))
      file_mod_date = dt.strptime(file_mod_date, '%a %b %d %H:%M:%S %Y')
    except FileNotFoundError as e:
      #Set file mod date to nothing as we do not have a file
      file_mod_date = None

    try:
        #Check if file date is today. If so, continue. Otherwise, throw exception so that we can use the API instead to load the data
        if(file_mod_date.date() == todays_date):
            my_file = open(file_path, "r")        
        else:
            # Throw exception so that we can read the data from api
            raise Exception('Need to read from API') 
    except Exception as error:
        temp_data = []
        temp_data.append(requests.get(url).json())

        # Write response to File
        with open(file_path, 'w') as f:
            for item in temp_data:
                f.write("%s\n" % item)

        # try to open the file in read mode again
        my_file = open(file_path, "r")        

    data = my_file.read()
    
    # replacing end splitting the text 
    # when newline ('\n') is seen.
    liststr = data.split("\n")
    my_file.close()

    data_list = eval(liststr[0])

    return data_list

def get_api_json_data_no_file(url):

    data_list = []

    data_list.append(requests.get(url).json())

    return data_list

def get_zacks_us_companies():
  list_of_files = glob.glob('data/zacks_custom_screen_*.csv',) # * means all if need specific format then *.csv
  latest_zacks_file = max(list_of_files, key=os.path.getctime)
  latest_zacks_file = latest_zacks_file.replace("data\\", "")
  temp_excel_file_path = '/data/{}'.format(latest_zacks_file)

  #Get company data from various sources
  df_us_companies = convert_csv_to_dataframe(temp_excel_file_path)

  #Need to multiply outstanding_shares by 1mill because it is in 1mill units
  df_us_companies['shares_outstanding'] = df_us_companies['Shares Outstanding (mil)'] * 1000000

  return df_us_companies

def get_one_pager(ticker):

  #Initialize dataframes
  df_zacks_balance_sheet_shares = pd.DataFrame()
  df_zacks_earnings_surprises = pd.DataFrame()
  df_zacks_product_line_geography = pd.DataFrame()
  df_stockrow_stock_data = pd.DataFrame()
  df_yf_key_stats = pd.DataFrame()
  df_zacks_peer_comparison = pd.DataFrame()
  df_finwiz_stock_data = pd.DataFrame()
  df_dcf_valuation = pd.DataFrame()

  # get ticker cid
  cid = sql_get_cid(ticker)

  if(cid):
    # Query database tables and retrieve all data for the ticker
    df_company_details = get_data(table="company", cid=cid)
    df_zacks_balance_sheet_shares = get_data(table="balancesheet",cid=cid)
    df_zacks_earnings_surprises = get_data(table="earningssurprise",cid=cid)
    df_zacks_product_line_geography = get_data(table="companygeography",cid=cid)
    df_stockrow_stock_data = get_data(table="companyforecast",cid=cid)
    df_yf_key_stats = get_data(table="companymovingaverage",cid=cid)
    df_zacks_peer_comparison = get_data(table="companypeercomparison",cid=cid)
    df_finwiz_stock_data = get_data(table="companyratio",cid=cid)
    df_dcf_valuation = get_data(table="companystockvaluedcf",cid=cid)

  return df_company_details, df_zacks_balance_sheet_shares, df_zacks_earnings_surprises, df_zacks_product_line_geography, df_stockrow_stock_data, df_yf_key_stats, df_zacks_peer_comparison, df_finwiz_stock_data,df_dcf_valuation

def get_data(table=None, cid=None, innerjoin=None):
  df = sql_get_records_as_df(table, cid, innerjoin)
  return df

def set_summary_ratios(df_tickers, logger):
  success = False

  # Load exclusion list
  csv_file_path = '/data/finwiz_exclusion_list.csv'
  df_exclusion_list = convert_csv_to_dataframe(csv_file_path)

  #data = {'Ticker': [],'Market Cap':[],'EV':[],'PE':[],'EV/EBITDA':[],'EV/EBIT':[],'EV/Revenue':[],'EBIT/Margin':[],'ROE':[],'PB':[]}
  data = {'ev_ebitda':[],'ev_ebit':[],'ev_revenue':[],'ebit_margin':[]}

  df_summary_ratios = pd.DataFrame(data)

  for index, row in df_tickers.iterrows():
    temp_row = []
    ticker = row['Ticker']  
    #cid = sql_get_cid(ticker)    
    #print(cid)
    #print(ticker)
    if(df_exclusion_list['Ticker'].str.contains(ticker).any() == False):   

      json_module_profile, json_module_quote, json_module_balance_sheet, json_module_key_metrics, json_module_company_outlook, json_module_price_target_summary,json_module_key_metrics_ttm,json_module_company_core_information, json_module_company_income_statement, error = get_financialmodelingprep_price_action(ticker,logger)

      #df_moving_average = get_data(table="CompanyMovingAverage", cid=cid)
      #df_company_ratio = get_data(table="CompanyRatio", cid=cid)
      #try:
      #  pb = df_company_ratio['price_book'][0]
      #except (KeyError,TypeError) as e:
      #  pb = None
      #try:
      #  roe = df_company_ratio['roe'][0]
      #except (KeyError,TypeError) as e:
      #  roe = None
      #try:
      #  market_cap = df_moving_average['market_cap'][0]
      #except (KeyError,TypeError) as e:
      #  market_cap = None
      #try:
      #  ev = df_moving_average['ev'][0]
      #except (KeyError,TypeError) as e:
      #  ev = None

      try:
        pe = json_module_key_metrics_ttm[0]['peRatioTTM']
        pe ='{:,.2f}'.format(pe) 
      except (IndexError, KeyError,TypeError) as e:
        pe = None

      try:
        ev_ebitda = json_module_key_metrics[0]['enterpriseValueOverEBITDA']
        ev_ebitda ='{:,.2f}'.format(ev_ebitda) 
      except (IndexError, KeyError,TypeError, UnboundLocalError) as e:
        ev_ebitda = None

      # Get EV.
      try:
        ev_unformatted = json_module_key_metrics[0]['enterpriseValue']
      except (IndexError, KeyError,TypeError, UnboundLocalError) as e:
        ev_unformatted = None

      # Get Revenue
      try:
        revenue = json_module_company_income_statement[0]['revenue']
      except (IndexError, KeyError,TypeError, UnboundLocalError) as e:
        revenue = None

      # Calculate Ebit using latest Ebitda and D&A
      try:
        ebitda = json_module_company_income_statement[0]['ebitda']
      except (IndexError, KeyError,TypeError, UnboundLocalError) as e:
        ebitda = None

      try:
        depreciation_and_amortization = json_module_company_income_statement[0]['depreciationAndAmortization']
      except (IndexError, KeyError,TypeError, UnboundLocalError) as e:
        depreciation_and_amortization = None

      try:
        ebit = ebitda - depreciation_and_amortization
      except (KeyError,TypeError, UnboundLocalError, ZeroDivisionError) as e:
        ebit = None

      try:
        #ev_revenue = dataDefaultKeyStatistics['enterpriseToRevenue']['fmt']
        ev_revenue = ev_unformatted/revenue 
        ev_revenue ='{:,.2f}'.format(ev_revenue) 
      except (KeyError,TypeError, UnboundLocalError, ZeroDivisionError) as e:
        ev_revenue = None

      try:
        ev_ebit = ev_unformatted/ebit
        ev_ebit ='{:,.2f}'.format(ev_ebit) 
      except (KeyError,TypeError, UnboundLocalError, ZeroDivisionError) as e:
        ev_ebit = None

      try:
        ebit_margin = (ebit/revenue) * 100
        ebit_margin ='{:,.2f}'.format(ebit_margin)      
      except (KeyError,TypeError, UnboundLocalError, ZeroDivisionError) as e:
        ebit_margin = None

      #temp_row.append(ticker)
      #temp_row.append(market_cap)
      #temp_row.append(ev)
      #temp_row.append(pe) 
      temp_row.append(ev_ebitda) 
      temp_row.append(ev_ebit) 
      temp_row.append(ev_revenue) 
      temp_row.append(ebit_margin)
      #temp_row.append(roe) 
      #temp_row.append(pb)

      df_summary_ratios.loc[len(df_summary_ratios.index)] = temp_row

      # get ticker cid
      cid = sql_get_cid(ticker)
      if(cid):
        # write records to database
        rename_cols = {}
        add_col_values = {"cid": cid}
        conflict_cols = "cid"

        success = sql_write_df_to_db(df_summary_ratios, "CompanyRatio", rename_cols, add_col_values, conflict_cols)
        logger.info(f'Successfully Saved Additional Summary Ratios from TMP for {ticker}')     

#  df_competitor_metrics = df_competitor_metrics.T
#  new_header = df_competitor_metrics.iloc[0] #grab the first row for the header
#  df_competitor_metrics = df_competitor_metrics[1:] #take the data less the header row

#  df_competitor_metrics.columns = new_header #set the header row as the df header

#  return df_competitor_metrics
  return success

def get_summary_ratios(df_tickers):
  data = {'Ticker': [],'Market Cap':[],'EV':[],'PE':[],'EV/EBITDA':[],'EV/EBIT':[],'EV/Revenue':[],'EBIT/Margin':[],'ROE':[],'PB':[]}
  df_summary_ratios = pd.DataFrame(data)

  for index, row in df_tickers.iterrows():
    temp_row = []
    ticker = row['Ticker']  
    cid = sql_get_cid(ticker)

    df_moving_average = get_data(table="CompanyMovingAverage", cid=cid)
    df_company_ratio = get_data(table="CompanyRatio", cid=cid)

    try:
      market_cap = df_moving_average['market_cap'][0]
    except (KeyError,TypeError) as e:
      market_cap = None

    try:
      ev = df_moving_average['ev'][0]
    except (KeyError,TypeError) as e:
      ev = None

    try:
      pe = df_company_ratio['pe'][0]
    except (KeyError,TypeError) as e:
      pe = None

    try:
      ev_ebitda = df_company_ratio['ev_ebitda'][0]
    except (KeyError,TypeError) as e:
      ev_ebitda = None

    try:
      ev_ebit = df_company_ratio['ev_ebit'][0]
    except (KeyError,TypeError) as e:
      ev_ebit = None

    try:
      ev_revenue = df_company_ratio['ev_revenue'][0]
    except (KeyError,TypeError) as e:
      ev_revenue = None

    try:
      ebit_margin = df_company_ratio['ebit_margin'][0]
    except (KeyError,TypeError) as e:
      ebit_margin = None

    try:
      pb = df_company_ratio['price_book'][0]
    except (KeyError,TypeError) as e:
      pb = None

    try:
      roe = df_company_ratio['roe'][0]
    except (KeyError,TypeError) as e:
      roe = None

    temp_row.append(ticker)
    temp_row.append(market_cap)
    temp_row.append(ev)
    temp_row.append(pe) 
    temp_row.append(ev_ebitda) 
    temp_row.append(ev_ebit) 
    temp_row.append(ev_revenue) 
    temp_row.append(ebit_margin)
    temp_row.append(roe) 
    temp_row.append(pb)

    df_summary_ratios.loc[len(df_summary_ratios.index)] = temp_row

  return df_summary_ratios

def get_stlouisfed_data(series, period, num_years):

  df = get_data(table="macro_stlouisfed")
  df['series_date'] = pd.to_datetime(df['series_date'],format='%Y-%m-%d')
  df = df.rename(columns={"series_date":"DATE"})  
  df[series] = pd.to_numeric(df[series])
  df_all = df[['DATE',series]][df[series] > 0].sort_values(by=['DATE']).reset_index(drop=True)

  # Calculate additional metrics
  #YoY, QoQ, QoQ_Annualized
  if(period == 'Q'):
    df_all['QoQ'] = (df_all[series] - df_all[series].shift()) / df_all[series].shift()
    df_all['YoY'] = (df_all[series] - df_all[series].shift(periods=4)) / df_all[series].shift(periods=4)
    df_all['QoQ_ANNUALIZED'] = ((1 + df_all['QoQ']) ** 4) - 1

  elif(period=='M'):
    df_all['MoM'] = (df_all[series] - df_all[series].shift()) / df_all[series].shift()
    df_all['QoQ'] = (df_all[series] - df_all[series].shift(periods=4)) / df_all[series].shift(periods=4)
    df_all['YoY'] = (df_all[series] - df_all[series].shift(periods=12)) / df_all[series].shift(periods=12)
    df_all['QoQ_ANNUALIZED'] = ((1 + df_all['QoQ']) ** 12) - 1

  # Get the most recent data (ie. last 5 years)
  todays_date = date.today()
  start_date = todays_date - relativedelta(years=num_years)
  date_str_start = "%s-%s-%s" % (start_date.year, start_date.month, start_date.day)

  df_recent = df_all.loc[(df_all['DATE'] >= date_str_start)].reset_index(drop=True)            

  return df_all, df_recent


####################
# Output Functions #
####################

def convert_csv_to_dataframe(excel_file_path):

  if(isWindows):
    filepath = os.getcwd()
    excel_file_path = filepath + excel_file_path.replace("/","\\")

  else:
    filepath = os.path.realpath(__file__)
    excel_file_path = filepath[:filepath.rfind('/')] + excel_file_path

  df = pd.read_csv(excel_file_path)

  return df


def style_df_for_display_date(df, cols_gradient, cols_rename, cols_drop, cols_format=None):

  df = df.drop(cols_drop, axis=1)
  #if(format_date):
  #   df['DATE'] = df['DATE'].dt.strftime('%m/%d/%Y')
  #import pdb; pdb.set_trace()
  df = df.sort_values(by=['DATE'], ascending=False)
  df = df.rename(columns=cols_rename)
  #df = df.set_index(df.columns[0])
  #table_styles = [{'selector': 'tr:hover',
  #    'props': 'background-color: yellow; font-size: 1em;'}]
  #cmap = plt.cm.get_cmap('YIOrRd')

  df_style = df.style.background_gradient(cmap='Oranges',subset=cols_gradient).format(cols_format).hide(axis=0)
  #import pdb; pdb.set_trace()
  #import pdb; pdb.set_trace()
  #df = df.to_html()
  #df = df.hide(axis=0)
  #df = df.set_table_styles(table_styles)
  #df.hide_columns_ = True 
  return df_style,df

def format_bullish_bearish(row):    

    bearish = 'background-color: lightcoral;'
    bullish = 'background-color: mediumseagreen;'

    # must return one string per cell in this row
    if row[row.index[0]] == 'bullish':
        return [bullish]
    else:
        return [bearish]

def format_earnings_surprises(row):    

    negative = 'background-color: lightcoral;'
    positive = 'background-color: mediumseagreen;'
    normal = ''

    if(row[row.index[1]] > row[row.index[0]]):
      return [normal, positive]
    else:
      return [normal, negative]

def format_positive_negative(row):    
    #import pdb; pdb.set_trace()
    negative = 'background-color: lightcoral;'
    positive = 'background-color: mediumseagreen;'
    normal = ''
    ##import pdb; pdb.set_trace()
    if(row[0] > 0):
      return [positive]
    else:
      return [negative]


def style_df_for_display(df, cols_gradient, cols_rename, cols_drop, cols_format=None,format_rows=False):

  df = df.drop(cols_drop, axis=1)
  df = df.rename(columns=cols_rename)

  if(format_rows):
    df_style = df.style.background_gradient(cmap='Oranges',axis=1).format(cols_format).hide(axis=0)
  else:
    df_style = df.style.background_gradient(cmap='Oranges',subset=cols_gradient).format(cols_format).hide(axis=0)

  #df_style = df_style.apply(format_bullish_bearish, subset=['Outlook'], axis=1)

  return df_style, df

def format_fields_for_dashboard(col_names, data):
  index = 0

  dict = {}
  for x in col_names:
    dict[x] = [data[index]]
    index = index + 1

  df_table = pd.DataFrame(dict)
  df_table = df_table.T
  df_table = df_table.reset_index()
  style = df_table.style.hide_index()

  return style

def format_df_for_dashboard_flip(df, sort_cols, drop_rows, rename_cols, number_format_col, date_format_col=None, percentage_format_col=None):

  #cols to format
  try:
    arr_number_format_cols = df[number_format_col].squeeze().tolist()
  except KeyError as e:
    pass

  #Sorting
  try:
    df = df.sort_values(by=sort_cols, ascending=True)
  except KeyError as e:
    pass

  #Dropping Rows
  try:
    df = df.drop(drop_rows, axis=1)
  except KeyError as e:
    pass

  #Renaming Indexes
  df.rename(columns=rename_cols, inplace=True)
  try:
    df = df.set_index(df.columns[0],drop=True)
  except IndexError as e:
    pass

  df = df.T

  #Formatting Columns
  if(len(df.columns) > 0):

    for x in arr_number_format_cols:
      # Format Numbers
      try:
        df[x] = df[x].astype(float)
        df[x] = df[x].map('{:,.2f}'.format)
      except KeyError as e:
        pass

    style = df.style.hide_index()
  else:
    style = None

  return style

def format_df_for_dashboard(df, sort_cols, drop_cols, rename_cols, format_cols=None, order_cols=None):
  #Sorting
  try:
    df = df.sort_values(by=sort_cols, ascending=True)
  except KeyError as e:
    print(f"Error Sorting Columns: {e}")
    pass
  
  #Dropping Columns
  try:
    df = df.drop(drop_cols, axis=1)
  except KeyError as e:
    print(f"Error Dropping Columns: {e}")
    pass

  #Formatting Columns
  if(format_cols):
    for key in format_cols:
      x = key
      data_type = format_cols[key]
      if(data_type == 'number'):
        try:
          df[x] = df[x].astype(float)
          df[x] = df[x].map('{:,.2f}'.format)
        except KeyError as e:
          print(f"Error Formatting Columns: {e}")
          pass

      elif(data_type == 'date'):
        try:
          df[x] = df[x].dt.strftime('%d-%m-%Y')
        except KeyError as e:
          pass

      elif(data_type == 'percentage'):
        try:
          df[x] = df[x].astype(float)
          df[x] = df[x] * 100
          df[x] = df[x].map('{:,.2f}%'.format)
        except KeyError as e:
          pass

  if(order_cols):
    # Sort by putting symbol1 first and symbol2 second. 
    df = df.loc[:, order_cols]

  #Renaming Indexes
  df.rename(columns=rename_cols, inplace=True)

  try:
    df = df.set_index(df.columns[0],drop=True)
  except IndexError as e:
    print(f"Error Dropping Index: {e}")
    pass

  #if(gradient_cols):
  #  df = df.style.background_gradient(cmap='Blues',subset=gradient_cols)

  return df

def format_outlook(styler):
  styler.highlight_max(subset=['Outlook'], color='yellow')
  return styler

def format_columns(df, gradient_cols):
  styler = df.style.background_gradient(cmap='Blues',subset=gradient_cols)
  return styler
   

####################
# Helper Functions #
####################

def download_yf_data_as_csv(df_tickers):
  todays_date = date.today()
  start_date = todays_date - relativedelta(years=5)
  date_str_today = "%s-%s-%s" % (todays_date.year, todays_date.month, todays_date.day)
  date_str_start = "%s-%s-%s" % (start_date.year, start_date.month, start_date.day)

  for index, row in df_tickers.iterrows():
    ticker = row['symbol'] 
    data = yf.download(ticker, start=date_str_start, end=date_str_today)
    data.to_csv('data/daily_prices/{}.csv'.format(ticker))

  return True


def combine_df(df_original, df_new):

  return df_original.combine(df_new, take_larger, overwrite=False)  

def append_two_df(df1, df2, how='outer'):
  merged_data = pd.merge(df1, df2, how=how, on='DATE')
  return merged_data

def take_larger(s1, s2):
  return s2

def combine_df_on_index(df1, df2, index_col):
  df1 = df1.set_index(index_col)
  df2 = df2.set_index(index_col)

  return df2.combine_first(df1).reset_index()

def convert_html_table_to_df(table, contains_th):
  df = pd.DataFrame()

  try:
    table_rows = table.find_all('tr')
    table_rows_header = table.find_all('tr')[0].find_all('th')
  except AttributeError as e:
    return df
  
  index = 0

  for header in table_rows_header:
    df.insert(index,str(header.text).strip(),[],True)
    index+=1

  #Insert New Row. Format the data to show percentage as float
  for tr in table_rows:
    temp_row = []

    if(contains_th):
      tr_th = tr.find('th')
      text = str(tr_th.text).strip()
      temp_row.append(text)        

    td = tr.find_all('td')
    for obs in td:
      
      exclude = False

      if(obs.find_all('div')):
        if 'hidden' in obs.find_all('div')[0].attrs['class']:
          exclude = True

      if not exclude:
        text = str(obs.text).strip()
        temp_row.append(text)        

    if(len(temp_row) == len(df.columns)):
      df.loc[len(df.index)] = temp_row
  
  return df

def convert_list_to_df(list):

  df = pd.DataFrame(list)

  return df

def _util_check_diff_list(li1, li2):
  # Python code to get difference of two lists
  return list(set(li1) - set(li2))

def dataframe_convert_to_numeric(df, column, logger):

  #TODO: Deal with percentages and negative values in brackets
  try:
    contains_mill = False
    contains_thousands = False
    contains_percentage = False

    #TODO: what if number contains a k. We are reporting in billions so we need to deal with the "k". For example, NXE
    if(df[column].str.contains('k',regex=False).sum() > 0):
      contains_thousands = True
      df[column] = df[column].str.replace('k','')

    if(df[column].str.contains('m',regex=False).sum() > 0):
      contains_mill = True
      df[column] = df[column].str.replace('m','')

    if(df[column].str.contains('%',regex=False).sum() > 0):
      contains_percentage = True
      df[column] = df[column].str.replace('%','')

    #contains a billion. Because we are reporting in billions, simply remove the "b"
    if(df[column].str.contains('b',regex=False).sum() > 0):
      df[column] = df[column].str.replace('b','')

    df[column] = df[column].str.replace('N/A','')
    df[column] = df[column].str.replace('NA','')
    df[column] = df[column].str.replace('$','', regex=False)
    df[column] = df[column].str.replace('--','')
    df[column] = df[column].str.replace(',','').replace('–','0.00').replace("-",'0.00')
    df[column] = df[column].str.replace('(','-', regex=True)
    df[column] = df[column].str.replace(')','', regex=True)
    df[column] = df[column].str.replace('+','', regex=True)
    df[column] = df[column].str.replace('>','', regex=True)

  except KeyError as e:
    logger.exception(df)
    logger.exception(column)

  df[column] = pd.to_numeric(df[column])

  if(contains_thousands):
    df[column] = df[column]/1000000000

  if(contains_mill):
    df[column] = df[column]/1000000

  if(contains_percentage):
    df[column] = df[column]/100

  return df

def transpose_df(df):
  df = df.T
  new_header = df.iloc[0] #grab the first row for the header
  df = df[1:] #take the data less the header row
  df.columns = new_header #set the header row as the df header

  return df
  
def handle_exceptions_print_result(future, executor_num, process_num, logger):
  exception = future.exception()
  if exception:
    logger.error(f'EXCEPTION of Executor {executor_num} Process {process_num}: {exception}')
    #st.write(f'EXCEPTION of Executor {executor_num} Process {process_num}: {exception}')
    return 1
  
  else:
    logger.info(f'Status of Executor {executor_num} Process {process_num}: {future.result()}')
    #st.write(f'Status of Executor {executor_num} Process {process_num}: {future.result()}')
    return 0

"""
def display_execution_results(executor_count, range_tuple, logger):
  data = {'Executor':[],'Process':[],'Result':[]}
  df_result = pd.DataFrame(data)
  executor_count = executor_count
  
  for x in range_tuple:
      result = handle_exceptions_print_result(eval('e{0}p{1}'.format(int(executor_count), int(x))),int(executor_count), int(x), logger)
      temp_row = [executor_count,x,result]
      df_result.loc[len(df_result.index)] = temp_row

  rename_cols = {}
  cols_gradient = ['Result']
  cols_drop = []

  disp = style_df_for_display(df_result,cols_gradient,rename_cols,cols_drop)   

  return disp
"""

# Function to clean the names
def clean_dates(date_name):
    pattern_regex = re.compile(r'^(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)')
    day_of_week = re.search(pattern_regex,date_name).group(0)

    pattern_regex = re.compile(r'[0-9][0-9]')
    day_of_month = re.search(pattern_regex,date_name).group(0)

    pattern_regex = re.compile(r'(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)')
    month_of_year = re.search(pattern_regex,date_name).group(0)

    formatted_date_string = "%s %s %s" % (day_of_week, day_of_month, month_of_year)

    todays_date = date.today()
    todays_date_year = todays_date.year
    formatted_date_string_new = "%s %s" % (formatted_date_string, todays_date_year)
    dt_date = pd.to_datetime(formatted_date_string_new,format='%A %d %B %Y')
    
    # Check if date is in the past. If the date is in the past, change the year to next year
    if(dt_date.to_pydatetime().date() < todays_date):
      todays_date_year += 1
      formatted_date_string_new = "%s %s" % (formatted_date_string, todays_date_year)
      dt_date = pd.to_datetime(formatted_date_string_new,format='%A %d %B %Y')

    #return formatted_date_string
    return dt_date

# Swap function
def swapPositions(list, pos1, pos2):
     
    list[pos1], list[pos2] = list[pos2], list[pos1]
    return list

######################
# Database Functions #
######################

def sql_get_cid(ticker):

  connection, cursor = sql_open_db()

  sqlCmd = """SELECT cid FROM company WHERE symbol='{}'""".format(sql_escape_str(ticker))
  cursor.execute(sqlCmd)
  try:
    cid = cursor.fetchone()[0]
  except TypeError as e:
    cid = None

  success = sql_close_db(connection, cursor)

  return cid

def sql_get_cid(ticker):

  connection, cursor = sql_open_db()

  sqlCmd = """SELECT cid FROM company WHERE symbol='{}'""".format(sql_escape_str(ticker))
  cursor.execute(sqlCmd)
  try:
    cid = cursor.fetchone()[0]
  except TypeError as e:
    cid = None

  success = sql_close_db(connection, cursor)

  return cid


def sql_write_df_to_db(df, db_table, rename_cols=None, additional_col_values=None, conflict_cols=None):

  connection, cursor = sql_open_db()
  if(rename_cols):
    # rename cols based on rename_cols
    df = df.rename(columns=rename_cols)

  for index, row in df.iterrows():
    str1, str2, str3 = "", "", ""

    for name, value in row.items():
      str1 += f'{name},'
      str2 += sql_format_str(value)
      str3 += f'{name}=excluded.{name},'

    #add additional col values based on additional_col_values variable
    if(additional_col_values):
      for key in additional_col_values:
        str1 += f'{key},'
        str2 += sql_format_str(additional_col_values[key])

    #Remove last comma from both str1 and str2
    str1 = str1.rstrip(',')
    str2 = str2.rstrip(',')
    str3 = str3.rstrip(',')
    if(conflict_cols):
      sqlCmd = """INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO UPDATE SET {};
      """.format(db_table, str1, str2, conflict_cols, str3)
    else:
      sqlCmd = """INSERT INTO {} ({}) VALUES ({});
      """.format(db_table, str1, str2, str3)

    cursor.execute(sqlCmd)
    connection.commit()

  success = sql_close_db(connection, cursor)

  return success

def sql_escape_str(escape_str):
  try:
    escape_str = escape_str.replace("'", "''")
  except AttributeError as e:
    escape_str = str(escape_str)
    #logger.exception(f"Error: {e}")
  return escape_str

def sql_format_str(value):
  if(pd.isnull(value)):
      return f'\'0.0\',' 
  elif(isinstance(value, dt)):
    #TODO: Need to convert python datetime into postgresql datetime and append it to str2
    # yyyy-mm-dd
    value = value.strftime('%Y-%m-%d')
    return f'\'{value}\','
  elif(isinstance(value, (int, float))):
    if(math.isnan(value)):
      return f'\'0.0\',' 
    else:
      return f'\'{value}\','
  else:
    return f'\'{sql_escape_str(value)}\','

def sql_get_volume():

  connection, cursor = sql_open_db()

  # Exclude Managed Funds and ETFs
  sqlCmd = """SELECT companypriceaction.*, company.symbol, company.company_name, company.sector, company.industry FROM companypriceaction INNER JOIN company ON companypriceaction.cid=company.cid WHERE company.exchange IN ('NYSE','NSDQ') AND company.industry NOT IN ('Financial - Investment Funds')"""

  cursor.execute(sqlCmd)

  df = return_df_from_sql(connection, cursor)

  return df

def sql_get_records_as_df(table, cid, innerjoin):
  #df = pd.DataFrame()
    
  connection, cursor = sql_open_db()
  if(cid):
    sqlCmd = """SELECT * FROM {} WHERE cid={}""".format(table, cid)
  else:
    sqlCmd = """SELECT * FROM {}""".format(table)
     
  cursor.execute(sqlCmd)

  df = return_df_from_sql(connection, cursor)

  #colnames = [desc[0] for desc in cursor.description]
  #df = pd.DataFrame(cursor.fetchall())
  #if(len(df) > 0):
  #  df.columns = colnames
  #success = sql_close_db(connection, cursor)
  return df

def return_df_from_sql(connection, cursor):
  colnames = [desc[0] for desc in cursor.description]
  df = pd.DataFrame(cursor.fetchall())
  if(len(df) > 0):
    df.columns = colnames
  success = sql_close_db(connection, cursor)
  return df


def sql_delete_all_rows(table):
  connection, cursor = sql_open_db()
  sqlCmd = """TRUNCATE {} RESTART IDENTITY;""".format(table)
  cursor.execute(sqlCmd)
  connection.commit()  
  success = sql_close_db(connection, cursor)
  return success   

def sql_open_db():
  connection = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME, user=config.DB_USER, password=config.DB_PASS)
  cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
  return connection, cursor

def sql_close_db(connection, cursor):
  connection.close()
  cursor.close()
  return True

#####################
# Logging Functions #
#####################

def get_logger():

  logs_dir = 'logs/'
  error_logfile = dt.now().strftime('log_error_%Y%m%d_%H%M%S.log')
  debug_logfile = dt.now().strftime('log_debug_%Y%m%d_%H%M%S.log')

  logger = logging.getLogger(__name__)
  logger.setLevel(logging.DEBUG)

  formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

  file_handler_errors = logging.FileHandler(logs_dir + error_logfile, mode='w')
  file_handler_errors.setFormatter(formatter)
  file_handler_errors.setLevel(logging.ERROR)

  file_handler_all = logging.FileHandler(logs_dir + debug_logfile, mode='w')
  file_handler_all.setFormatter(formatter)
  file_handler_all.setLevel(logging.DEBUG)

  stream_handler = logging.StreamHandler()
  stream_handler.setFormatter(formatter)

  logger.addHandler(file_handler_errors)
  logger.addHandler(file_handler_all)

  logger.addHandler(stream_handler)

  return logger


#### TODO #######
"""
def set_insider_trades_company(df_tickers, logger):

  for index, row in df_tickers.iterrows():
    symbol = row['Ticker']

    url = "http://openinsider.com/search?q=%s" % (symbol,)

    print("Getting Insider Trading Data: %s" % symbol)
    page = get_page_selenium(url)

    soup = BeautifulSoup(page, 'html.parser')
    table = soup.find_all('table')[11]
    df = process_insider_trading_table(table, logger)

    #TODO: Write to database
    import pdb; pdb.set_trace()
    #TODO: make an aggregate line item relating to qty and value, compared to total shares
    #TODO: add to df of consolidate metrics for all symbols                

  return True
"""

def set_todays_insider_trades(logger):
  success = False
  try:
    logger.info("Getting Insider Trades")
    url = "http://openinsider.com/insider-purchases"
    page = get_page_selenium(url)
    soup = BeautifulSoup(page, 'html.parser')
    table = soup.find_all('table')[11]

    df = convert_html_table_insider_trading_to_df(table, True)

    df.loc[df["percentage_owned"] == "New", "percentage_owned"] = "0"

    df = dataframe_convert_to_numeric(df,'percentage_owned', logger)

    df = df.sort_values(by=['percentage_owned'], ascending=False)

    df['filing_date'] = pd.to_datetime(df['filing_date'],format='%Y-%m-%d')

    #Clear out old data
    sql_delete_all_rows("Macro_InsiderTrading")

    #Write new data into table
    rename_cols = None
    add_col_values = None
    conflict_cols = None

    success = sql_write_df_to_db(df, "Macro_InsiderTrading", rename_cols, add_col_values, conflict_cols)

    logger.info("Successfully Scraped Todays Insider Trades")
  except Exception as e:
    logger.exception(f"Error: {e}")

  return success


def convert_html_table_insider_trading_to_df(table, contains_th):
  data =  {'filing_date':[],'company_ticker':[],'company_name':[],'insider_name':[],'insider_title':[],'trade_type':[],'trade_price':[],'percentage_owned':[]}

  df = pd.DataFrame(data)
  
  try:
    table_rows = table.find_all('tr')
  except AttributeError as e:
    return df

  first_row = True

  for tr in table_rows:
    temp_row = []

    if(first_row):
      first_row = False
    else:
      td = tr.find_all('td')
      for obs in td:
        text = str(obs.text).strip()
        temp_row.append(text)        

      filing_date = temp_row[1]
      company_ticker = temp_row[3]
      company_name = temp_row[4] # Name
      insider_name = temp_row[5] 
      insider_title = temp_row[6] 
      trade_type = temp_row[7] 
      trade_price = temp_row[8]
      percentage_owned = temp_row[11]

      df.loc[len(df.index)] = [filing_date,company_ticker,company_name,insider_name,insider_title,trade_type,trade_price,percentage_owned]

  return df

def format_volume_df(df):
  try:
    df['percentage_sold'] = df['percentage_sold'] * 100
  except KeyError as e:
    pass

  try:
    df['percentage_sold'] = df['percentage_sold'].map('{:,.2f}%'.format)
  except KeyError as e:
    pass

  try:
    df['last_close'] = df['last_close'].map('{:,.2f}'.format)
  except KeyError as e:
    pass

  try:
    df['vs_avg_vol_10d'] = df['vs_avg_vol_10d'].map('{:,.2f}%'.format)
  except KeyError as e:
    pass

  try:
    df['vs_avg_vol_3m'] = df['vs_avg_vol_3m'].map('{:,.2f}%'.format)
  except KeyError as e:
    pass

  try:
    df['last_volume'] = df['last_volume'].map('{:,.0f}'.format)
  except KeyError as e:
    pass

  return df


####################################################

def return_atr(df_data):
  # Creates a new column in the netflix dataframe called 'H-L' and does the high - low
  df_data['H-L'] = df_data['High'] - df_data['Low']

  # Creates a new column in the netflix dataframe called 'H-C' which is the absolute value of the high on the current day - close previous day
  # the .shift(1) function takes the close from the previous day
  df_data['H-C'] = abs(df_data['High'] - df_data['Close'].shift(1))

  # Creates a new column in the netflix dataframe called 'L-C' which is the absolute value of the low on the current day - close previous day
  df_data['L-C'] = abs(df_data['Low'] - df_data['Close'].shift(1))

  # Creates a new column in the netflix dataframe called 'TR' which chooses which is the highest out of the H-L, H-C and L-C values
  df_data['TR'] = df_data[['H-L', 'H-C', 'L-C']].max(axis=1)

  # Creates a new column in the netflix datafram called 'ATR' and calculates the ATR
  df_data['ATR'] = df_data['TR'].rolling(14).mean()

  df_data['ATR %'] = abs(df_data['ATR']/df_data['Open'])

  #Remove unnecessary columns from df_EUR_USD and rename columns
  #df_data = df_data.drop(['Open', 'High', 'Low', 'Volume'], axis=1)
  df_data = df_data.drop(['Volume'], axis=1)

  # Creates a new dataframe called netflix_sorted_df using the netflix dataframe
  # Sorts the dates from newest to oldest, rather than oldest to newest which the Yahoo Finance default
  df_sorted = df_data.sort_values(by='DATE', ascending = False)

  return df_sorted

def get_atr_prices(index, number):
  #get date range
  todays_date = date.today()
  date_str = "%s-%s-%s" % (todays_date.year, todays_date.month, todays_date.day)

  
  # Get Daily ATR 
  df_data = get_yf_historical_stock_data(index, "1d", "2000-12-28", date_str)
  df_sorted_daily_atr = return_atr(df_data)

  
  # Get Monthly ATR 
  df_data = get_yf_historical_stock_data(index, "1mo", "2000-12-28", date_str)
  df_sorted_monthly_atr = return_atr(df_data)

  
  # Get Quarterly ATR
  df_data = get_yf_historical_stock_data(index, "3mo", "2000-12-28", date_str)
  df_sorted_quarterly_atr = return_atr(df_data)

  df_sorted_daily_price = df_sorted_daily_atr.drop(['H-L', 'H-C', 'L-C', 'TR', 'ATR'], axis=1)
  df_sorted_daily_price = df_sorted_daily_price.rename(columns={"Close": index})

  return df_sorted_daily_atr, df_sorted_monthly_atr, df_sorted_quarterly_atr, df_sorted_daily_price

def atr_to_excel(df_price_action, df_ticker1_daily, df_ticker1_monthly, df_ticker1_quarterly,df_ticker2_daily, df_ticker2_monthly, df_ticker2_quarterly):

  output = io.BytesIO()
  writer = pd.ExcelWriter(output, engine='xlsxwriter')

  df_price_action.to_excel(writer, index=False, sheet_name='PriceAction')
  df_ticker1_daily.to_excel(writer, index=False, sheet_name='Ticker1Daily')
  df_ticker1_monthly.to_excel(writer, index=False, sheet_name='Ticker1Monthly')
  df_ticker1_quarterly.to_excel(writer, index=False, sheet_name='Ticker1Quarterly')
  df_ticker2_daily.to_excel(writer, index=False, sheet_name='Ticker2Daily')
  df_ticker2_monthly.to_excel(writer, index=False, sheet_name='Ticker2Monthly')
  df_ticker2_quarterly.to_excel(writer, index=False, sheet_name='Ticker2Quarterly')

  workbook = writer.book
  worksheet = writer.sheets['PriceAction']

  format1 = workbook.add_format({'num_format': '0.00'}) 
  worksheet.set_column('A:A', None, format1)  
  writer.save()
  processed_data = output.getvalue()
  return processed_data

def set_ism_manufacturing(logger):
  success = False
  logger.info("Getting ISM Manufacturing")

  para_manufacturing, para_new_orders, para_production, ism_date, ism_month = scrape_ism_manufacturing_data_from_page()        

  # We have scraped the important data from the ism manufacturing website. Now we need to extract the rankings
  df_manufacturing_rankings = extract_ism_manufacturing_rankings(para_manufacturing, ism_date)
  df_new_orders_rankings = extract_ism_manufacturing_rankings(para_new_orders, ism_date)
  df_production_rankings = extract_ism_manufacturing_rankings(para_production, ism_date)
  df_ism_headline_index = extract_ism_manufacturing_headline_index(ism_date, ism_month)

  #TODO: Write to database
  rename_cols = {
    'DATE':'ism_date',                                          
    'Apparel,Leather&AlliedProducts':'apparel_leather_allied_products',                      
    'ChemicalProducts':'chemical_products',                                 
    'Computer&ElectronicProducts':'computer_electronic_products',                           
    'ElectricalEquipment,Appliances&Components':'electrical_equipment_appliances_components',             
    'FabricatedMetalProducts':'fabricated_metal_products',                                 
    'Food,Beverage&TobaccoProducts':'food_beverage_tobacco_products',                        
    'Furniture&RelatedProducts':'furniture_related_products',                             
    'Machinery':'machinery',                                               
    'MiscellaneousManufacturing':'miscellaneous_manufacturing',                              
    'NonmetallicMineralProducts':'nonmetallic_mineral_products',                              
    'PaperProducts':'paper_products',                                            
    'Petroleum&CoalProducts':'petroleum_coal_products',                                 
    'Plastics&RubberProducts':'plastics_rubber_products',                                
    'PrimaryMetals':'primary_metals',                                            
    'Printing&RelatedSupportActivities':'printing_related_support_activities',                     
    'TextileMills':'textile_mills',                                            
    'TransportationEquipment':'transportation_equipment',                                  
    'WoodProducts':'wood_products'  
  }
  add_col_values = None
  conflict_cols = 'ism_date'

  success = sql_write_df_to_db(df_manufacturing_rankings, "macro_us_ism_manufacturing_sectors", rename_cols, add_col_values, conflict_cols)
  success = sql_write_df_to_db(df_new_orders_rankings, "macro_us_ism_manufacturing_new_orders", rename_cols, add_col_values, conflict_cols)
  success = sql_write_df_to_db(df_production_rankings, "macro_us_ism_manufacturing_production", rename_cols, add_col_values, conflict_cols)

  rename_cols = {
      'DATE':'ism_date'
  }
  add_col_values = None
  conflict_cols = "ism_date"
  success = sql_write_df_to_db(df_ism_headline_index, "macro_us_ism_manufacturing_headline", rename_cols, add_col_values, conflict_cols)

  logger.info("Successfully retrieved ISM Manufacturing")

  return success

def scrape_ism_manufacturing_data_from_page():

  ism_date, ism_month, page = get_ism_manufacturing_page()

  soup = BeautifulSoup(page.content, 'html.parser')

  #get all paragraphs
  paras = soup.find_all("p", attrs={'class': None})

  para_manufacturing = "" 
  para_new_orders = ""
  para_production = ""
  pattern_manufacturing = re.compile(r'(manufacturing industries (that\s)?report(ed|ing) growth in (January|February|...|December))')
  pattern_new_orders = re.compile(r'(growth in new orders [A-Za-z,&;\s]* (January|February|...|December))')
  pattern_production = re.compile(r'(growth in production [A-Za-z,&;\s]* (January|February|...|December))')

  for para in paras:
      #Get the specific paragraph
      if(len(pattern_manufacturing.findall(para.text)) > 0):
        if(len(para_manufacturing) == 0):
          para_manufacturing = para.text

      if(len(pattern_new_orders.findall(para.text)) > 0):
        if(len(para_new_orders) == 0):
          para_new_orders = para.text

      if(len(pattern_production.findall(para.text)) > 0):
        if(len(para_production) == 0):          
          para_production = para.text
  
  return para_manufacturing, para_new_orders, para_production, ism_date, ism_month

def get_ism_manufacturing_page():

  ism_date, ism_month = get_ism_date(1)
  #url_ism = get_ism_manufacturing_url(ism_month)
  url_ism = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/pmi/%s' % (ism_month.lower(),)
  #url_ism = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/pmi/%s' % ('august',)

  #This is duplicate code found in get_page function but we need to handle special case of ism data where page may not be found and we need to switch to 1 month previous
  header={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36'}
  page = requests.get(url=url_ism,headers=header)

  try:
      page.raise_for_status()
  except requests.exceptions.HTTPError as e:
    if(page.status_code == 404):
        # Use previous month to get ISM data
        ism_date, ism_month = get_ism_date(2)
        #url_ism = get_ism_manufacturing_url(ism_month)
        url_ism = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/pmi/%s' % (ism_month.lower(),)

        page = get_page(url_ism)

    else:
        raise Exception("Http Response (%s) Is Not 200: %s" % (url_ism,str(page.status_code)))

  return ism_date, ism_month, page


def extract_ism_manufacturing_rankings(industry_str, ism_date):

    #ism_date, ism_month, page = get_ism_manufacturing_content()

    #Use regex (https://pythex.org/) to get substring that contains order of industries. It should return 2 matches - for increase and decrease   
    pattern_select = re.compile(r'((?<=following order:\s)[A-Za-z,&;\s]*.|(?<=are:\s)[A-Za-z,&;\s]*.|(?<=are\s)[A-Za-z,&;\s]*.)')
    matches = pattern_select.finditer(industry_str)
    match_arr = []
    pattern_remove = r'and|\.'
    for match in matches:
        new_str = re.sub(pattern_remove, '',match.group(0))
        match_arr.append(new_str)

    #put increase and decrease items into arrays
    increase_arr = match_arr[0].split(';')
    try:
        decrease_arr = []
        decrease_arr = match_arr[1].split(';')        
    except IndexError as e:
        #There must only be one industry reporting decrease, so extract that one.
        pattern_select_decrease = re.compile(r'(only\sindustry[A-Za-z,&;\s]*)')        
        match = pattern_select_decrease.search(industry_str)

        if(match):
            pattern_remove = r'only\sindustry[A-Za-z,&;\s]*is\s'
            new_str = re.sub(pattern_remove, '',match.group(0))
            if(new_str):
                decrease_arr.append(new_str)

    df_rankings = pd.DataFrame()

    #Add Rankings columns to df
    ranking = len(increase_arr)
    index = 0
    for industry in increase_arr:
        industry = industry.replace(' ','')
        #df_rankings[industry.lstrip()] = [ranking - index]      
        df_rankings[industry] = [ranking - index]      

        index += 1

    ranking = len(decrease_arr)
    index = 0
    for industry in decrease_arr:
        industry = industry.replace(' ','')
        #df_rankings[industry.lstrip()] = [0 - (ranking - index)]      
        df_rankings[industry] = [0 - (ranking - index)]      
        index += 1

    if(len(df_rankings.columns) < 18):
        #df_columns_18_industries = ['Machinery','Computer & Electronic Products','Paper Products','Apparel, Leather & Allied Products','Printing & Related Support Activities',
        #                    'Primary Metals','Nonmetallic Mineral Products','Petroleum & Coal Products','Plastics & Rubber Products','Miscellaneous Manufacturing',
        #                    'Food, Beverage & Tobacco Products','Furniture & Related Products','Transportation Equipment','Chemical Products','Fabricated Metal Products',
        #                    'Electrical Equipment, Appliances & Components','Textile Mills','Wood Products']

        df_columns_18_industries = ['Machinery','Computer&ElectronicProducts','PaperProducts','Apparel,Leather&AlliedProducts','Printing&RelatedSupportActivities',
                            'PrimaryMetals','NonmetallicMineralProducts','Petroleum&CoalProducts','Plastics&RubberProducts','MiscellaneousManufacturing',
                            'Food,Beverage&TobaccoProducts','Furniture&RelatedProducts','TransportationEquipment','ChemicalProducts','FabricatedMetalProducts',
                            'ElectricalEquipment,Appliances&Components','TextileMills','WoodProducts']

        #Find out what columns are missing
        missing_columns = _util_check_diff_list(df_columns_18_industries,df_rankings.columns)
        
        #Add missing columns to df_ranking with zero as the rank number
        for col in missing_columns:
            df_rankings[col] = [0]

    #Add DATE column to df
    df_rankings["DATE"] = [ism_date]

    # Reorder Columns
    # get a list of columns
    cols = list(df_rankings)
    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index('DATE')))
    cols.insert(1, cols.pop(cols.index('Apparel,Leather&AlliedProducts')))
    cols.insert(2, cols.pop(cols.index('Machinery')))
    cols.insert(3, cols.pop(cols.index('PaperProducts')))
    cols.insert(4, cols.pop(cols.index('Computer&ElectronicProducts')))
    cols.insert(5, cols.pop(cols.index('Petroleum&CoalProducts')))
    cols.insert(6, cols.pop(cols.index('PrimaryMetals')))
    cols.insert(7, cols.pop(cols.index('Printing&RelatedSupportActivities')))
    cols.insert(8, cols.pop(cols.index('Furniture&RelatedProducts')))
    cols.insert(9, cols.pop(cols.index('TransportationEquipment')))
    cols.insert(10, cols.pop(cols.index('ChemicalProducts')))
    cols.insert(11, cols.pop(cols.index('Food,Beverage&TobaccoProducts')))
    cols.insert(12, cols.pop(cols.index('MiscellaneousManufacturing')))
    cols.insert(13, cols.pop(cols.index('ElectricalEquipment,Appliances&Components')))
    cols.insert(14, cols.pop(cols.index('Plastics&RubberProducts')))
    cols.insert(15, cols.pop(cols.index('FabricatedMetalProducts')))
    cols.insert(16, cols.pop(cols.index('WoodProducts')))
    cols.insert(17, cols.pop(cols.index('TextileMills')))
    cols.insert(18, cols.pop(cols.index('NonmetallicMineralProducts')))

    # reorder
    df_rankings = df_rankings[cols]

    return df_rankings

def extract_ism_manufacturing_headline_index(ism_date, ism_month):

  #url_ism = get_ism_manufacturing_url(ism_month)
  url_ism = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/pmi/%s' % (ism_month.lower(),)

  page = get_page(url_ism)

  soup = BeautifulSoup(page.content, 'html.parser')

  #Get all html tables on the page
  tables = soup.find_all('table')    
  table_at_a_glance = tables[0]
  
  #Convert the tables into dataframes so that we can read the data
  df_at_a_glance = convert_html_table_to_df(table_at_a_glance, True)

  #Drop Unnecessary Columns
  column_numbers = [x for x in range(df_at_a_glance.shape[1])]  # list of columns' integer indices
  column_numbers .remove(2) #removing column integer index 0
  column_numbers .remove(3)
  column_numbers .remove(4)
  column_numbers .remove(5)
  column_numbers .remove(6)
  df_at_a_glance = df_at_a_glance.iloc[:, column_numbers] #return all columns except the 0th column

  #Flip df around
  df_at_a_glance = df_at_a_glance.T

  #Rename Columns
  df_at_a_glance = df_at_a_glance.rename(columns={0: "ISM", 1:"NEW_ORDERS",2:"PRODUCTION",3:"EMPLOYMENT",4:"DELIVERIES",
                                                  5:"INVENTORIES",6:"CUSTOMERS_INVENTORIES",7:"PRICES",8:"BACKLOG_OF_ORDERS",9:"EXPORTS",10:"IMPORTS"})

  #Drop the first row because it contains the old column names
  df_at_a_glance = df_at_a_glance.iloc[1: , :]
  df_at_a_glance = df_at_a_glance.reset_index()
  df_at_a_glance = df_at_a_glance.drop(columns='index', axis=1)

  #Fix datatypes of df_at_a_glance
  for column in df_at_a_glance:
      df_at_a_glance[column] = pd.to_numeric(df_at_a_glance[column])

  #Add DATE column to df
  df_at_a_glance["DATE"] = [ism_date]

  # Reorder Columns
  # get a list of columns
  cols = list(df_at_a_glance)
  cols.insert(0, cols.pop(cols.index('DATE')))
  cols.insert(1, cols.pop(cols.index('NEW_ORDERS')))
  cols.insert(2, cols.pop(cols.index('IMPORTS')))
  cols.insert(3, cols.pop(cols.index('BACKLOG_OF_ORDERS')))
  cols.insert(4, cols.pop(cols.index('PRICES')))
  cols.insert(5, cols.pop(cols.index('PRODUCTION')))
  cols.insert(6, cols.pop(cols.index('CUSTOMERS_INVENTORIES')))
  cols.insert(7, cols.pop(cols.index('INVENTORIES')))
  cols.insert(8, cols.pop(cols.index('DELIVERIES')))
  cols.insert(9, cols.pop(cols.index('EMPLOYMENT')))
  cols.insert(10, cols.pop(cols.index('EXPORTS')))
  cols.insert(11, cols.pop(cols.index('ISM')))

  # reorder
  df_at_a_glance = df_at_a_glance[cols]

  return df_at_a_glance

def get_ism_date(delta):
  #get date range
  todays_date = date.today()

  #use todays date to get ism month (first day of last month) and use the date in scraping functions
  ism_date = todays_date - relativedelta(months=delta)
  ism_date = "01-%s-%s" % (ism_date.month, ism_date.year) #make the ism date the first day of ism month
  ism_date = dt.strptime(ism_date, "%d-%m-%Y")
  ism_month = ism_date.strftime("%B")

  return ism_date, ism_month

def set_ism_services(logger):
  success = False
  logger.info("Getting ISM Services")
  para_services, para_new_orders, para_business, ism_date, ism_month = scrape_services_new_orders_production()
  df_services_rankings = extract_ism_services_rankings(para_services, ism_date)
  df_business_rankings = extract_ism_services_rankings(para_business, ism_date)
  df_new_orders_rankings = extract_ism_services_rankings(para_new_orders, ism_date)
  df_ism_headline_index = scrape_ism_services_headline_index(ism_date, ism_month)

  df_services_rankings.columns = df_services_rankings.columns.str.replace(' ', '')
  df_business_rankings.columns = df_business_rankings.columns.str.replace(' ', '')
  df_new_orders_rankings.columns = df_new_orders_rankings.columns.str.replace(' ', '')
  df_ism_headline_index.columns = df_ism_headline_index.columns.str.replace(' ', '')

  """
  rename_cols = {
      'DATE':'ism_date',
      'Arts, Entertainment & Recreation':'arts_entertainment_recreation',
      'Other Services':'other_services',
      'Health Care & Social Assistance':'health_care_social_assistance',
      'Accommodation & Food Services':'accommodation_food_services',
      'Finance & Insurance':'finance_insurance',
      'Real Estate, Rental & Leasing':'real_estate_rental_leasing',
      'Transportation & Warehousing':'transportation_warehousing',
      'Mining':'mining',
      'Construction':'construction',
      'Wholesale Trade':'wholesale_trade',
      'Public Administration':'public_administration',
      'Professional, Scientific & Technical Services':'professional_scientific_technical_services',
      'Agriculture, Forestry, Fishing & Hunting':'agriculture_forestry_fishing_hunting',
      'Information':'information',
      'Educational Services':'educational_services',
      'Management of Companies & Support Services':'management_of_companies_support_services',
      'Retail Trade':'retail_trade',
      'Utilities':'utilities',
  }
  """
  rename_cols = {
      'DATE':'ism_date',
      'Arts,Entertainment&Recreation':'arts_entertainment_recreation',
      'OtherServices':'other_services',
      'HealthCare&SocialAssistance':'health_care_social_assistance',
      'Accommodation&FoodServices':'accommodation_food_services',
      'Finance&Insurance':'finance_insurance',
      'RealEstate,Rental&Leasing':'real_estate_rental_leasing',
      'Transportation&Warehousing':'transportation_warehousing',
      'Mining':'mining',
      'Construction':'construction',
      'WholesaleTrade':'wholesale_trade',
      'PublicAdministration':'public_administration',
      'Professional,Scientific&TechnicalServices':'professional_scientific_technical_services',
      'Agriculture,Forestry,Fishing&Hunting':'agriculture_forestry_fishing_hunting',
      'Information':'information',
      'EducationalServices':'educational_services',
      'ManagementofCompanies&SupportServices':'management_of_companies_support_services',
      'RetailTrade':'retail_trade',
      'Utilities':'utilities',
  }
  #import pdb; pdb.set_trace()
  add_col_values = None
  conflict_cols = 'ism_date'
  success = sql_write_df_to_db(df_services_rankings, "macro_us_ism_services_sectors", rename_cols, add_col_values, conflict_cols)
  success = sql_write_df_to_db(df_business_rankings, "macro_us_ism_services_business_activity", rename_cols, add_col_values, conflict_cols)
  success = sql_write_df_to_db(df_new_orders_rankings, "macro_us_ism_services_new_orders", rename_cols, add_col_values, conflict_cols)

  rename_cols = {
      'DATE':'ism_date',
      'ISM_SERVICES':'ISM'
  }
  add_col_values = None
  conflict_cols = "ism_date"
  success = sql_write_df_to_db(df_ism_headline_index, "macro_us_ism_services_headline", rename_cols, add_col_values, conflict_cols)

  logger.info("Successfully retrieved ISM Manufacturing")

  return success

def scrape_services_new_orders_production():

    ism_date, ism_month, page = get_ism_services_content()

    soup = BeautifulSoup(page.content, 'html.parser')

    paras = soup.find_all("p")

    para_services = "" 
    para_new_orders = ""
    para_business = ""
    pattern_select = re.compile(r'((?<=following order:\s)[A-Za-z,&;\s]*.|(?<=are:\s)[A-Za-z,&;\s]*.)')

    for para in paras:
        #Get the specific paragraph
        if('services industries' in para.text and '%s' % (ism_month) in para.text and len(pattern_select.findall(para.text)) > 0):
            para_services = para.text

        if('new orders' in para.text and '%s' % (ism_month) in para.text and len(pattern_select.findall(para.text)) > 0):
            para_new_orders = para.text

        if('business activity' in para.text and '%s' % (ism_month) in para.text and len(pattern_select.findall(para.text)) > 0):
            para_business = para.text

    return para_services, para_new_orders, para_business, ism_date, ism_month


def extract_ism_services_rankings(industry_str, ism_date):

    #ism_date, ism_month, page = get_ism_services_content()

    #Use regex (https://pythex.org/) to get substring that contains order of industries. It should return 2 matches - for increase and decrease   
    pattern_select = re.compile(r'((?<=following order:\s)[A-Za-z,&;\s]*.|(?<=are:\s)[A-Za-z,&;\s]*.|(?<=are\s)[A-Za-z,&;\s]*.)')
    matches = pattern_select.finditer(industry_str)
    match_arr = []
    pattern_remove = r'and|\.'
    for match in matches:
        new_str = re.sub(pattern_remove, '',match.group(0))
        match_arr.append(new_str)

    #put increase and decrease items into arrays
    try:
        increase_arr = match_arr[0].split(';')
    except IndexError as e:
        increase_arr = []
    try:
        decrease_arr = []
        decrease_arr = match_arr[1].split(';')        
    except IndexError as e:
        #There must only be one industry reporting decrease, so extract that one.
        pattern_select_decrease = re.compile(r'(only\sindustry[A-Za-z,&;\s]*)')        
        match = pattern_select_decrease.search(industry_str)

        if(match):
            pattern_remove = r'only\sindustry[A-Za-z,&;\s]*is\s'
            new_str = re.sub(pattern_remove, '',match.group(0))
            if(new_str):
                decrease_arr.append(new_str)

    df_rankings = pd.DataFrame()

    #Add Rankings columns to df
    ranking = len(increase_arr)
    index = 0
    for industry in increase_arr:
        industry = industry.replace(' ','')        
        #df_rankings[industry.lstrip()] = [ranking - index]      
        df_rankings[industry] = [ranking - index]      
        index += 1

    ranking = len(decrease_arr)
    index = 0
    for industry in decrease_arr:
        industry = industry.replace(' ','')
        #df_rankings[industry.lstrip()] = [0 - (ranking - index)]      
        df_rankings[industry] = [0 - (ranking - index)]      
        index += 1

    if(len(df_rankings.columns) < 18):
        #df_columns_18_industries = ['Utilities','Retail Trade','Arts, Entertainment & Recreation','Other Services','Health Care & Social Assistance','Accommodation & Food Services',
        #                            'Transportation & Warehousing','Finance & Insurance','Real Estate, Rental & Leasing','Public Administration','Agriculture, Forestry, Fishing & Hunting',
        #                            'Construction','Professional, Scientific & Technical Services','Wholesale Trade','Management of Companies & Support Services','Mining',
        #                            'Information','Educational Services']

        df_columns_18_industries = ['Utilities','RetailTrade','Arts,Entertainment&Recreation','OtherServices','HealthCare&SocialAssistance','Accommodation&FoodServices',
                                    'Transportation&Warehousing','Finance&Insurance','RealEstate,Rental&Leasing','PublicAdministration','Agriculture,Forestry,Fishing&Hunting',
                                    'Construction','Professional,Scientific&TechnicalServices','WholesaleTrade','ManagementofCompanies&SupportServices','Mining',
                                    'Information','EducationalServices']


        #Find out what columns are missing
        missing_columns = _util_check_diff_list(df_columns_18_industries,df_rankings.columns)
        
        #Add missing columns to df_ranking with zero as the rank number
        for col in missing_columns:
            df_rankings[col] = [0]

    #Add DATE column to df
    df_rankings["DATE"] = [ism_date]

    return df_rankings

def scrape_ism_services_headline_index(ism_date, ism_month):

    #url_ism = get_ism_services_url(ism_month)
    url_ism = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/services/%s' % (ism_month.lower(),)

    page = get_page(url_ism)

    soup = BeautifulSoup(page.content, 'html.parser')

    #Get all html tables on the page
    tables = soup.find_all('table')    
    table_at_a_glance = tables[0]
    
    #Convert the tables into dataframes so that we can read the data
    #df_at_a_glance = convert_html_table_to_df(table_at_a_glance, True)

    table_rows = table_at_a_glance.find_all('tbody')[0].find_all('tr')
    table_rows_header = table_at_a_glance.find_all('tr')[1].find_all('th')
    df_at_a_glance = pd.DataFrame()

    index = 0

    for header in table_rows_header:
        df_at_a_glance.insert(index,str(header.text).strip(),[],True)
        index+=1

    #Insert New Row. Format the data to show percentage as float
    for tr in table_rows:
        temp_row = []

        tr_th = tr.find('th')
        text = str(tr_th.text).strip()
        temp_row.append(text)        

        td = tr.find_all('td')
        for obs in td:
            text = str(obs.text).strip()
            temp_row.append(text)        
        
        if(len(temp_row) == len(df_at_a_glance.columns)):
            df_at_a_glance.loc[len(df_at_a_glance.index)] = temp_row
    
    #Drop Unnecessary Columns
    column_numbers = [x for x in range(df_at_a_glance.shape[1])]  # list of columns' integer indices
    column_numbers .remove(7)
    column_numbers .remove(8)
    column_numbers .remove(9)

    df_at_a_glance = df_at_a_glance.iloc[:, column_numbers] #return all columns except the 0th column

    #Flip df around
    df_at_a_glance = df_at_a_glance.T

    # Rename Columns as per requirements of excel file 017
    df_at_a_glance = df_at_a_glance.rename(columns={0: "ISM_SERVICES", 1:"BUSINESS_ACTIVITY",2:"NEW_ORDERS",3:"EMPLOYMENT",4:"DELIVERIES",
                                                    5:"INVENTORIES",6:"PRICES",7:"BACKLOG_OF_ORDERS",8:"EXPORTS",9:"IMPORTS",10:"INVENTORY_SENTIMENT",11:"CUSTOMER_INVENTORIES"})

    #Drop the first row because it contains the old column names
    df_at_a_glance = df_at_a_glance.iloc[1: , :]
    df_at_a_glance = df_at_a_glance.head(1)
    df_at_a_glance = df_at_a_glance.reset_index()
    df_at_a_glance = df_at_a_glance.drop(columns='index', axis=1)
    df_at_a_glance = df_at_a_glance.drop(columns='CUSTOMER_INVENTORIES', axis=1)

    #Fix datatypes of df_at_a_glance
    for column in df_at_a_glance:
        df_at_a_glance[column] = pd.to_numeric(df_at_a_glance[column])

    #Add DATE column to df
    df_at_a_glance["DATE"] = [ism_date]

    # Put DATE as the first column
    # get a list of columns
    cols = list(df_at_a_glance)
    cols.insert(0, cols.pop(cols.index('DATE')))

    # reorder
    df_at_a_glance = df_at_a_glance[cols]

    return df_at_a_glance

def get_ism_services_content():

  ism_date, ism_month = get_ism_date(1)
  #url_ism = get_ism_services_url(ism_month)

  url_ism = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/services/%s' % (ism_month.lower(),)

  #This is duplicate code found in get_page function but we need to handle special case of ism data where page may not be found and we need to switch to 1 month previous
  header={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36'}
  page = requests.get(url=url_ism,headers=header)

  try:
      page.raise_for_status()
  except requests.exceptions.HTTPError as e:
    if(page.status_code == 404):
        # Use previous month to get ISM data
        ism_date, ism_month = get_ism_date(2)
        #url_ism = get_ism_services_url(ism_month)
        url_ism = 'https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/services/%s' % (ism_month.lower(),)

        page = get_page(url_ism)

    else:
        raise Exception("Http Response (%s) Is Not 200: %s" % (url_ism,str(page.status_code)))

  return ism_date, ism_month, page

##########################################

def temp_load_excel_data_to_db(excel_file_path, sheet_name, database_table,rename_cols=None, conflict_cols=False):
  #import pdb; pdb.set_trace()
  # Load original data from excel file into original df
  #df_original = convert_excelsheet_to_dataframe(excel_file_path, sheet_name, False)
  df_original = convert_csv_to_dataframe(excel_file_path, True,'%m/%d/%Y')
  df_original = df_original.fillna(method='ffill')
  #TODO: Need to write this data into the database
  #df_original = df_original.drop(['SP500','GDPC1','GDPQoQ','GDPYoY','GDPQoQ_ANNUALIZED','GDPC1_QoQ','GDPC1_QoQ_ANNUALIZED','GDPC1_YoY',], axis=1)
  #import pdb; pdb.set_trace()
  add_col_values = {}
  success = sql_write_df_to_db(df_original, database_table, rename_cols, add_col_values, conflict_cols)

  return success

def convert_csv_to_dataframe(excel_file_path,date_exists=False, date_format=None):

  if(isWindows):
    filepath = os.getcwd()
    excel_file_path = filepath + excel_file_path.replace("/","\\")

  else:
    filepath = os.path.realpath(__file__)
    excel_file_path = filepath[:filepath.rfind('/')] + excel_file_path


  df = pd.read_csv(excel_file_path)

  if(date_exists):
    df['DATE'] = pd.to_datetime(df['DATE'],format=date_format)

  return df

def convert_excelsheet_to_dataframe(excel_file_path,sheet_name,date_exists=False, index_col=None, date_format='%d/%m/%Y'):

  if(isWindows):
    filepath = os.getcwd()
    excel_file_path = filepath + excel_file_path.replace("/","\\")

  else:
    filepath = os.path.realpath(__file__)
    excel_file_path = filepath[:filepath.rfind('/')] + excel_file_path

  if(index_col):
    df = pd.read_excel(excel_file_path, sheet_name=sheet_name, index_col=index_col, engine='openpyxl')
  else:
    df = pd.read_excel(excel_file_path, sheet_name=sheet_name, engine='openpyxl')

  if(date_exists):
    df['DATE'] = pd.to_datetime(df['DATE'],format=date_format)

  return df

def display_chart(settings, df,series, tab, series2=None, col=None):
  #ax = df['myvar'].plot(kind='bar')
  #ax.yaxis.set_major_formatter(mtick.PercentFormatter())

  #import pdb; pdb.set_trace()
  #plt.style.use('ggplot')
  plt.style.use('seaborn-v0_8-whitegrid')
  #plt.style.use('bmh')
  
  if(settings['ypercentage']):
    df[series] = df[series] * 100
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter())            

  #Add the appropriate dataframes to the 2 histogram vars
  if(settings['type'] == 'line'):
    plt.plot(df["DATE"], df[series])
    if(series2):
      plt.plot(df["DATE"], df[series2])
      # Insert legend because we now have multiple values
      plt.legend([series, series2], fontsize="x-small", loc="upper left")

  elif(settings['type'] == 'bar'):
    plt.bar(df["DATE"], df[series], width=50)       

  plt.title(settings['title'])
  plt.xlabel(settings['xlabel'])
  plt.ylabel(settings['ylabel'])
  plt.xticks(rotation='vertical')
  # Set the font size for x tick labels
  plt.rc('xtick', labelsize=8)
  plt.rc('ytick', labelsize=8)
  #plt.tight_layout()
  plt.grid(True)

  if(col):
    col.pyplot(plt)
  else:
    tab.pyplot(plt)

  plt.clf()
 
def display_chart_assets(settings, df,x_axis,y_axis, tab, series2=None, col=None):
  #import pdb; pdb.set_trace()
  plt.style.use('seaborn-v0_8-whitegrid')
  
  if(settings['ypercentage']):
    df[y_axis] = df[y_axis] * 100
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter())            

  #Add the appropriate dataframes to the 2 histogram vars
  if(settings['type'] == 'line'):
    plt.plot(df[x_axis], df[y_axis])

  elif(settings['type'] == 'bar'):
    plt.bar(df[x_axis], df[y_axis], edgecolor='black')       

  plt.title(settings['title'])
  plt.xlabel(settings['xlabel'])
  plt.ylabel(settings['ylabel'])
  plt.xticks(rotation='vertical')
  # Set the font size for x tick labels
  plt.rc('xtick', labelsize=8)
  plt.rc('ytick', labelsize=8)
  #plt.tight_layout()
  plt.grid(True)

  if(col):
    col.pyplot(plt)
  else:
    tab.pyplot(plt)

  plt.clf()


def display_chart_ism(settings, df,series, col=None):

  #TODO: Need to fix the following:
  # 1) Ticks on the x axis needs to reflect df values
  # 2) Keeping the same y axis range fixed
  # 3) Lines around each bar
  data = {}
  plt.style.use('seaborn-v0_8-whitegrid')
  df['DATE'] = df['DATE'].astype(str) 
  df_temp = df[['DATE',series]]

  for index, row in df_temp.iterrows():
    data[row[0]] = row[1]

  plt.ylim(-15, 15)

  names = list(data.keys())
  values = list(data.values())

  # https://matplotlib.org/stable/gallery/lines_bars_and_markers/categorical_variables.html
  #fig, axs = plt.subplots(1, 3, figsize=(9, 3), sharey=True)
  plt.bar(names, values)
  plt.title(settings['title'])
  plt.xlabel(settings['xlabel'])
  plt.ylabel(settings['ylabel'])
  plt.xticks(rotation='vertical')
  # Set the font size for x tick labels
  plt.rc('xtick', labelsize=8)
  plt.rc('ytick', labelsize=8)
  plt.set_loglevel('WARNING')
  col.pyplot(plt)

  plt.clf()

#def return_styled_ism_table1(df):
#  df_formatted = df.reset_index(drop=True)
#  df_formatted = df_formatted.T

#  col1 = str(df_formatted[:1][0]['ism_date']) 
#  col2 = str(df_formatted[:1][1]['ism_date']) 
#  col3 = str(df_formatted[:1][2]['ism_date'])
#  rename_cols = {0: col1,1:col2,2:col3}

#  df_formatted = df_formatted.rename(columns=rename_cols)
#  df_formatted = df_formatted.drop('ism_date')

  #TODO Format columns to integers. 
#  df_formatted[col1] = pd.to_numeric(df_formatted[col1])
#  df_formatted[col2] = pd.to_numeric(df_formatted[col2])
#  df_formatted[col3] = pd.to_numeric(df_formatted[col3])

  #TODO: Apply gradient to last column
#  gradient_cols = [col3]
#  style_t3 = format_columns(df_formatted, gradient_cols)

#  return style_t3
   

def standard_display(series_name, tab, title, period, series_display,col1, col2):

  #eval("df_us%s_all" % series), df_us_gdp_recent = get_stlouisfed_data('gdpc1', 'Q', 10)
  #eval('df_us{0}_all'.format(series)), eval('df_us{0}_recent'.format(series)) 
  
  df_series_all, df_series_recent = get_stlouisfed_data(series_name, period, 10)

  series = series_display

  if(series == 'YoY' or series == 'MoM'):
     ypercentage = True
  else:
     ypercentage = False

  #tab.subheader(title)

  chart_settings = {
      "type": "line",
      "title": title, 
      "xlabel": "Year", 
      "ylabel": title,
      "ypercentage": ypercentage,

  }

  display_chart(chart_settings, df_series_all, series, tab,col=col1)

  chart_settings = {
      "type": "line",
      "title": '{0} - Last 10 Years'.format(title), 
      "xlabel": "Year", 
      "ylabel": title, 
      "ypercentage": ypercentage,
  }

  display_chart(chart_settings, deepcopy(df_series_recent), series, tab,col=col2)

  chart_settings = {
      "type": "bar",
      "title": '{0} - MoM'.format(title), 
      "xlabel": "Year", 
      "ylabel": "MoM", 
      "ypercentage": ypercentage,
  }

  display_chart(chart_settings, df_series_all, 'MoM', tab,col=col1)

  chart_settings = {
      "type": "bar",
      "title": '{0} - MoM - Last 10 Years'.format(title), 
      "xlabel": "Year", 
      "ylabel": "MoM", 
      "ypercentage": ypercentage,
  }

  display_chart(chart_settings, deepcopy(df_series_recent), 'MoM', tab,col=col2)

  rename_cols = {'DATE': 'Date (MM-DD-YYYY)', series_name: title}
  cols_gradient = ['YoY']
  cols_drop = ['QoQ','QoQ_ANNUALIZED']
  format_cols = {
      'MoM': '{:,.2%}'.format,
      'YoY': '{:,.2%}'.format,
      title: '{:,.2f}'.format,
      'Date (MM-DD-YYYY)': lambda t: t.strftime("%m-%d-%Y"),
  }

  disp,df = style_df_for_display_date(df_series_recent,cols_gradient,rename_cols,cols_drop,format_cols)

  tab.markdown(disp.to_html(), unsafe_allow_html=True)

  return df_series_all, df_series_recent

# 10y database Data from Investing.com
def set_10y_rates(logger):
  success = False
  country_list = ['u.s.','canada','brazil','germany','france','uk','australia','china']

  df_invest_10y = get_invest_data_manual_scrape(country_list,'10')
  df_invest_10y = df_invest_10y.rename(columns={"DATE":"dt", "u.s.": "us"})

  # Fill NA values by propegating values before
  df_invest_10y = df_invest_10y.fillna(method='ffill')

  # Write to database macro_ir_10y
  try:
    rename_cols = {}
    add_col_values = None
    conflict_cols = "dt"
    success = sql_write_df_to_db(df_invest_10y, "macro_ir_10y", rename_cols, add_col_values, conflict_cols)

    logger.info("Successfully retrieved 10y Rates")
  except Exception as e:
    logger.error("Error retrieving 10y Rates")

  return success

# 2y database Data from Investing.com
def set_2y_rates(logger):
  success = False
  country_list = ['u.s.','canada','brazil','germany','france','uk','australia','china']

  df_invest_2y = get_invest_data_manual_scrape(country_list,'2')
  df_invest_2y = df_invest_2y.rename(columns={"DATE":"dt", "u.s.": "us"})

  # Fill NA values by propegating values before
  df_invest_2y = df_invest_2y.fillna(method='ffill')

  # Write to database macro_ir_10y
  try:
    rename_cols = {}
    add_col_values = None
    conflict_cols = "dt"
    success = sql_write_df_to_db(df_invest_2y, "macro_ir_2y", rename_cols, add_col_values, conflict_cols)

    logger.info("Successfully retrieved 2y Rates")
  except Exception as e:
    logger.error("Error retrieving 2y Rates")

  return success

def calc_ir_metrics(df):

  cols = list(df.columns)
  country = cols[1]

  last_date = df.iloc[-1]['dt']
  last_value = df.iloc[-1][country]

  df_series = df.copy().squeeze()
  df_series['dt'] = pd.to_datetime(df_series['dt'],format='%Y-%m-%d')
  df_series[country] = pd.to_numeric(df_series[country])
  rename_cols = {"dt": "series_date"}
  df_series = df_series.rename(columns=rename_cols)

  # calculate_asset_percentage_changes
  #1w 
  td = timedelta(days=5)
  last_5_days_date = last_date - td
  df_last_5_days = util_return_date_values(df_series,last_5_days_date)
  last_5_days_value = df_last_5_days[country].values[0]
  # minus last price
  last_5_days_value = decimal.Decimal(last_value) - decimal.Decimal(last_5_days_value)
  last_5_days_value = round(last_5_days_value, 2)

  #1m 
  rd = relativedelta(months=+1)
  last_month_date = last_date - rd
  df_last_month = util_return_date_values(df_series,last_month_date)
  last_month_value = df_last_month[country].values[0]
  # minus last price
  last_month_value = decimal.Decimal(last_value) - decimal.Decimal(last_month_value)
  last_month_value = round(last_month_value, 2)

  #3m
  rd = relativedelta(months=+3)
  last_3_months_date = last_date - rd

  df_last_3_months = util_return_date_values(df_series,last_3_months_date)
  try:
    last_3_months_value = df_last_3_months[country].values[0]
    # minus last price
    last_3_months_value = decimal.Decimal(last_value) - decimal.Decimal(last_3_months_value)
    last_3_months_value = round(last_3_months_value, 2)
  except IndexError as e:
     last_3_months_value = None

  #ytd   
  year_first_day = date(date.today().year, 1, 1)
  df_ytd = util_return_date_values(df_series,year_first_day)
  try:
    ytd_value = df_ytd[country].values[0]
    # minus last price
    ytd_value = decimal.Decimal(last_value) - decimal.Decimal(ytd_value)
    ytd_value = round(ytd_value, 2)
  except IndexError as e:
    ytd_value = None

  #yoy
  rd = relativedelta(years=+1)
  yoy_date = last_date - rd
  df_yoy = util_return_date_values(df_series,yoy_date)
  yoy_value = df_yoy[country].values[0]
  # minus last price
  yoy_value = decimal.Decimal(last_value) - decimal.Decimal(yoy_value)
  yoy_value = round(yoy_value, 2)

  # create and return df with values
  data = {'Country': [],'Last Date': [],'Last': [],'1w': [],'1m': [],'3m': [],'YTD': [],'YoY': []}

  # Convert the dictionary into DataFrame
  df_country_ir = pd.DataFrame(data)

  temp_row = [country,last_date,last_value,last_5_days_value,last_month_value,last_3_months_value,ytd_value,yoy_value]
  df_country_ir.loc[len(df_country_ir.index)] = temp_row

  return df_country_ir

# Set Credit Rating Data from Trading Economics
def set_country_credit_rating(logger):
  success = False

  #Get World Production Data
  df_country_credit_rating = scrape_table_country_rating("https://tradingeconomics.com/country-list/rating")

  # Write to database
  rename_cols = {
    "Country": "country",    
    "Moodys":"Moodys",     
    "DBRS":"dbrs",
    "S&P":"s_and_p"
  }
  try:
    #Clear out old data
    sql_delete_all_rows('Macro_CountryRatings')
    success = sql_write_df_to_db(df_country_credit_rating, "Macro_CountryRatings",rename_cols=rename_cols)
    logger.info(f'Successfully Downloaded Company Credit Ratings')     
  except Exception as e:
    logger.error(f'Failed to download Company Credit Ratings')     

  return success

def get_invest_data_manual_scrape(country_list, bond_year):

  data = {'DATE': []}

  # Convert the dictionary into DataFrame
  df_invest_data = pd.DataFrame(data)

  for country in country_list:
    print("Getting %s-y data for: %s" % (bond_year,country))
    
    url = "https://www.investing.com/rates-bonds/%s-%s-year-bond-yield-historical-data" % (country,bond_year)

    print("Getting URL: %s" % (url))

    df_country_rates = return_selenium_rates_table_to_df(url)

    if(len(df_country_rates) == 0):
      url = "https://www.investing.com/rates-bonds/%s-%s-year-historical-data" % (country,bond_year)
      df_country_rates = return_selenium_rates_table_to_df(url)

    if(len(df_country_rates) == 0):
      url = "https://www.investing.com/rates-bonds/%s-%s-years-bond-yield-historical-data" % (country,bond_year)
      df_country_rates = return_selenium_rates_table_to_df(url)

    try:
        df_country_rates = df_country_rates.drop(['Open', 'High', 'Low', 'Change %'], axis=1)
        df_country_rates['Date'] = pd.to_datetime(df_country_rates['Date'],format='%m/%d/%Y')
        df_country_rates = df_country_rates.rename(columns={"Date": "DATE","Price": country})
        df_country_rates[country] = pd.to_numeric(df_country_rates[country])
        df_invest_data = combine_df_on_index(df_invest_data, df_country_rates, 'DATE')

    except KeyError as e:
        print("======================================%s DOES NOT EXIST=======================================" % country)
        print("======================================%s DOES NOT EXIST=======================================" % url)

  return df_invest_data.drop_duplicates()


def return_selenium_rates_table_to_df(url):
  #import pdb; pdb.set_trace() #Need to check that the URL is getting the data
  page = get_page_selenium(url)
  soup = BeautifulSoup(page, 'html.parser')
  #import pdb; pdb.set_trace()

  table = soup.find_all('table')[0]
  df = convert_html_table_to_df(table, False)

  return df

def scrape_table_country_rating(url):
    #import pdb; pdb.set_trace()
    page = get_page(url)

    soup = BeautifulSoup(page.content, 'html.parser')

    #TODO: Need to scrape table for world production countries and numbers.
    table = soup.find('table')

    table_rows = table.find_all('tr', recursive=False)
    #table_rows = table.find_all('tr', attrs={'class':'an-estimate-row'})
    table_rows_header = table.find_all('tr')[0].find_all('th')
    df = pd.DataFrame()
    index = 0
    for header in table_rows_header:
        if(index == 0):
            df.insert(0,"Country",[],True)
        else:
            df.insert(index,str(header.text).strip().replace("'", ""),[],True)
        index+=1

    #Get rows of data.
    for tr in table_rows:
        temp_row = []
        #first_col = True
        index = 0
        td = tr.find_all('td')

        if(td):        
            for obs in td:
                text = str(obs.text).strip()
                temp_row.append(text)        
                index += 1

            df.loc[len(df.index)] = temp_row

    df = df.drop(['TE'], axis=1)
    return df


def set_us_treasury_yields(logger):
  success = False
  filename = '013_Daily_Treasury_Yields.xml'

  todays_date = date.today()
  date_str = "%s%s" % (todays_date.strftime('%Y'), todays_date.strftime('%m'))

  url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value_month=%s" % (date_str,)

  #xml_file_path = "%s/data/xml/%s" % (sys.path[0],filename)
  partial_file_path = "data/xml/%s" % (filename,)

  if(isWindows):
    filepath = os.getcwd()
    temp_file_path = "%s/%s" % (filepath,partial_file_path)
    full_file_path = temp_file_path.replace("/","\\")

  try:
      resp = requests.get(url=url)

      resp_formatted = resp.text[resp.text.find('<'):len(resp.text)]
      # Write response to an XML File
      with open(full_file_path, 'w') as f:
          f.write(resp_formatted)

  except requests.exceptions.ConnectionError:
      print("Connection refused, Opening from File...")

  # Load in the XML file into ElementTree
  tree = ET.parse(full_file_path)
  data = {'dt': [], 'rate3m':[], 'rate2y': [], 'rate3y': [], 'rate10y': [], 'rate30y': []}
  df_us_treasury_yields = pd.DataFrame(data=data)

  #Load into a dataframe and return the data frame
  root = tree.getroot()

  ns = {'ty': 'http://www.w3.org/2005/Atom'}

  # <class 'xml.etree.ElementTree.Element'>
  for content in root.findall('./ty:entry/ty:content',ns):
    temp_row = []

    for elem in content.iter():
      #Check if current tag is the date, 30y, 10y, 2y or 3y
      if(elem.tag.__contains__("NEW_DATE")|elem.tag.__contains__("BC_3MONTH")|elem.tag.__contains__("BC_2YEAR")|elem.tag.__contains__("BC_3YEAR")|elem.tag.__contains__("BC_10YEAR")|elem.tag.__contains__("BC_30YEARDISPLAY")):
        temp_row.append(elem.text)        

    try:
      df_us_treasury_yields.loc[len(df_us_treasury_yields.index)] = temp_row
      logger.info(f'Rates: {temp_row}')     
    except ValueError as e:
      logger.error(f'Cound not append row {temp_row}')
    #print(elem.tag)
    #print(elem.text)

  # format columns
  df_us_treasury_yields['dt'] = pd.to_datetime(df_us_treasury_yields['dt'],format='%Y-%m-%d')
  df_us_treasury_yields['rate3m'] = pd.to_numeric(df_us_treasury_yields['rate3m'])
  df_us_treasury_yields['rate2y'] = pd.to_numeric(df_us_treasury_yields['rate2y'])
  df_us_treasury_yields['rate3y'] = pd.to_numeric(df_us_treasury_yields['rate3y'])
  df_us_treasury_yields['rate10y'] = pd.to_numeric(df_us_treasury_yields['rate10y'])
  df_us_treasury_yields['rate30y'] = pd.to_numeric(df_us_treasury_yields['rate30y'])

  # Write to database
  try:
    rename_cols = {}
    #add_col_values = {}
    #conflict_cols = "dt"

    success = sql_write_df_to_db(df_us_treasury_yields, "Macro_USTreasuryYields",rename_cols=rename_cols)
    logger.info(f'Successfully Downloaded US Treasury Yields for: {date_str}')     
  except Exception as e:
    logger.error(f'Could not download US Treasury Yields for: {date_str}')     

  return success
#  return df_us_treasury_yields

def ema_signal(df, current_candle, backcandles):
  df_slice = df.reset_index().copy()
  # Get the range of candles to consider
  start = max(0, current_candle - backcandles)
  end = current_candle
  relevant_rows = df_slice.iloc[start:end]

  # Check if all EMA_fast values are below EMA_slow values
  if all(relevant_rows["EMA_fast"] < relevant_rows["EMA_slow"]):
      return 1
  elif all(relevant_rows["EMA_fast"] > relevant_rows["EMA_slow"]):
      return 2
  else:
      return 0
    

def total_signal(df, current_candle, backcandles):
  if (ema_signal(df, current_candle, backcandles)==2
      and df.Close[current_candle]<=df['BBL_15_1.5'][current_candle]
      #and df.RSI[current_candle]<60
      ):
          return 2
  if (ema_signal(df, current_candle, backcandles)==1
      and df.Close[current_candle]>=df['BBU_15_1.5'][current_candle]
      #and df.RSI[current_candle]>40
      ):
  
          return 1
  return 0


def pointpos_ema(x):
  if x['TotalSignal']==2:
      return x['Low']-1e-3
  elif x['TotalSignal']==1:
      return x['High']+1e-3
  else:
      return np.nan

#TODO: Run this, and use to find signals in recent data
def plot_ticker_signals_ema(ticker, logger):

  filename = "{}.csv".format(ticker)

  df = pd.read_csv('data/daily_prices/{}'.format(filename))

  #Replace with getting data from file
  #df = pd.read_csv("EURUSD_Candlestick_5_M_ASK_30.09.2019-30.09.2022.csv")

  #df["Gmt time"]=df["Gmt time"].str.replace(".000","")
  df['Date']=pd.to_datetime(df['Date'],format='%Y-%m-%d')
  df=df[df.High!=df.Low]
  df.set_index("Date", inplace=True)  

  df["EMA_slow"]=ta.ema(df.Close, length=50)
  df["EMA_fast"]=ta.ema(df.Close, length=30)
  df['RSI']=ta.rsi(df.Close, length=10)
  my_bbands = ta.bbands(df.Close, length=15, std=1.5)
  df['ATR']=ta.atr(df.High, df.Low, df.Close, length=7)
  df=df.join(my_bbands)

  df=df[-10000:-1]
  tqdm.pandas()
  df.reset_index(inplace=True)
  df['EMASignal'] = df.progress_apply(lambda row: ema_signal(df, row.name, 7) , axis=1) #if row.name >= 20 else 0
  df['TotalSignal'] = df.progress_apply(lambda row: total_signal(df, row.name, 7), axis=1)
  df[df.TotalSignal != 0].head(20)
  df['pointpos'] = df.apply(lambda row: pointpos_ema(row), axis=1)
  #import pdb; pdb.set_trace()
  #st=100
  fin = len(df)
  st = fin - 100
  dfpl = df[st:fin]
  x_index = dfpl['Date']
  #x_index = dfpl.index
  #dfpl.reset_index(inplace=True)
  fig = go.Figure(data=[go.Candlestick(x=x_index,
                  open=dfpl['Open'],
                  high=dfpl['High'],
                  low=dfpl['Low'],
                  close=dfpl['Close']), 

                  go.Scatter(x=x_index, y=dfpl['BBL_15_1.5'], 
                            line=dict(color='green', width=1), 
                            name="BBL"),
                  go.Scatter(x=x_index, y=dfpl['BBU_15_1.5'], 
                            line=dict(color='green', width=1), 
                            name="BBU"),
                  go.Scatter(x=x_index, y=dfpl['EMA_fast'], 
                            line=dict(color='black', width=1), 
                            name="EMA_fast"),
                  go.Scatter(x=x_index, y=dfpl['EMA_slow'], 
                            line=dict(color='blue', width=1), 
                            name="EMA_slow")])

  fig.add_scatter(x=x_index, y=dfpl['pointpos'], mode="markers",
                  marker=dict(size=10, color="MediumPurple"),
                  name="entry")
  
  fig.update_yaxes(nticks=10)
  fig.update_xaxes(tickangle = 90)
  fig.update_layout(
    autosize=False,
    width=config.PLOTLY_CHART_WIDTH,
    height=config.PLOTLY_CHART_HEIGHT,
  )

  return fig

def TotalSignalVWAP(l, df):
    if (df.VWAPSignal[l]==2
        and df.Close[l]<=df['BBL_14_2.0'][l]
        and df.RSI[l]<45):
            return 2
    if (df.VWAPSignal[l]==1
        and df.Close[l]>=df['BBU_14_2.0'][l]
        and df.RSI[l]>55):
            return 1
    return 0

def pointposbreak_vwap(x):
    if x['TotalSignal']==1:
        return x['High']+1e-4
    elif x['TotalSignal']==2:
        return x['Low']-1e-4
    else:
        return np.nan

def plot_ticker_signals_vwap(ticker, logger):

  filename = "{}.csv".format(ticker)

  df = pd.read_csv('data/daily_prices/{}'.format(filename))

  df['Date']=pd.to_datetime(df['Date'],format='%Y-%m-%d')
  df=df[df.High!=df.Low]
  df.set_index("Date", inplace=True)  

  df["VWAP"]=ta.vwap(df.High, df.Low, df.Close, df.Volume)
  df['RSI']=ta.rsi(df.Close, length=16)
  my_bbands = ta.bbands(df.Close, length=14, std=2.0)
  df=df.join(my_bbands)

  VWAPsignal = [0]*len(df)
  backcandles = 15

  for row in range(backcandles, len(df)):
      upt = 1
      dnt = 1
      for i in range(row-backcandles, row+1):
          if max(df.Open[i], df.Close[i])>=df.VWAP[i]:
              dnt=0
          if min(df.Open[i], df.Close[i])<=df.VWAP[i]:
              upt=0
      if upt==1 and dnt==1:
          VWAPsignal[row]=3
      elif upt==1:
          VWAPsignal[row]=2
      elif dnt==1:
          VWAPsignal[row]=1

  df['VWAPSignal'] = VWAPsignal

  TotSignal = [0]*len(df)
  for row in range(backcandles, len(df)): #careful backcandles used previous cell
      TotSignal[row] = TotalSignalVWAP(row,df)
  df['TotalSignal'] = TotSignal

  print(df[df.TotalSignal!=0].count())
    
  df['pointposbreak'] = df.apply(lambda row: pointposbreak_vwap(row), axis=1)

  fin = len(df)
  st = fin - 100
  dfpl = df[st:fin]

  x_index = dfpl.index

  dfpl.reset_index(inplace=True)
  fig = go.Figure(data=[go.Candlestick(x=x_index,
                  open=dfpl['Open'],
                  high=dfpl['High'],
                  low=dfpl['Low'],
                  close=dfpl['Close']),
                  go.Scatter(x=x_index, y=dfpl.VWAP, 
                            line=dict(color='blue', width=1), 
                            name="VWAP"), 
                  go.Scatter(x=x_index, y=dfpl['BBL_14_2.0'], 
                            line=dict(color='green', width=1), 
                            name="BBL"),
                  go.Scatter(x=x_index, y=dfpl['BBU_14_2.0'], 
                            line=dict(color='green', width=1), 
                            name="BBU")])

  fig.add_scatter(x=x_index, y=dfpl['pointposbreak'], mode="markers",
                  marker=dict(size=10, color="MediumPurple"),
                  name="Signal")
  #fig.show()

  fig.update_yaxes(nticks=10)
  fig.update_xaxes(tickangle = 90)
  fig.update_layout(
    autosize=False,
    width=config.PLOTLY_CHART_WIDTH,
    height=config.PLOTLY_CHART_HEIGHT,
  )

  return fig


##TODO: KEY LEVELS HISTOGRAM

def pivotid(df1, l, n1, n2): #n1 n2 before and after candle l
  if l-n1 < 0 or l+n2 >= len(df1):
      return 0
  
  pividlow=1
  pividhigh=1
  for i in range(l-n1, l+n2+1):
      if(df1.Low[l]>df1.Low[i]):
          pividlow=0
      if(df1.High[l]<df1.High[i]):
          pividhigh=0
  if pividlow and pividhigh:
      return 3
  elif pividlow:
      return 1
  elif pividhigh:
      return 2
  else:
      return 0
    

def pointpos_key_levels(x):
  if x['pivot']==1:
      return x['Low']-1e-3
  elif x['pivot']==2:
      return x['High']+1e-3
  else:
      return np.nan
  

def plot_ticker_signals_histogram(ticker, logger):

  filename = "{}.csv".format(ticker)

  df = pd.read_csv('data/daily_prices/{}'.format(filename))
  df['Date']=pd.to_datetime(df['Date'],format='%Y-%m-%d')
  df=df[df.High!=df.Low]
  df=df[df['Volume']!=0]
  df.reset_index(drop=True, inplace=True)

  df['pivot'] = df.apply(lambda x: pivotid(df, x.name,10,10), axis=1)
  df['pointpos'] = df.apply(lambda row: pointpos_key_levels(row), axis=1)

  dfpl = df[-300:-1]
  x_index = dfpl['Date']
  fig = go.Figure(data=[go.Candlestick(x=x_index,
                  open=dfpl['Open'],
                  high=dfpl['High'],
                  low=dfpl['Low'],
                  close=dfpl['Close'],
                  increasing_line_color= 'green', 
                  decreasing_line_color= 'red')])

  fig.add_scatter(x=x_index, y=dfpl['pointpos'], mode="markers",
                  marker=dict(size=5, color="MediumPurple"),
                  name="pivot")
  fig.update_layout(xaxis_rangeslider_visible=False)
  fig.update_xaxes(showgrid=False)
  fig.update_yaxes(showgrid=False)
  fig.update_layout(
    paper_bgcolor='black', 
    plot_bgcolor='black',
    autosize=False,
    width=config.PLOTLY_CHART_WIDTH,
    height=config.PLOTLY_CHART_HEIGHT,
  )

  #fin = len(df)
  #st = fin - 100
  #dfkeys = df[st:fin]

  dfkeys = df[:]

  # Filter the dataframe based on the pivot column
  high_values = dfkeys[dfkeys['pivot'] == 2]['High']
  low_values = dfkeys[dfkeys['pivot'] == 1]['Low']

  # Define the bin width
  bin_width = config.HISTOGRAM_BIN_SIZE  # Change this value as needed

  # Calculate the number of bins
  bins = int((high_values.max() - low_values.min()) / bin_width)

  # Create the histograms
  plt.figure(figsize=(10, 5))
  plt.hist(high_values, bins=bins, alpha=0.5, label='High Values', color='red')
  plt.hist(low_values, bins=bins, alpha=0.5, label='Low Values', color='blue')

  plt.xlabel('Value')
  plt.ylabel('Frequency')
  plt.title('Histogram of High and Low Values')
  plt.legend()

  return fig, plt

def set_report_data():

  list_of_files = glob.glob('data/trading_reports/*') # * means all if need specific format then *.csv
  latest_file = max(list_of_files, key=os.path.getctime)
  latest_file = latest_file.split('\\')[1]

  df = pd.read_csv('data/trading_reports/{}'.format(latest_file), header=None, names=range(17))

  # Strip out all rows except Trades
  df1 = df.loc[df[0] == 'Trades']
  df2 = df1.drop(df.columns[[0,1,2,3,4,7,9,10,11,13, 14, 15,16]],axis = 1)
  df3 = df2.loc[df[12] != '0']

  df3.columns = df3.iloc[0]
  df3 = df3[1:]
  #In case there is another row containing the header
  df3.drop(df3[df3['Symbol'] == 'Symbol'].index, inplace = True)
  df3['T. Price'] = pd.to_numeric(df3['T. Price'])
  df3['Realized P/L'] = pd.to_numeric(df3['Realized P/L'])

  df4 = df3.loc[df3['T. Price'].notna()]
  df4 = df4.drop('T. Price', axis=1)

  # Format Datetime field
  df4['Date/Time'] = pd.to_datetime(df4['Date/Time'],format='%Y-%m-%d, %H:%M:%S')
  # Rename columns to remove /
  #df4 = df4.rename(columns={"Date/Time": "Date_Time", "Realized P/L": "Realized_PL"})
  df4.sort_values(by='Date/Time', inplace = True)
  df4 = df4.reset_index(drop=True)
  df4 = df4.rename_axis(None, axis=1)
  df4[['asset']] = df4['Symbol'].str.extract('(^[A-Z]*)', expand=True)

  # write records to database
  rename_cols = {"Date/Time": "date_time", "Realized P/L": "realized_pl"}
  add_col_values = {}
  conflict_cols = "Symbol"

  success = sql_write_df_to_db(df4, "Trading_Report", rename_cols, add_col_values, conflict_cols)

  return success

def get_report_data():

  # TODO: Return all rows from database
  df_report_data = get_data(table="trading_report").reset_index(drop=True)
  total = None
  try:
    df_report_data['realized_pl'] = pd.to_numeric(df_report_data['realized_pl'])

    # Format Datetime field
    df_report_data['date_time'] = pd.to_datetime(df_report_data['date_time'],format='%Y-%m-%d')
    
    total = df_report_data['realized_pl'].sum().round(2)

    df_report_data = df_report_data.groupby(["asset","date_time"])['realized_pl'].sum().reset_index(name ='realized_pl').sort_values(by=['date_time'], ascending=True) 
    df_report_data['realized_pl'] = df_report_data.realized_pl.round(2)
  except KeyError as e:
     pass

  return df_report_data, total
