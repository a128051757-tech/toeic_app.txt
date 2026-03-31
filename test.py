import streamlit as st
import pandas as pd
import os

st.title("育漢的多益戰情室 - 除錯模式")

# 1. 診斷區：印出伺服器目前路徑下的所有檔案
files = os.listdir('.')
st.write("📂 伺服器目前看到的檔案列表：", files)

# 2. 檢查檔案是否存在
file_name = 'toeic_data.csv'
if file_name in files:
    st.success(f"✅ 找到 {file_name} 了！正在讀取...")
    df = pd.read_csv(file_path)
    st.write(df.head()) # 顯示前幾筆資料確認沒亂碼
else:
    st.error(f"❌ 真的找不到 {file_name}！")
    st.write("請檢查 GitHub 上的檔名是否完全小寫，或有無多餘空格。")
