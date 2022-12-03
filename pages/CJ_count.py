# streamlit_app.py

import streamlit as st
import gspread
from gspread.models import Cell, Spreadsheet
from google.oauth2 import service_account
from gsheetsdb import connect

# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)
conn = connect(credentials=credentials)

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

new_week = gspread.authorize(credentials)
new_week.copy("1U9AtBpN1BJweufhofeyYBMtcfg3uEbdGh7TEJ89O95c", title="asd", copy_permissions=True)
