import streamlit as st
import sqlite3, os, time, re, pytz, json, ssl
from io import BytesIO
import urllib.request, urllib.parse, urllib.error

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

form1 = st.form(key="Options")
main_container = st.container()
main_container.write("")
form1.title("时效助手")
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
    dl = '单量：' + str(js['data'][text]['total_packages'])
    dtl = '投递率：' + str(js['data'][text]['toudi_rate'])
    main_container.write(dl)
    main_container.write(dtl)

    for driver,info in jss['data'].items() :
        if driver == 'noid' : continue
        if driver == 'zeroid' : continue
        if driver == '99088' : continue
        if jss['data'][driver]['total'] <= 20 : continue
        if 'DELIVERED' not in jss['data'][driver].keys():
            zero_list = zero_list + str(driver) + '/'
            fail_list = fail_list + str(driver) + '/'
            st.write(str(driver),0)
            continue
        d_percent = jss['data'][driver]['DELIVERED'] / jss['data'][driver]['total']
        if d_percent < 0.9 :
            d_percent = d_pecent * 100
            st.write(driver,round(d_percent,2))
            fail_list = fail_list + str(driver) + '/'

        #st.subheader(driver)
        #st.write(jss['data'][driver])
    notstart = '尚未开始：' + str(zero_list)
    notfinish = '未送完：' + str(fail_list)
    main_container.write(notstart)
    main_container.write(notfinish)
