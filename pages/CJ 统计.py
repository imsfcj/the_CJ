import streamlit as st 
from datetime import date, timedelta, datetime
import sqlite3, os, time, re, pytz
from pytz import timezone
from io import BytesIO
import pandas as pd
from pandas import DataFrame
from gspread_pandas import Spread,Client
from google.oauth2 import service_account
from gsheetsdb import connect
from collections import defaultdict

st.set_page_config(page_title='CJ 统计司机助手',page_icon = "🛐" ,initial_sidebar_state = 'expanded')
m = st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #b5a2c8;
    color:#ffffff;
}
div.stButton > button:hover {
    background-color: #C8A2C8;
    color:#ff0000;
    }
</style>""", unsafe_allow_html=True)

st.sidebar.image('./pages/setup/images/aba_icon6.jpg', width=100)
st.sidebar.title("程序运行详情")

con = sqlite3.connect('./pages/setup/data/sql/schedule.sqlite')
cur = con.cursor()
cur.executescript('''
DROP TABLE IF EXISTS Driver_List;
DROP TABLE IF EXISTS All_List;
DROP TABLE IF EXISTS Area_List;
DROP TABLE IF EXISTS Import_List;
CREATE TABLE Driver_List (
    Driver INTEGER,
    Area TEXT,
    Warehouse INTEGER
);
CREATE TABLE All_List (
    Driver TEXT,
    Location TEXT,
    WH INTEGER,
    Mon INTEGER,
    Tue INTEGER,
    Wed INTEGER,
    Thu INTEGER,
    Fri INTEGER,
    Sat INTEGER,
    Sun INTEGER,
    Origin TEXT
)
''')
con.commit()
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
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

for dri,are in alist.items():
    cur.execute("INSERT INTO Driver_List (Driver,Area) VALUES (?,?)",(dri,are))
    con.commit()

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, encoding='utf-8-sig', index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0'})
    worksheet.set_column('A:A', None, format1)
    writer.save()
    processed_data = output.getvalue()
    return processed_data
    
toronto_timezone = timezone('America/Toronto')   
now = datetime.now(tz=toronto_timezone)
today = now.date()
tomorrow = today + timedelta(days=1)
tmr_str = tomorrow.strftime('%b%d_%a')
the_day = today.strftime('%a')
if the_day == 'Mon' : the_pick = 1
if the_day == 'Tue' : the_pick = 2
if the_day == 'Wed' : the_pick = 3
if the_day == 'Thu' : the_pick = 4
if the_day == 'Fri' : the_pick = 5
if the_day == 'Sat' : the_pick = 6
if the_day == 'Sun' : the_pick = 0
#st.write(today_str)


# Get the day of the week (1-7, where 1 is Monday and 7 is Sunday)
day_of_week = today.isoweekday()

# Calculate the starting and ending dates of the week
start_of_week = today - timedelta(days=day_of_week - 1)
end_of_week = today + timedelta(days=7 - day_of_week)

dates = {}

# Loop through each day of the week
for i in range(7):
    # Calculate the date for the current day
    date = start_of_week + timedelta(days=i)

    # Get the day of the week as a string (Monday, Tuesday, etc.)
    day_of_week_str = date.strftime("%a")

    # Add the date to the dictionary
    dates[day_of_week_str] = date.strftime("%b%d_%a")

# Print the starting and ending dates
this_week = "{}-{}".format(start_of_week.strftime("%b%d"), end_of_week.strftime("%b%d"))
#st.write(this_week)

next_week = today + timedelta(days=7)

# Get the day of the week (1-7, where 1 is Monday and 7 is Sunday)
day_of_week = next_week.isoweekday()

# Calculate the starting and ending dates of the week
start_of_week = next_week - timedelta(days=day_of_week - 1)
end_of_week = next_week + timedelta(days=7 - day_of_week)

# Print the starting and ending dates
next_week = "{}-{}".format(start_of_week.strftime("%b%d"), end_of_week.strftime("%b%d"))
#st.write(next_week)

st.title("统计司机助手")
tab1,tab2 = st.tabs(["每日统计","一周统计"])    
form1 = tab1.form(key="Options")
form1.header("统计每日司机")
form1.subheader(f"本周为：{this_week}")
choice = form1.selectbox("想统计哪一天的司机报名情况？",('Mon','Tue','Wed','Thu','Fri','Sat','Sun'),index=the_pick)
main_container1 = tab1.container()
main_container1.write("")
bt1 = form1.form_submit_button("提交")
    
if bt1 :
    if choice == 'Mon' : this_week = next_week
    st.sidebar.write(f"日期：{dates[choice]}")
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = service_account.Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"], scopes = scope)
    client = Client(scope=scope,creds=credentials)
    spreadsheetname = "司机一周统计表"
    spread = Spread(spreadsheetname,client = client)
    sh = client.open(spreadsheetname)
    #
    df = spread.sheet_to_df(index=0,sheet=this_week)
    day_driver = df.loc[:, ['Driver', 'Location', choice]]
    count = dict()
    for index, row in day_driver.iterrows():
        if row[choice] != '1' : continue
        on_board = str(row['Driver'])
        the_area = row['Location'].upper().replace(' ','_')
        count[on_board]=the_area
    df = pd.DataFrame()
    for d,a in count.items() :
        df = df.append({a:d},ignore_index=True)
    df = df.apply(lambda x: pd.Series(x.dropna().values)).fillna(' ').dropna(axis=1, how='all')
    st.write(df)
    schedule_sheet = sh.worksheet('day_temp')
    schedule_sheet.duplicate(insert_sheet_index=None, new_sheet_id=None, new_sheet_name=dates[choice])
    spread.df_to_sheet(df,start=(1,1),sheet=dates[choice],index = False)
    st.sidebar.write('\n -----     统计完毕     ----- ')
    
form2 = tab2.form(key="Optionss")
form2.header("统计一周司机地区及取货时间")
form2.subheader(f"统计日期为：{next_week}")
alldrivers = form2.file_uploader("请在这里上传统计文件：", accept_multiple_files=True)
#englishdrivers = form2.file_uploader("请在这里上传Google Form：", accept_multiple_files=False)
bt2 = form2.form_submit_button("提交")
main_container2 = tab2.container()
main_container2.write("")
cm1,cm2 = tab2.columns(2)
cm1.subheader("司机号")
cm2.subheader("地区")


if bt2 :
    st.sidebar.write('\n -----     开始统计     ----- ')
    for uploaded_file in alldrivers:
        try :
            df = pd.read_excel(uploaded_file,sheet_name="物流列表",header=None,names=["driver","pickup_day"],skiprows=1,usecols="AD:AE", encoding="utf-8")
            #df = df[["driver","pickup_day"]]
            df.to_sql('Import_List', con, if_exists='append', index=False)
            con.commit()
        except :
            df = pd.read_csv(uploaded_file,header=None,names=["driver","pickup_day"],skiprows=1,usecols=[1,2])
            df.to_sql('Import_List', con, if_exists='append', index=False)
            con.commit()

    dlist = {}
    ddlist = {}
    cur.execute("SELECT * FROM Import_List")
    for row in cur :
        try :
            alterdriver = re.findall('[0-9][0-9][0-9][0-9]',row[0])[0]
        except :
            alterdriver = re.findall('[0-9][0-9][0-9]',row[0])[0]

        print(alterdriver)
        alterformat = row[1].replace(";",",")
        days = alterformat.split(',')
        dlist[alterdriver] = days
        ddlist[alterdriver] = row[0]

    for dri,dys in dlist.items():
        cur.execute("INSERT INTO All_List (Driver,Origin) VALUES (?,?)",(dri,ddlist[dri]))
        for day in dys :
            print(dri,day)
            if day == 'Mon' :
                cur.execute("UPDATE All_List SET Mon = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if re.findall('一',day) :
                cur.execute("UPDATE All_List SET Mon = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if day == 'Tue' :
                cur.execute("UPDATE All_List SET Tue = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if re.findall('二',day) :
                cur.execute("UPDATE All_List SET Tue = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if re.findall('We',day) :
                cur.execute("UPDATE All_List SET Wed = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if re.findall('三',day) :
                cur.execute("UPDATE All_List SET Wed = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if day == 'Thu' :
                cur.execute("UPDATE All_List SET Thu = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if re.findall('四',day) :
                cur.execute("UPDATE All_List SET Thu = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if day == 'Fri' :
                cur.execute("UPDATE All_List SET Fri = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if re.findall('五',day) :
                cur.execute("UPDATE All_List SET Fri = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if day == 'Sat' :
                cur.execute("UPDATE All_List SET Sat = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if re.findall('六',day) :
                cur.execute("UPDATE All_List SET Sat = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if day == 'Sun' :
                cur.execute("UPDATE All_List SET Sun = '1' WHERE Driver = ?",(dri,))
                con.commit()
            if re.findall('日',day) :
                cur.execute("UPDATE All_List SET Sun = '1' WHERE Driver = ?",(dri,))
                con.commit()


    dlist = {}
    wlist = {}
    cur.execute('SELECT * FROM All_List')
    for row in cur :
        dlist[row[0]] = 0
        wlist[row[0]] = 0

    for d,a in dlist.items() :
        cur.execute('Select * FROM Driver_List where Driver = ?', (d, ))
        for item in cur :
            dlist[d] = item[1]
            wlist[d] = item[2]

    for d,a in dlist.items() :
        cur.execute('UPDATE All_List SET Location = ?,WH = ? WHERE Driver = ?',(a,wlist[d],d,))
        con.commit()

    cur.execute("UPDATE All_List SET WH = NULL, Location = 'N/A' WHERE Location = '0'")
    con.commit()

    cur.execute("SELECT * FROM All_List")
    for row in cur :
        w = '你猜'
        if str(row[2]) == '202' : w = 'North York'
        if str(row[2]) == '895' : w = 'Mississauga'
        cm1.write(row[0])
        cm2.write(row[1])

    ctt = cur.execute("SELECT count(Driver) FROM All_List").fetchone()[0]
    st.sidebar.write('这周一共报名了',str(ctt),'个司机')

    rq = '''
    SELECT * FROM All_List ORDER BY Location
    '''
    df = pd.read_sql (rq, con)
    df_xlsx = to_excel(df)
    
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = service_account.Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"], scopes = scope)
    client = Client(scope=scope,creds=credentials)
    spreadsheetname = "司机一周统计表"
    spread = Spread(spreadsheetname,client = client)
    sh = client.open(spreadsheetname)
    the_sheets = sh.worksheet('template')
    the_sheets.duplicate(insert_sheet_index=None, new_sheet_id=None, new_sheet_name=next_week)
    spread.df_to_sheet(df,start=(1,1),sheet=next_week,index = False)
    
    
    main_container2.download_button(label='📥 下载每周司机统计信息',
                                    data=df_xlsx ,
                                    file_name= 'Driver_Info.xlsx')
    st.sidebar.write('\n -----     统计完毕     ----- ')
 















#
