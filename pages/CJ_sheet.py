import streamlit as st 
from pandas import DataFrame
from gspread_pandas import Spread,Client
from google.oauth2 import service_account

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes = scope)
client = Client(scope=scope,creds=credentials)
spreadsheetname = "司机一周统计表"
spread = Spread(spreadsheetname,client = client)

# Check the connection
st.write(spread.url)

sh = client.open(spreadsheetname)

the_new = st.button('new')
if the_new :
    the_sheets = sh.worksheet('template')
    worksheet_id = the_sheets.id
    sh.duplicate_sheet(worksheet_id, "New Sheet Name", insert_sheet_index=none, new_sheet_id=none)

