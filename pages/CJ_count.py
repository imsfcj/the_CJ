# streamlit_app.py

import streamlit as st
from pandas import DataFrame
#from gspread_pandas import Spread,Client
from google.oauth2 import service_account
from gsheetsdb import connect

# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ],
)
conn = connect(credentials=credentials)

spreadsheetname = "司机一周统计表"
spread = Spread(spreadsheetname,client = client)
st.write(spread.url)

@st.cache(ttl=600)
def run_query(query):
    rows = conn.execute(query, headers=1)
    rows = rows.fetchall()
    return rows

sheet_url = st.secrets["private_gsheets_url"]
rows = run_query(f'SELECT * FROM "{sheet_url}"')

alist = {}
for row in rows:
    alist[row[0]] = row[1]
st.write(alist)

