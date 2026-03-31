import streamlit as st
import pandas as pd
import random

# 頁面設定
st.set_page_config(page_title="2026 TOEIC 衝刺工具", layout="centered")

# 1. 載入資料 (增加錯誤處理)
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('toeic_data.csv')
        return df
    except FileNotFoundError:
        return None

df = load_data()

if df is None:
    st.error("找不到 toeic_data.csv，請先建立檔案！")
    st.stop()

# 2. 側邊欄：進度與篩選
st.sidebar.header("🎯 學習設定")
scenarios = ["全部"] + list(df['scenario'].unique())
selected_scen = st.sidebar.selectbox("選擇測驗情境", scenarios)

# 3. 篩選資料邏輯
if selected_scen != "全部":
    filtered_df = df[df['scenario'] == selected_scen]
else:
    filtered_df = df

# 4. Session State 紀錄目前卡片索引
if 'card_index' not in st.session_state:
    st.session_state.card_index = 0

# 5. 切換卡片功能
def next_card():
    st.session_state.card_index = random.randint(0, len(filtered_df) - 1)

# 6. UI 顯示
st.title("🚀 育漢的 2026 轉職戰情室")
st.caption("目標：5/31 多益 750+ | 2027 滿血入職外商")

if not filtered_df.empty:
    # 確保索引不溢出
    if st.session_state.card_index >= len(filtered_df):
        st.session_state.card_index = 0
        
    current_card = filtered_df.iloc[st.session_state.card_index]

    # 顯示卡片正面
    st.markdown(f"### 情境：【{current_card['scenario']}】")
    st.info(f"##單字：{current_card['word']} ({current_card['pos']})")
    
    # 翻面功能 (用 Expander 模擬)
    with st.expander("🔍 點擊翻面 (查看解釋與例句)"):
        st.success(f"**翻譯：** {current_card['translation']}")
        st.write(f"**例句：** \n{current_card['example']}")
        st.warning(f"**💡 考點筆記：** {current_card['note']}")

    # 控制按鈕
    st.button("換下一張卡片 ➡️", on_click=next_card)
else:
    st.warning("該情境下暫無單字數據。")

# 7. 底部署名 (給自己的動力)
st.divider()
st.write("🦁 *性格比聰明重要 10000 倍。保持冷靜，10/4 迎接新生命，2027 領取資遣費華麗轉身。*")