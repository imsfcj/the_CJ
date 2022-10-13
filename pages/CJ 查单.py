import streamlit as st
import sqlite3, os, time, re, pytz, json, ssl
from io import BytesIO
#from pyxlsb import open_workbook as open_xlsb
import pandas as pd
from datetime import datetime, timedelta
import urllib.request, urllib.parse, urllib.error

tz = pytz.timezone('America/Toronto')
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

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

st.set_page_config(page_title='CJ 查单助手',page_icon = "🛐" ,initial_sidebar_state = 'expanded', layout="wide")

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

st.sidebar.image('./pages/setup/images/aba_icon2.jpg', width=100)
st.sidebar.title("程序运行详情")

con = sqlite3.connect('./pages/setup/data/sql/查单.sqlite')
cur = con.cursor()
cur.executescript('''
DROP TABLE IF EXISTS Trans_List;
CREATE TABLE IF NOT EXISTS Trans_List (
    '单号' TEXT,
    '子批次' TEXT,
    '当前司机号' TEXT,
    '当前状态' TEXT,
    '更新时间' TEXT,
    '映射' INTEGER,
    '主单号' TEXT
)
''')
con.commit()

conn = sqlite3.connect('./pages/setup/data/sql/postcode.sqlite')
curr = conn.cursor()
curr.executescript('''
DROP TABLE IF EXISTS Post_List;
CREATE TABLE IF NOT EXISTS Post_List (
    'id' INTEGER,
    'route_no' INTEGER,
    'zipcode' TEXT,
    'sorting_zone' INTEGER,
    'price' TEXT,
    'city' INTEGER,
    'area' TEXT,
    'segment' TEXT,
    'owner' TEXT,
    'is_remote' INTEGER,
    'is_enabled' INTEGER,
    'pattern_id' INTEGER
)
''')
conn.commit()
df = pd.read_excel('./pages/setup/data/important/post.xlsx')
df.to_sql('Post_List', conn, if_exists='replace', index=False)
conn.commit()

form1 = st.form(key="Options")
main_container = st.container()
main_container.write("")
form1.title("查单助手")
text = form1.text_area("请直接输入查单单号： ")
bt1 = form1.form_submit_button("开始 查单")

cllm1,cllm2,cllm3,cllm4,cllm5,cllm6 = st.columns(6)
cllm1.subheader("单号")
cllm2.subheader("子批次")
cllm3.subheader("当前司机号")
cllm4.subheader("当前状态")
cllm5.subheader("更新时间")
cllm6.subheader("映射")
cll1,cll2,cll3,cll4,cll5,cll6 = st.columns(6)

if bt1 :
    st.sidebar.write('\n -----     准备中     ----- ')
    my_bar = main_container.progress(0)
    h = text.split('\n')
    percent_complete = 1 / len(h)
    #percent_complete = round(percent_complete,1)
    x = 0
    url_head = 'https://map.cluster.uniexpress.org/map/getorderdetail?tno='
    for line in h :
        if len(line) <= 4 : continue
        url = url_head + line
        uh = urllib.request.urlopen(url, context=ctx)
        data = uh.read().decode()
        js = json.loads(data)
        if js['status'] == 'SUCCESS' :
            tracking_number = js['data']['tracking']['tno']
            sub_batch = js['data']['orders']['sub_referer']
            main_batch = js['data']['tracking']['reference']
            driver_id = js['data']['orders']['shipping_staff_id']
            current_stat = js['data']['orders']['latest_status']
            three_post = js['data']['orders']['zipcode'][:3]
            try:
                pot = curr.execute('SELECT route_no FROM Post_List WHERE zipcode = ?',(three_post,)).fetchone()[0]
                conn.commit()
            except: pot = 'N/A'

            if current_stat == '190' : the_time = datetime.fromtimestamp(js['data']['orders']['latest_update_time']).strftime("%Y-%m-%d %H:%M:%S")
            else :
                the_time = datetime.fromtimestamp(js['data']['orders']['latest_update_time'])
                the_time = the_time.strftime("%Y-%m-%d %H:%M:%S")
        else :
            tracking_number = line
            sub_batch = 'N/A'
            driver_id = 'N/A'
            current_stat = 'N/A'
            the_time = 'N/A'
            pot = 'N/A'
        cur.execute("INSERT INTO Trans_List (单号,子批次,当前司机号,当前状态,更新时间,映射,主单号) VALUES (?,?,?,?,?,?,?)",(tracking_number,sub_batch,driver_id,current_stat,the_time,pot,main_batch))
        con.commit()
        cll1.write(tracking_number)
        cll2.write(sub_batch)
        cll3.write(str(driver_id))
        cll4.write(str(current_stat))
        cll5.write(the_time)
        cll6.write(pot)
        x = x + percent_complete
        my_bar.progress(x)

    rq = '''
    SELECT * FROM Trans_List
    '''
    df = pd.read_sql (rq, con)
    df_xlsx = to_excel(df)
    main_container.download_button(label='📥 下载查单信息',
                                    data=df_xlsx ,
                                    file_name= 'Tno_Info.xlsx')
