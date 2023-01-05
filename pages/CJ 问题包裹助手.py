import streamlit as st
import sqlite3, os, time, re, pytz, json, ssl, requests
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

st.set_page_config(page_title='CJ 人工助手',page_icon = "🛐" ,initial_sidebar_state = 'expanded')
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
.stProgress .st-bm {
    background-color: #b5a2c8;
}
</style>""", unsafe_allow_html=True)

st.sidebar.image('./pages/setup/images/aba_icon4.jpg', width=100)
st.sidebar.title("程序运行详情")

form1 = st.form(key="Options")
main_container = st.container()
form1.title("CJ 四号")
uploaded_file = form1.file_uploader("请上传司机取货统计表", accept_multiple_files=False)
the_package = form1.radio("是否有实际包裹：",('No','Yes'), horizontal=True)
today_dispatch_number = form1.text_input("请输入今日批次：")
text = form1.text_area("请直接输入查单单号： ")
bt1 = form1.form_submit_button("开始查单")

fmt = "%d %b %Y %H:%M"
tz = pytz.timezone('America/Toronto')
yesterday = datetime.now() - timedelta(1)
yesterday_timp = datetime.timestamp(yesterday)
tnt_now = datetime.now(tz).strftime("%y%m%d")
the_day = datetime.today().strftime('%A')
#today_dispatch_number = 'TSUB-' + str(yesterday.strftime("%Y%m%d"))
the_decision = '不懂'
nope = 'N/A'
refund_info = '尚未赔付，'

con = sqlite3.connect('./pages/setup/data/sql/ai_fix.sqlite')
cur = con.cursor()
cur.executescript('''
CREATE TABLE IF NOT EXISTS YYZ_Route_List (
    'Route_Number' INTEGER
);

CREATE TABLE IF NOT EXISTS YYZ_Service_List (
    'Service_Number' INTEGER
);

CREATE TABLE IF NOT EXISTS YYZ_Warehouse_List (
    'Warehouse_number' INTEGER,
    'Warehouse_Batch' TEXT
);

CREATE TABLE IF NOT EXISTS Pickup_List (
    'Driver_ID' TEXT
)
''')
con.commit()
df = pd.read_excel('./pages/setup/data/important/route_info.xlsx', sheet_name="route_yyz")
df.to_sql('YYZ_Route_List', con, if_exists='replace', index=False)
df = pd.read_excel('./pages/setup/data/important/route_info.xlsx', sheet_name="service_yyz")
df.to_sql('YYZ_Service_List', con, if_exists='replace', index=False)
con.commit()
df = pd.read_excel('./pages/setup/data/important/route_info.xlsx', sheet_name="warehouse_yyz")
df.to_sql('YYZ_Warehouse_List', con, if_exists='replace', index=False)
con.commit()
yyz_all_route = []
cur.execute("SELECT * FROM YYZ_Route_List")
for row in cur : yyz_all_route.append(row[0])
 #st.write(yyz_all_route)
yyz_all_service = []
cur.execute("SELECT * FROM YYZ_Service_List")
for row in cur : yyz_all_service.append(row[0])
 #st.write(yyz_all_service)
yyz_all_warehouse = []
cur.execute("SELECT * FROM YYZ_Warehouse_List")
for row in cur : yyz_all_warehouse.append(row[0])

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
    con = sqlite3.connect('./pages/setup/data/sql/ai_fix.sqlite')
    cur = con.cursor()
    cur.executescript('''
    DROP TABLE IF EXISTS Final_Decision;

    CREATE TABLE IF NOT EXISTS Final_Decision (
        'Tno' TEXT,
        'Recommendation' TEXT
    )
    ''')
    con.commit()

    h = text.split('\n')
    url_head = 'https://driver.cluster.uniexpress.org/delivery/parcels/scan-journals/'
    percent_complete = 1 / len(h)
    #percent_complete = round(percent_complete,1)
    x = 0
    for ii in range(len(h)) :
        if len(h[ii]) <= 4 : continue
        #st.write(ii)
        url = url_head + h[ii]
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
            'tno': h[ii],
        }

        response = requests.get('https://map.cluster.uniexpress.org/map/getorderdetail', params=params, headers=headers)
        js = json.loads(response.content)
        #st.write(js)
        if js['status'] == 'SUCCESS' :
            #系统单号
            the_order = js['data']['orders']['order_id']
            #扫描记录 0是最晚
            scan_url = url_head + str(the_order)
            try:
                uhh = urllib.request.urlopen(scan_url, context=ctx)
            except :
                time.sleep(5)
                uhh = urllib.request.urlopen(scan_url, context=ctx)
            scan_data = uhh.read().decode()
            jss = json.loads(scan_data)
            driver_scan = jss['biz_data']
            driver_scan_id = []
            driver_scan_time = []

            if len(driver_scan) == 0 :
                driver_scan_id.append(nope)
                driver_scan_time.append(0)
            else :
                for lin in driver_scan :
                    driver_scan_id.append(lin['driver_id'])
                    driver_scan_time.append(datetime.timestamp(datetime.strptime(lin['submit_time'],'%Y-%m-%d %H:%M:%S')))
             #st.write(driver_scan_id)
            #轨迹 0是最早
            latest_trajectory = js['data']['orders']['latest_status']
             #st.write(latest_trajectory,type(latest_trajectory))
            trajectory = js['data']['path']
            trajectory_stat = []
            trajectory_time = []
            trajectory_person = []
            trajectory_count = len(js['data']['path']) - 1
            for lin in trajectory :
                trajectory_stat.append(lin['code'])
                trajectory_time.append(lin['pathTime'])
                if lin['staff_id'] is None : trajectory_person.append('N/A')
                else : trajectory_person.append(lin['staff_id'])
            #修改记录 0是最晚
            alteration = js['data']['operation']
            alteration_count = len(alteration) - 1
            alteration_details = []
            alteration_time = []
            alteration_person = []
            if len(alteration) == 0 :
                alteration_details.append(nope)
                alteration_time.append(0)
                alteration_person.append(nope)
            else :
                for lin in alteration :
                    alteration_details.append(lin['description'])
                    alteration_time.append(lin['utc_add_time'])
                    if len(str(lin['operator'])) == 0 : alteration_person.append(nope)
                    else : alteration_person.append(lin['operator'])
             #st.write(alteration_person)
            #仓储
            try:
                if len(js['data']['tracking']['storage_info']) == 0 : storage_info = nope
            except :
                if js['data']['tracking']['storage_info'] is None : storage_info = nope
            else : storage_info = js['data']['tracking']['storage_info']
             #st.write(storage_info)
            #大区
            segment_info = js['data']['tracking']['segment']
            #子批次
            sub_batch_info = js['data']['tracking']['sub_reference']
            #电话短信
            if len(js['data']['calllog']) == 0 :
                call_info = nope
                sms_info = nope
            else :
                if len(str(js['data']['calllog']['call_time'])) == 0 : call_info = nope
                else : call_info = js['data']['calllog']['call_time']
                if len(str(js['data']['calllog']['msg_time'])) == 0 : sms_info = nope
                else : sms_info = js['data']['calllog']['msg_time']
             #st.write(sms_info)
            #地址邮编
            address_info = js['data']['orders']['address']
            post_info = js['data']['orders']['zipcode']
            #经纬
            latitude_info = js['data']['orders']['lat']
            longitude_info = js['data']['orders']['lng']
            #司机号
            driver_id_info = str(js['data']['orders']['shipping_staff_id'])
            if len(driver_id_info) == 0 or re.search('[A-Za-z]',driver_id_info) : driver_id_info = 0
            #路线信息
            driver_memo_info = js['data']['orders']['driver_notes']
            if len(driver_memo_info) == 0 : driver_memo_info = nope
             #st.write(driver_memo_info)
            #备注
            order_memo_info = js['data']['orders']['postscript']
            if len(order_memo_info) == 0 : order_memo_info = nope
             #st.write(order_memo_info)
            #查仓库
            warehouse_info = js['data']['orders']['warehouse']
            #查投递状态
            shipping_status = js['data']['orders']['shipping_status']
            #查二配状态
            secondary_status = str(js['data']['tracking']['second_delivery_sn'])
            if len(secondary_status) == 0 : secondary_status = nope
            #POD
            #pod_status = js['data']['tracking']['pod_qualified']
            #st.write(js['data']['tracking']['pod_qualified'])
        else :
            latest_trajectory = nope
            the_decision = '查无'
            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
            con.commit()
            continue
        if latest_trajectory == 218 :
            latest_trajectory = trajectory_stat[trajectory_count-1]
            trajectory_stat[trajectory_count] = trajectory_stat[int(trajectory_count)-1]
            trajectory_person[trajectory_count] = trajectory_person[int(trajectory_count)-1]
            trajectory_time[trajectory_count] = trajectory_time[int(trajectory_count)-1]

        if latest_trajectory == 190 :
         #st.write(latest_trajectory)
            if the_package == 'No' :
                if driver_scan_id[0] == 'N/A' :
                    if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                        the_decision = '包裹被盲扫，状态未更新'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    if sub_batch_info == 'N/A' :
                        the_time_diff = int(yesterday_timp) - int(trajectory_time[trajectory_count])
                         #st.write(the_time_diff )
                        if the_time_diff > 864000 :
                            the_decision = '包裹长时间未到仓需确认'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            the_decision = '包裹尚未到仓'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                    else :
                        if driver_id_info != '0' and len(driver_id_info) <= 4 :
                            the_decision = '未定责需确认，由配送司机'+ str(driver_id_info) +'赔付'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            the_decision = '未定责需确认，由仓库赔付'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                else :
                    the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
            else :
                if int(warehouse_info) in yyz_all_warehouse :
                    the_decision = '包裹需盲扫'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    the_decision = '包裹错区需转运'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()

        if latest_trajectory == 203 :
            if the_package == 'Yes' :
                the_decision = '请检查包裹及面单'
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()
            else :
                the_decision = 'POD ' + str(trajectory_person[trajectory_count])
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()

        if latest_trajectory == 213 or latest_trajectory == 214 :
            if the_package == 'Yes' :
                the_decision = '包裹仓储号：' + storage_info + '确认仓储号并入库'
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()
            else :
                if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                    the_decision = '包裹被盲扫，需挑出'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    if driver_scan_id[0] == 'N/A' :
                        the_decision = '由仓库赔付，有概率已被自提'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        if int(driver_scan_time[0]) > int(trajectory_time[trajectory_count]) :
                            the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            the_decision = '由仓库赔付，有概率已被自提'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()

        if latest_trajectory == 192 or latest_trajectory == 198 :
            if the_package == 'Yes' :
                if int(warehouse_info) in yyz_all_warehouse :
                    the_decision = '包裹需盲扫，并修改状态'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    the_decision = '包裹错区需转运'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
            else :
                if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                    the_decision = '包裹被盲扫，状态未更新'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    if sub_batch_info == 'N/A' :
                        if driver_scan_id[0] != 'N/A' :
                            the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            the_time_diff = int(yesterday_timp) - int(trajectory_time[trajectory_count])
                            if the_time_diff > 864000 :
                                the_decision = '包裹长时间未到仓需确认'
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                            else :
                                the_decision = '包裹尚未到仓'
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                    else :
                        if int(driver_scan_time[0]) > int(trajectory_time[trajectory_count]) :
                            the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            the_decision = '未定责需确认，由仓库赔付'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()

        if latest_trajectory == 204 :
            for i in range(len(alteration_details)) :
                if re.search('^TRANSSHIPMENT',alteration_details[i]) :
                    decision_person = alteration_person[i]
                    the_time = str(datetime.fromtimestamp(alteration_time[i]).strftime('%Y-%m-%d %H:%M:%S'))
                    break
                else :
                    decision_person = nope
                    the_time = nope
            if the_package == 'Yes' :
                the_decision = '包裹待第三方转运，操作人: ' + decision_person
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()
            else :
                if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                    the_decision = '包裹被盲扫，需拿出'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    the_decision = '需和操作人: ' + decision_person + '确认包裹；时间：' + the_time
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()

        if latest_trajectory == 217 :
            for i in range(len(alteration_details)) :
                if re.search('COMPLETE',alteration_details[i]) :
                    decision_person = alteration_person[i]
                    the_time = str(datetime.fromtimestamp(alteration_time[i]).strftime('%Y-%m-%d %H:%M:%S'))
                     #st.write(the_time)
                    break
                else :
                    decision_person = nope
                    the_time = nope
            if the_package == 'Yes' :
                the_decision = '需和操作人: ' + decision_person + '确认包裹；时间：' + the_time
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()
            else :
                the_decision = '包裹已给第三方转运，操作人：' + decision_person + ' 时间：' + the_time
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()

        if latest_trajectory == 195 :
            if the_package == 'Yes' :
                if int(warehouse_info) in yyz_all_warehouse :
                    the_decision = '包裹需盲扫，并修改状态'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    the_decision = '包裹错区需转运'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
            else :
                if int(warehouse_info) not in yyz_all_warehouse :
                    the_decision = '包裹与该城市无关'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    if str(warehouse_info) != '2' :
                        the_head = cur.execute("SELECT Batch_Head FROM YYZ_Warehouse_List WHERE Warehouse = ?",(warehouse_info,)).fetchone()[0]
                        con.commit()
                        if the_head in sub_batch_info :
                            dispatch_time = int(re.findall('^[A-Z]+\-([0-9]+)',sub_batch_info)[0][:8])
                            the_time_diff = int(yesterday.strftime("%Y%m%d")) - dispatch_time
                            if the_time_diff > 3 :
                                if int(driver_scan_time[0]) > int(trajectory_time[trajectory_count]) :
                                    the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                    con.commit()
                                else :
                                    the_decision = '包裹大概率在转运途中丢失'
                                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                    con.commit()
                            else :
                                the_decision = '包裹在转运途中'
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                        else :
                            if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                                the_decision = '包裹被盲扫，状态未更新'
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                            else :
                                if driver_scan_id[0] != 'N/A' :
                                    the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                    con.commit()
                                else :
                                    tra_time = trajectory_time[trajectory_count]
                                    the_time_diff = int(yesterday_timp) - tra_time
                                    if the_time_diff > 345600 :
                                        the_decision = '未定责需确认，由仓库赔付'
                                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                        con.commit()
                                    else :
                                        the_decision = '包裹大概率在运输途中'
                                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                        con.commit()
                    else :
                        if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                            the_decision = '包裹被盲扫，状态未更新'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            if driver_scan_id[0] != 'N/A' :
                                the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                            else :
                                tra_time = trajectory_time[trajectory_count]
                                the_time_diff = int(yesterday_timp) - tra_time
                                if the_time_diff > 345600 :
                                    the_decision = '未定责需确认，由仓库赔付'
                                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                    con.commit()
                                else :
                                    the_decision = '包裹大概率在运输途中'
                                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                    con.commit()

        if latest_trajectory == 220 or latest_trajectory == 228:
            if the_package == 'Yes' :
                the_decision = '确认包裹及面单进行二配, 二配号：' + str(secondary_status)
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()
            else :
                if int(datetime.timestamp(datetime.strptime(re.findall('^[A-Z]+\-([0-9]+)',sub_batch_info)[0],'%Y%m%d%H%M'))) < trajectory_time[trajectory_count] :
                    the_decision = '请查询, 二配号：' + str(secondary_status)
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    if int(driver_scan_time[0]) > int(trajectory_time[trajectory_count]) :
                        the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        the_decision = '请查询, 二配号：' + str(secondary_status)
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()

        if latest_trajectory == 199 or latest_trajectory == 200 :
            if the_package == 'Yes' :
                 #st.write(warehouse_info,type(warehouse_info))
                 #st.write(yyz_all_warehouse)
                if int(warehouse_info) in yyz_all_warehouse :
                    the_decision = '包裹需盲扫'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    the_decision = '包裹错区需转运'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
            else :
                dispatch_time = int(re.findall('^[A-Z]+\-([0-9]+)',sub_batch_info)[0][:8])
                the_time_diff = int(yesterday.strftime("%Y%m%d")) - dispatch_time
                if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                    the_decision = '包裹被盲扫'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                if the_time_diff > 2 :
                    if int(driver_scan_time[0]) > int(trajectory_time[trajectory_count]) :
                        the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        if driver_id_info == trajectory_person[trajectory_count] :
                            the_decision = '未定责需确认，由轨迹司机' + str(trajectory_person[trajectory_count]) +'赔付'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            for i in range(len(alteration_details)) :
                                if re.search('^Trans',alteration_details[i]) :
                                    decision_person = alteration_person[i]
                                    the_time = alteration_time[i]
                                    break
                                else :
                                    decision_person = nope
                                    the_time = 0
                            if trajectory_time[trajectory_count] > the_time :
                                the_decision = '未定责需确认，由轨迹司机' + str(trajectory_person[trajectory_count]) + '赔付；时间' + str(datetime.fromtimestamp(trajectory_time[trajectory_count]).strftime('%Y-%m-%d %H:%M:%S'))
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                            else :
                                the_decision = '未定责需确认，由仓库赔付'
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                else :
                    if driver_id_info != '0' and len(driver_id_info) <= 4 :
                        the_decision = '需与配送司机: '+ str(driver_id_info) +'确认包裹状态'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        if int(driver_scan_time[0]) > int(trajectory_time[trajectory_count]) :
                            the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            if driver_id_info == trajectory_person[trajectory_count] :
                                the_decision = '未定责需确认，由轨迹司机' + str(trajectory_person[trajectory_count]) +'赔付'
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                            else :
                                for i in range(len(alteration_details)) :
                                    if re.search('^Trans',alteration_details[i]) :
                                        decision_person = alteration_person[i]
                                        the_time = alteration_time[i]
                                        break
                                    else :
                                        decision_person = nope
                                        the_time = 0
                                if trajectory_time[trajectory_count] > the_time :
                                    the_decision = '未定责需确认，由轨迹司机' + str(trajectory_person[trajectory_count]) + '赔付；时间' + str(datetime.fromtimestamp(trajectory_time[trajectory_count]).strftime('%Y-%m-%d %H:%M:%S'))
                                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                    con.commit()
                                else :
                                    the_decision = '未定责需确认，由仓库赔付'
                                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                    con.commit()

        if latest_trajectory == 202 :
            the_fix = 'Trans from ' + str(trajectory_person[trajectory_count])
            for i in range(len(alteration_details)) :
                if the_fix in alteration_details[i] :
                    the_person = re.findall('to\s([0-9]+)', alteration_details[i])[0]
                    the_time = alteration_time[i]
                    break
                else :
                    the_person = nope
                    the_time = 0
            if the_package == 'Yes' :
                 #st.write(warehouse_info,type(warehouse_info))
                 #st.write(yyz_all_warehouse)
                if int(warehouse_info) in yyz_all_warehouse :
                    the_decision = '包裹需盲扫'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    the_decision = '包裹错区需转运'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
            else :
                if driver_scan_id[0] != 'N/A' :
                    if driver_scan_time[0] > the_time :
                        the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        if the_person == '99088' :
                            the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            if driver_id_info != '0' and len(driver_id_info) <= 4 :
                                the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                            else :
                                the_decision = '未定责需确认，由仓库赔付'
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                else :
                    if driver_id_info != '0' and len(driver_id_info) <= 4 :
                        the_decision = '未定责需确认，由配送司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(the_time).strftime('%Y-%m-%d %H:%M:%S'))
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                            the_decision = '包裹被盲扫'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            the_decision = '未定责需确认，由仓库赔付'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()

        if latest_trajectory == 215 :
            tra_time = trajectory_time[trajectory_count]
            for i in range(len(trajectory_stat)) :
                if trajectory_stat[i] == 213 :
                    storage_time = trajectory_time[i]
                    break
                else : storage_time = 9999999999
            the_time_diff = trajectory_time[trajectory_count] - storage_time
            if the_time_diff >= 3456000 :
                the_decision = '包裹自然过期'
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()
            else :
                if the_package == 'Yes' :
                    the_decision = '误操作，操作人：' + trajectory_person[trajectory_count]
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                        the_decision = '包裹被盲扫，需修改状态/拿出'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        the_decision = '需和操作人：' + trajectory_person[trajectory_count] + '确认包裹'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()

        if latest_trajectory == 216 :
            if the_package == 'Yes' :
                the_decision = '大概率误操作，请检查'
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()
            else :
                the_decision = '查自提POD'
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()

        if latest_trajectory == 206 or latest_trajectory == 222 :
            if the_package == 'Yes' :
                if sms_info != 'N/A' :
                    if call_info != 'N/A' :
                        the_decision = '包裹可入库'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        the_decision = '包裹85入库'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                else :
                    the_decision = '配送不合格'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
            else :
                if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                    the_decision = '包裹被盲扫，需挑出单独处理'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    if int(driver_scan_time[0]) > int(trajectory_time[trajectory_count]) :
                        the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        if trajectory_person[trajectory_count] == driver_id_info :
                            the_decision = '未定责需确认，由轨迹司机' + str(trajectory_person[trajectory_count]) + '赔付'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            for i in range(len(alteration_details)) :
                                if re.search('^Trans',alteration_details[i]) :
                                    decision_person = alteration_person[i]
                                    the_time = alteration_time[i]
                                    break
                                else :
                                    decision_person = nope
                                    the_time = 0
                            if trajectory_time[trajectory_count] > the_time :
                                the_decision = '未定责需确认，由轨迹司机' + str(trajectory_person[trajectory_count]) + '赔付；时间' + str(datetime.fromtimestamp(trajectory_time[trajectory_count]).strftime('%Y-%m-%d %H:%M:%S'))
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                            else :
                                the_decision = '未定责需确认，由仓库赔付'
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()

        if latest_trajectory == 226 :
            if the_package == 'Yes' :
                tra_time = trajectory_time[trajectory_count]
                the_time_diff = int(yesterday_timp) - tra_time
                if the_time_diff >= 864000 :
                    the_decision = '包裹需入库'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    the_decision = '包裹需反去自提点'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
            else :
                if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                    the_decision = '包裹被盲扫，需挑出单独处理'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    the_decision = '查贴条POD,包裹可能在自提点'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()

        if latest_trajectory == 229 :
            if the_package == 'Yes' :
                the_decision = '需送去自提点'
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()
            else :
                if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                    the_decision = '包裹被盲扫，需送去自提点'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    the_decision = '需和轨迹司机' + str(trajectory_person[trajectory_count]) + '确认包裹位置'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()

        if latest_trajectory == 211 :
            if the_package == 'Yes' :
                if sms_info != 'N/A' :
                    if call_info != 'N/A' :
                        the_decision = '查贴条POD'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        the_decision = '包裹85入库'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                else :
                    the_decision = '配送不合格'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
            else :
                if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                    the_decision = '包裹被盲扫，需挑出单独处理'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    if int(driver_scan_time[0]) > int(trajectory_time[trajectory_count]) :
                        the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        if trajectory_person[trajectory_count] == driver_id_info :
                            the_decision = '未定责需确认，由轨迹司机' + str(trajectory_person[trajectory_count]) + '赔付'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            for i in range(len(alteration_details)) :
                                if re.search('^Trans',alteration_details[i]) :
                                    decision_person = alteration_person[i]
                                    the_time = alteration_time[i]
                                    break
                                else :
                                    decision_person = nope
                                    the_time = 0
                            if trajectory_time[trajectory_count] > the_time :
                                the_decision = '未定责需确认，由轨迹司机' + str(trajectory_person[trajectory_count]) + '赔付；时间' + str(datetime.fromtimestamp(trajectory_time[trajectory_count]).strftime('%Y-%m-%d %H:%M:%S'))
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                            else :
                                the_decision = '未定责需确认，由仓库赔付'
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()

        if latest_trajectory == 219 :
            if the_package == 'Yes' :
                if int(warehouse_info) in yyz_all_warehouse :
                    if 'refund' in order_memo_info :
                        the_decision = '包裹已赔付'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        the_decision = '包裹需盲扫，并修改状态'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                else:
                    the_decision = '其他城市发错包裹需转运'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
            else :
                if int(warehouse_info) in yyz_all_warehouse :
                    if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                        the_decision = '包裹被盲扫，需修改状态'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        the_decision = '包裹发错城市，包裹发现时间：' + str(trajectory_time[trajectory_count]) + '处理人：' + str(trajectory_person[trajectory_count])
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                else :
                    if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                        the_decision = '其他城市发错包裹被盲扫,需挑出转运'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        the_decision = '包裹与该城市无关'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()

        if latest_trajectory == 231 or latest_trajectory == 232:
            if the_package == 'Yes' :
                the_decision = '包裹需盲扫，并再次配送'
                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                con.commit()
            else :
                if today_dispatch_number in sub_batch_info or sub_batch_info == 'TSUB-202209011537' :
                    the_decision = '包裹被盲扫，待再次配送'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    if int(driver_scan_time[0]) > int(trajectory_time[trajectory_count]) :
                        the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        if trajectory_person[trajectory_count] == driver_id_info :
                            the_decision = '未定责需确认，由轨迹司机' + str(trajectory_person[trajectory_count]) + '赔付'
                            cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                            con.commit()
                        else :
                            for i in range(len(alteration_details)) :
                                if re.search('^Trans',alteration_details[i]) :
                                    decision_person = alteration_person[i]
                                    the_time = alteration_time[i]
                                    break
                                else :
                                    decision_person = nope
                                    the_time = 0
                            if trajectory_time[trajectory_count] > the_time :
                                the_decision = '未定责需确认，由轨迹司机' + str(trajectory_person[trajectory_count]) + '赔付；时间' + str(datetime.fromtimestamp(trajectory_time[trajectory_count]).strftime('%Y-%m-%d %H:%M:%S'))
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()
                            else :
                                the_decision = '未定责需确认，由仓库赔付'
                                cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                                con.commit()

        if latest_trajectory == 255 :
            if the_package == 'Yes' :
                if int(warehouse_info) in yyz_all_warehouse :
                    the_decision = '包裹需盲扫'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    the_decision = '包裹错区需转运'
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
            else :
                if driver_scan_id[0] == 'N/A' :
                    the_decision = '未定责需确认，由扫描司机' + str(driver_scan_id[0]) +'赔付；时间' + str(datetime.fromtimestamp(driver_scan_time[0]).strftime('%Y-%m-%d %H:%M:%S'))
                    cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                    con.commit()
                else :
                    if int(warehouse_info) in yyz_all_warehouse :
                        the_decision = '包裹未到，发货批次:' + sub_batch_info
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()
                    else :
                        the_decision = '包裹与本城市无关'
                        cur.execute("INSERT INTO Final_Decision (Tno,Recommendation) VALUES (?,?)",(h[ii],the_decision))
                        con.commit()

        if '包裹需盲扫' in the_decision :
            if sms_info != 'N/A' :
                the_decision = '包裹需入库'
                cur.execute("UPDATE Final_Decision SET  Recommendation = ? WHERE Tno = ?", (h[ii],tracking,))
                con.commit()
            else :
                if int(driver_id_info) not in yyz_all_service :
                    the_decision = the_decision + '，可盲扫'
                    cur.execute("UPDATE Final_Decision SET  Recommendation = ? WHERE Tno = ?", (h[ii],tracking,))
                    con.commit()
                else :
                    if driver_id_info == '0' or driver_id_info == '99088' :
                        the_decision = the_decision + '，可盲扫'
                        cur.execute("UPDATE Final_Decision SET  Recommendation = ? WHERE Tno = ?", (h[ii],tracking,))
                        con.commit()
                    if driver_id_info == '99092' :
                        if 'refund' in order_memo_info :
                            the_decision = '包裹已赔付'
                            cur.execute("UPDATE Final_Decision SET  Recommendation = ? WHERE Tno = ?", (h[ii],tracking,))
                            con.commit()
                        else :
                            the_decision = the_decision + '，可盲扫'
                            cur.execute("UPDATE Final_Decision SET  Recommendation = ? WHERE Tno = ?", (h[ii],tracking,))
                            con.commit()
                    if driver_id_info == '99085' or driver_id_info == '99087' or driver_id_info == '99093' or driver_id_info == '99099' :
                        the_decision = '包裹异常，需手动修正'
                        cur.execute("UPDATE Final_Decision SET  Recommendation = ? WHERE Tno = ?", (h[ii],tracking,))
                        con.commit()
                    if driver_id_info == '99090' or driver_id_info == '99000' :
                        count = 0
                        cur.execute("SELECT * FROM Alteration_Detail_List")
                        for row in cur :
                            if re.search('^Trans.*to\s99000',row[0]) or re.search('^Trans.*to\s99090',row[0]) : count = count + 1
                        if count > 3 :
                            the_decision = '包裹需手动修正地址'
                            cur.execute("UPDATE Final_Decision SET  Recommendation = ? WHERE Tno = ?", (h[ii],tracking,))
                            con.commit()
                        else :
                            the_decision = '包裹飞单待修复'
                            cur.execute("UPDATE Final_Decision SET  Recommendation = ? WHERE Tno = ?", (h[ii],tracking,))
                            con.commit()
                    if driver_id_info == '99084' :
                        for info in alteration :
                            if 'DESTINATION' in info :
                                the_decision = '包裹地址已修复，可盲扫'
                                cur.execute("UPDATE Final_Decision SET  Recommendation = ? WHERE Tno = ?", (h[ii],tracking,))
                                con.commit()
                                break
                            else : continue
                        else :
                            the_decision = '包裹地址待修复，给客服'
                            cur.execute("UPDATE Final_Decision SET  Recommendation = ? WHERE Tno = ?", (h[ii],tracking,))
                            con.commit()
        st.write(h[ii],the_decision)
        x = x + percent_complete
        my_bar.progress(x)

    st.sidebar.write('\n -----     开查小分队     ----- ')
    cur.execute("SELECT * FROM Final_Decision WHERE Recommendation like '%扫描司机%'")
    dlist = {}
    for row in cur :
        info = row[1].split('；')
        try :
            the_driver = re.findall('[0-9]+',info[0])[0]
        except :
            continue
        the_time = re.findall('时间(.*)',info[1])[0].split()[0]
        dlist[row[0]] = [the_driver,the_time]
    con.commit()

    for tno,driver in dlist.items() :
        dispatch_time = (datetime.strptime(dlist[tno][1], '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        try :
            df = pd.read_excel(uploaded_file,sheet_name=dispatch_time,names=["Driver_ID"],skiprows=4,usecols="A")
            df.to_sql('Pickup_List', con, if_exists='replace', index=False)
            cur.execute('SELECT * FROM Pickup_List')
            for row in cur :
                all_driver = str(row[0]).replace('.0','')
                if str(driver[0]) in all_driver : dlist[tno][0] = all_driver
        except :
            continue
    for tno,driver in dlist.items() :
        the_decision = '包裹由：' + driver[0] + '赔付；扫描时间：' + driver[1]
        cur.execute("UPDATE Final_Decision SET Recommendation = ? WHERE Tno = ?", (the_decision,tno,))
        con.commit()
        st.write(tno,the_decision)

    st.sidebar.write('\n -----     查询完毕     ----- ')

    rq = '''
    SELECT * FROM Final_Decision
    '''
    df = pd.read_sql (rq, con)
    df_xlsx = to_excel(df)
    main_container.download_button(label='📥 下载来着CJ四号的建议',
                                    data=df_xlsx ,
                                    file_name= 'Auto_Recommendation.xlsx')
#
