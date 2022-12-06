import streamlit as st 
from pandas import DataFrame
from gspread_pandas import Client
from google.oauth2 import service_account

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes = scope)
client = Client(scope=scope,creds=credentials)
spreadsheetname = "司机一周统计表"
spreadsheet = client.open(spreadsheetname)

# Check the connection
st.write(spreadsheet.url)

the_new = st.button('new')
if the_new :
    old_title = "template"
    new_title = "the_new_sheet"
    index = 1  # Insert the new sheet at index 1
    client.duplicate_sheet(spreadsheet, old_title, new_title, index)
