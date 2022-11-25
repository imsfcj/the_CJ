import streamlit as st
import sqlite3, os, time, re, pytz, json, ssl, requests
from io import BytesIO
#from pyxlsb import open_workbook as open_xlsb
import pandas as pd
from datetime import datetime, timedelta
import urllib.request, urllib.parse, urllib.error

tz = pytz.timezone('America/Toronto')

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
    '主单号' TEXT,
    '仓库' INTEGER,
    '重量' TEXT,
    '邮编' TEXT
)
''')
con.commit()

conn = sqlite3.connect('./pages/setup/data/sql/postcode.sqlite')
curr = conn.cursor()
curr.executescript('''
DROP TABLE IF EXISTS Post_List;
CREATE TABLE IF NOT EXISTS Post_List (
    'id' INTEGER,
    'route_no' TEXT,
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

headers = {
    'authority': 'map.cluster.uniexpress.org',
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'access-control-allow-credentials': 'true',
    'access-control-allow-headers': 'Origin, X-Requested-With, Content-Type, Accept, origin, content-type, accept',
    'access-control-allow-methods': 'GET, PUT, POST, DELETE, OPTIONS',
    'access-control-allow-origin': '*',
    'authorization': 'Bearer null',
    'content-type': 'application/json;charset=UTF-8',
    'origin': 'https://unimap.cluster.uniexpress.org',
    'referer': 'https://unimap.cluster.uniexpress.org/',
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
}

params = {
    'username': 'jason_cj',
}

json_data = {
    'password': '16988',
}

responsee = requests.post('https://map.cluster.uniexpress.org/map/login', params=params, headers=headers, json=json_data)
jss = json.loads(responsee.content)

the_pas = 'Bearer ' +  jss['data']['token']

if bt1 :
    st.sidebar.write('\n -----     准备中     ----- ')
    my_bar = main_container.progress(0)
    h = text.split('\n')
    percent_complete = 1 / len(h)
    #percent_complete = round(percent_complete,1)
    x = 0
    #url_head = 'https://map.cluster.uniexpress.org/map/getorderdetail?tno='
    for line in h :
        if len(line) < 3 :
            cllm1.write(line)
            continue
        headers = {
            'authority': 'map.cluster.uniexpress.org',
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'access-control-allow-credentials': 'true',
            'access-control-allow-headers': 'Origin, X-Requested-With, Content-Type, Accept, origin, content-type, accept',
            'access-control-allow-methods': 'GET, PUT, POST, DELETE, OPTIONS',
            'access-control-allow-origin': '*',
            'authorization': the_pas,
            'origin': 'https://unimap.cluster.uniexpress.org',
            'referer': 'https://unimap.cluster.uniexpress.org/',
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        }

        #x = 'MBORDU7012624903'
        params = {
            'tno': line,
        }

        response = requests.get('https://map.cluster.uniexpress.org/map/getorderdetail', params=params, headers=headers)
        js = json.loads(response.content)
        if js['status'] == 'SUCCESS' :
            #st.write(js)
            tracking_number = js['data']['tracking']['tno']
            sub_batch = js['data']['orders']['sub_referer']
            main_batch = js['data']['tracking']['reference']
            driver_id = js['data']['orders']['shipping_staff_id']
            current_stat = js['data']['orders']['latest_status']
            three_post = js['data']['orders']['zipcode'][:3]
            the_house = js['data']['tracking']['warehouse']
            the_weight = js['data']['tracking']['total_weight']
            the_zip = js['data']['orders']['zipcode']
            try:
                pot = curr.execute('SELECT route_no FROM Post_List WHERE zipcode = ?',(three_post,)).fetchone()[0]
                conn.commit()
            except: pot = '0'

            if current_stat == '190' : the_time = datetime.fromtimestamp(js['data']['orders']['latest_update_time']).strftime("%Y-%m-%d %H:%M:%S")
            else :
                try :
                    the_time = datetime.fromtimestamp(js['data']['orders']['latest_update_time']) - timedelta(hours=3)
                    the_time = the_time.strftime("%Y-%m-%d %H:%M:%S")
                except : the_time = 'N/A'
        else :
            tracking_number = line
            sub_batch = 'N/A'
            driver_id = 'N/A'
            current_stat = 'N/A'
            the_time = 'N/A'
            pot = '0'
            the_house = '0'
            the_weight = 'N/A'
        cur.execute("INSERT INTO Trans_List (单号,子批次,当前司机号,当前状态,更新时间,映射,主单号,仓库,重量,邮编) VALUES (?,?,?,?,?,?,?,?,?,?)",(tracking_number,sub_batch,driver_id,current_stat,the_time,pot,main_batch,the_house,the_weight,the_zip))
        con.commit()
        cll1.write(tracking_number)
        cll2.write(sub_batch)
        cll3.write(str(driver_id))
        cll4.write(str(current_stat))
        cll5.write(the_time)
        cll6.write(pot)
        x = x + percent_complete
        if x >= 1 : x = 1
        my_bar.progress(x)

    rq = '''
    SELECT * FROM Trans_List
    '''
    df = pd.read_sql (rq, con)
    df_xlsx = to_excel(df)
    main_container.download_button(label='📥 下载查单信息',
                                    data=df_xlsx ,
                                    file_name= 'Tno_Info.xlsx')
