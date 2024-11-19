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
from common import invoke_agent

pd.options.mode.chained_assignment = None #Switch off warning

st.set_page_config(
    page_title="ReAct Agent App",
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

st.markdown(f'''
    <style>
        section[data-testid="stSidebar"] .css-ng1t4o {{width: 14rem;}}
        section[data-testid="stSidebar"] .css-1d391kg {{width: 14rem;}}
    </style>
''',unsafe_allow_html=True)

option = st.sidebar.selectbox("Which Option?", ('Chat to Agent'), 0)

st.header(option)

if option == 'Chat to Agent':
    option_llm = st.selectbox(
        "Select LLM",
        ("gpt-4o-mini"),
    )

    option_prompt = st.selectbox(
        "Select Prompt",
        ("react"),
    )

    text_input = st.text_input(
        "Chat to Agent 👇"
    )

    if text_input:
        invoke_agent(st, option_llm, option_prompt, text_input)
     