import streamlit as st 
from pandas import DataFrame
from gspread_pandas import Spread,Client
from google.oauth2 import service_account

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes = scope)
client = Client(scope=scope,creds=credentials)
spreadsheetname = "Database"
spread = Spread(spreadsheetname,client = client)

# Check the connection
st.write(spread.url)
