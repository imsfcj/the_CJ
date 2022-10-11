import streamlit as st
import sqlite3, os, time, re, pytz
from io import BytesIO
from datetime import datetime
import pandas as pd
#from pyxlsb import open_workbook as open_xlsb

the_day = datetime.today().strftime('%A')[:3]
if the_day == 'Mon' : the_pick = 1
if the_day == 'Tue' : the_pick = 2
if the_day == 'Wed' : the_pick = 3
if the_day == 'Thu' : the_pick = 4
if the_day == 'Fri' : the_pick = 5
if the_day == 'Sat' : the_pick = 6
if the_day == 'Sun' : the_pick = 6

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

st.sidebar.image('./pages/setup/images/aba_icon3.jpg', width=100)
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
);

CREATE TABLE Import_List (
    driver TEXT,
    pickup_day TEXT
);

CREATE TABLE Area_List (
    Brampton TEXT,
    Etobicoke TEXT,
    Mississuaga TEXT,
    York TEXT,
    East_York TEXT,
    Downtown TEXT,
    Vaughan TEXT,
    North_York TEXT,
    Scarborough TEXT,
    Richmond_Hill TEXT,
    Markham TEXT,
    Midtown TEXT,
    Barrie TEXT,
    'Unknown' TEXT
)
''')
con.commit()

rq = '''
SELECT * FROM Area_List
'''
df = pd.read_sql (rq, con)
#path = r'C:\Users\Jason_Cang\Desktop\py\dispatch\check'
df.to_excel('./pages/setup/data/important/day_out.xlsx', index = False)

df = pd.read_csv('./pages/setup/data/important/driver.csv')
df.to_sql('Driver_List', con, if_exists='append', index=False)
con.commit()

st.title("统计司机助手")
tab1,tab2 = st.tabs(["每日统计","一周统计"])

form2 = tab2.form(key="Optionss")
form2.header("统计一周司机地区及仓库")

alldrivers = form2.file_uploader("请在这里上传统计文件：", accept_multiple_files=True)
#englishdrivers = form2.file_uploader("请在这里上传Google Form：", accept_multiple_files=False)
bt2 = form2.form_submit_button("提交")
main_container2 = tab2.container()
main_container2.write("")
cm1,cm2,cm3 = tab2.columns(3)
cm1.subheader("司机号")
cm2.subheader("地区")
cm3.subheader("仓库")

if bt2 :
    st.sidebar.write('\n -----     开始统计     ----- ')
    for uploaded_file in alldrivers:
        try :
            df = pd.read_excel(uploaded_file,sheet_name="物流列表",header=None,names=["driver","pickup_day"],skiprows=1,usecols="AD:AE")
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
        cm3.write(w)

    ctt = cur.execute("SELECT count(Driver) FROM All_List").fetchone()[0]
    st.sidebar.write('这周一共报名了',str(ctt),'个司机')

    rq = '''
    SELECT * FROM All_List ORDER BY Location
    '''
    df = pd.read_sql (rq, con)
    df_xlsx = to_excel(df)
    main_container2.download_button(label='📥 下载每周司机统计信息',
                                    data=df_xlsx ,
                                    file_name= 'Driver_Info.xlsx')
    st.sidebar.write('\n -----     统计完毕     ----- ')

form1 = tab1.form(key="Options")
choice = form1.selectbox("想统计哪一天的司机报名情况？",('Mon','Tue','Wed','Thu','Fri','Sat','Sun'),index=the_pick)
form1.header("统计每日司机")
uploaded_file = form1.file_uploader("请上传需要统计的文件：", accept_multiple_files=False)
main_container1 = tab1.container()
main_container1.write("")
bt1 = form1.form_submit_button("提交")
dm1,dm2 = tab1.columns(2)
dm1.subheader("司机号")
dm2.subheader("配送地区")


if bt1 :
    st.sidebar.write('\n -----     开始统计     ----- ')
    st.sidebar.write("配送日期：",choice)
    df = pd.read_csv(uploaded_file, engine='python')
    df.to_sql('All_List', con, if_exists='append', index=False)
    con.commit()

    cur.execute("UPDATE All_List SET Location = 'Unknown' WHERE Location is NULL")
    con.commit()

    if choice == 'Mon' :
        alist = {}
        cur.execute("SELECT Driver,Location FROM All_List WHERE Mon = '1'")

        cttttt=0
        for row in cur :
            cttttt = cttttt +1
            alist[row[0]] = row[1]
            dm1.write(row[0])
            dm2.write(row[1])
        df = pd.read_excel('./pages/setup/data/important/day_out.xlsx')
        for d,a in alist.items() :
            df = df.append({a:d},ignore_index=True)
        df = df.apply(lambda x: pd.Series(x.dropna().values)).fillna(' ')

        df_xlsx = to_excel(df)
        main_container1.download_button(label='📥 下载每日司机统计',
                                        data=df_xlsx ,
                                        file_name= 'Daily_driver_Info.xlsx')
    #
    if choice == 'Tue' :
        alist = {}
        cur.execute("SELECT Driver,Location FROM All_List WHERE Tue = '1'")

        cttttt=0
        for row in cur :
            cttttt = cttttt +1
            alist[row[0]] = row[1]
            dm1.write(row[0])
            dm2.write(row[1])
        df = pd.read_excel('./pages/setup/data/important/day_out.xlsx')
        for d,a in alist.items() :
            df = df.append({a:d},ignore_index=True)
        df = df.apply(lambda x: pd.Series(x.dropna().values)).fillna(' ')

        df_xlsx = to_excel(df)
        main_container1.download_button(label='📥 下载每日司机统计',
                                        data=df_xlsx ,
                                        file_name= 'Daily_driver_Info.xlsx')
    #
    if choice == 'Wed' :
        alist = {}
        cur.execute("SELECT Driver,Location FROM All_List WHERE Wed = '1'")

        cttttt=0
        for row in cur :
            cttttt = cttttt +1
            alist[row[0]] = row[1]

            dm1.write(row[0])
            dm2.write(row[1])
        df = pd.read_excel('./pages/setup/data/important/day_out.xlsx')
        for d,a in alist.items() :
            df = df.append({a:d},ignore_index=True)
        df = df.apply(lambda x: pd.Series(x.dropna().values)).fillna(' ')

        df_xlsx = to_excel(df)
        main_container1.download_button(label='📥 下载每日司机统计',
                                        data=df_xlsx ,
                                        file_name= 'Daily_driver_Info.xlsx')
    #
    if choice == 'Thu' :
        alist = {}
        cur.execute("SELECT Driver,Location FROM All_List WHERE Thu = '1'")

        cttttt=0
        for row in cur :
            cttttt = cttttt +1
            alist[row[0]] = row[1]
            dm1.write(row[0])
            dm2.write(row[1])
        df = pd.read_excel('./pages/setup/data/important/day_out.xlsx')
        for d,a in alist.items() :
            df = df.append({a:d},ignore_index=True)
        df = df.apply(lambda x: pd.Series(x.dropna().values)).fillna(' ')

        df_xlsx = to_excel(df)
        main_container1.download_button(label='📥 下载每日司机统计',
                                        data=df_xlsx ,
                                        file_name= 'Daily_driver_Info.xlsx')
    #
    if choice == 'Fri' :
        alist = {}
        cur.execute("SELECT Driver,Location FROM All_List WHERE Fri = '1'")

        cttttt=0
        for row in cur :
            cttttt = cttttt +1
            alist[row[0]] = row[1]
            dm1.write(row[0])
            dm2.write(row[1])
        df = pd.read_excel('./pages/setup/data/important/day_out.xlsx')
        for d,a in alist.items() :
            df = df.append({a:d},ignore_index=True)
        df = df.apply(lambda x: pd.Series(x.dropna().values)).fillna(' ')

        df_xlsx = to_excel(df)
        main_container1.download_button(label='📥 下载每日司机统计',
                                        data=df_xlsx ,
                                        file_name= 'Daily_driver_Info.xlsx')
    #
    if choice == 'Sat' :
        alist = {}
        cur.execute("SELECT Driver,Location FROM All_List WHERE Sat = '1'")

        cttttt=0
        for row in cur :
            cttttt = cttttt +1
            alist[row[0]] = row[1]
            dm1.write(row[0])
            dm2.write(row[1])
        df = pd.read_excel('./pages/setup/data/important/day_out.xlsx')
        for d,a in alist.items() :
            df = df.append({a:d},ignore_index=True)
        df = df.apply(lambda x: pd.Series(x.dropna().values)).fillna(' ')

        df_xlsx = to_excel(df)
        main_container1.download_button(label='📥 下载每日司机统计',
                                        data=df_xlsx ,
                                        file_name= 'Daily_driver_Info.xlsx')
    #
    if choice == 'Sun' :
        alist = {}
        cur.execute("SELECT Driver,Location FROM All_List WHERE Sun = '1'")

        cttttt=0
        for row in cur :
            cttttt = cttttt +1
            alist[row[0]] = row[1]
            dm1.write(row[0])
            dm2.write(row[1])
        df = pd.read_excel('./pages/setup/data/important/day_out.xlsx')
        for d,a in alist.items() :
            df = df.append({a:d},ignore_index=True)
        df = df.apply(lambda x: pd.Series(x.dropna().values)).fillna(' ')

        df_xlsx = to_excel(df)
        main_container1.download_button(label='📥 下载每日司机统计',
                                        data=df_xlsx ,
                                        file_name= 'Daily_driver_Info.xlsx')
    st.sidebar.write('共有',str(cttttt),'个报名司机')
    st.sidebar.write('\n -----     统计完毕     ----- ')
    #
    #df.to_csv('周一.csv', index = False)














#
