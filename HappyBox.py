import streamlit as st
#import sqlite3, os, time, re, pytz
#import pandas as pd
#from datetime import datetime
#from selenium import webdriver
#from selenium.webdriver.common.keys import Keys
#from webdriver_manager.chrome import ChromeDriverManager

st.set_page_config(page_title='CJ小工具',page_icon = "🛐" ,initial_sidebar_state = 'expanded')

st.title("CJ 快乐盒")
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


st.sidebar.image("./pages/setup/images/aba3.jpg",'工具在上方')


col1,col2 = st.columns(2)
st.image('./pages/setup/images/aba.jpg', width=300)
st.write("")
st.write("请在左边菜单选择对应工具")
st.header("统统 一次搞定")

#col1.subheader("BR助手介绍")
#col1.write("还在为截取单号而烦恼吗？")
#col1.subheader("POD助手介绍")
#col1.write("还在为查询POD而烦恼吗？")
#col1.write("还在为统计合格率而烦恼吗？")

#col1.subheader("统计助手介绍")
#col1.write("还在为查询司机配送地区而烦恼吗？")

#st.subheader("算了 不介绍了 反正")
#st.title("你的烦恼 全都 一次搞定")
#st.title("")
