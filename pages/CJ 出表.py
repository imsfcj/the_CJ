import streamlit as st
import sqlite3, os, time, re, pytz, json, ssl
import pandas as pd
from io import BytesIO
import urllib.request, urllib.parse, urllib.error

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

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

form1 = st.form(key="Options")
main_container = st.container()
main_container.write("")
form1.title("出表助手")
text = form1.text_input("请直接输入批次号： ")
bt1 = form1.form_submit_button("提交")

url_head = 'https://map.uniexpress.ca/getdispatchstatistics?radio=6&dispatch_no='
d_url_head = 'https://map.uniexpress.ca/getdispatchdriverstatistics?radio=6&dispatch_no='
url_tail = '&ps=uniexpress!@!@'

zero_list = ''
fail_list = ''

if bt1 :
    url = url_head + text + url_tail
    d_url = d_url_head + text + url_tail
    uh = urllib.request.urlopen(url, context=ctx)
    data = uh.read().decode()
    js = json.loads(data)
    uhh = urllib.request.urlopen(d_url, context=ctx)
    dataa = uhh.read().decode()
    jss = json.loads(dataa)



    d_rate = js['data'][text]['total_packages']
    st.write('单量：',js['data'][text]['total_packages'])
    st.write('投递率：',js['data'][text]['toudi_rate'])
    dlist = {}
    for driver,info in jss['data'].items() :
        dlist[str(driver)] = jss['data'][driver]['total']
    df = pd.DataFrame(dlist, index=['row1'])
    df_xlsx = to_excel(df)
    main_container.download_button(label='📥 下载查单信息',
                                    data=df_xlsx ,
                                    file_name= 'Route_Info.xlsx')
