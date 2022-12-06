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
    worksheets = sh.worksheets()
    worksheet_to_duplicate = worksheets[0]
    worksheet_id = worksheet_to_duplicate.id
    insert_sheet_index = 1
    sh.duplicate_sheet(worksheet_id, "New Sheet Name", insert_sheet_index)

