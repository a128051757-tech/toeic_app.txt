import os
import streamlit as st

# 在頁面最上方印出檔案列表，幫你偵錯
st.write("目前目錄下的檔案：", os.listdir("."))

# 如果沒看到 toeic_data.csv，那就是上傳路徑或分支錯了