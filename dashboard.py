import streamlit as st
import pandas as pd
import numpy as np
import requests
import config 
from matplotlib import pyplot as plt
import glob
import os
import json
from datetime import date
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

pd.options.mode.chained_assignment = None #Switch off warning

st.set_page_config(
    page_title="Stock Screener App",
    page_icon=":shark:",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

#TODO: Set Page Layout: https://www.youtube.com/watch?v=0AhG53TCezg

#Dates
todays_date = date.today()
date_str_today = "%s-%s-%s" % (todays_date.year, todays_date.month, todays_date.day)
date_str_start = "2007-01-01"

one_year_ago = dt(todays_date.year - 1, 12, 31)
two_year_ago = dt(todays_date.year - 2, 12, 31)
three_year_ago = dt(todays_date.year - 3, 12, 31)
list_dates = []
list_dates.append(one_year_ago)
list_dates.append(two_year_ago)
list_dates.append(three_year_ago)

#https://www.youtube.com/watch?v=0ESc1bh3eIg&list=WL&index=16&t=731s

#list_of_files = glob.glob('data/*.csv',) # * means all if need specific format then *.csv
#latest_zacks_file = max(list_of_files, key=os.path.getctime)
#latest_zacks_file = latest_zacks_file.replace("data\\", "")

st.markdown(f'''
    <style>
        section[data-testid="stSidebar"] .css-ng1t4o {{width: 14rem;}}
        section[data-testid="stSidebar"] .css-1d391kg {{width: 14rem;}}
    </style>
''',unsafe_allow_html=True)

option = st.sidebar.selectbox("Which Option?", ('Download Data','Market Data','Macroeconomic Data','Calendar', 'Single Stock One Pager','ATR Calculator', 'Bottom Up Ideas', 'Trading Report'), 2)

st.header(option)

if option == 'Download Data':

    #num_days = st.sidebar.slider('Number of days', 1, 30, 3)
    clicked1 = st.markdown("Download Economic Calendar Data (takes 15 minutes)")
    clicked1 = st.button(label="Click to Download Economic Calendar Data",key="economic_cal_data")

    clicked2 = st.markdown("Download Stock Data (takes 2 hours)")
    clicked2 = st.button(label="Click to Download Stock Data", key="stock_data")

    clicked3 = st.markdown("Download Stock Row Data (takes 6 hours)")
    clicked3 = st.button(label="Click to Download Stock Row Data", key="stock_row_data")

    clicked4 = st.markdown("Download Macroeconomic Data (takes 1 hour)")
    clicked4 = st.button(label="Click to Download Macroeconomic Data", key="macro_data")

    if(clicked1):
       pass

    if(clicked2):
       pass

    if(clicked3):
        pass

    if(clicked4):
        pass
if option == 'Calendar':
    pass

if option == 'Market Data':
    pass

if option == 'Macroeconomic Data':
    pass