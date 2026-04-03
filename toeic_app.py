import streamlit as st
import pandas as pd
import random

# 設定網頁標題與手機優化
st.set_page_config(page_title="育漢的多益戰情室", layout="centered")

@st.cache_data
def load_data():
    df = pd.read_csv('toeic_data.csv')
    # 清理標頭並去重
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.drop_duplicates(subset=['word'])
    return df

df = load_data()

# 初始化 Session State (紀錄錯題與學習進度)
if 'wrong_words' not in st.session_state:
    st.session_state.wrong_words = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

st.title("🚀 育漢的多益 AI 戰情室")
mode = st.sidebar.radio("切換模式", ["單字刷題", "模擬測驗", "弱點分析"])

# --- 模式 1：模擬測驗 (題目設計) ---
if mode == "模擬測驗":
    st.subheader("✍️ 隨機模擬練習")
    
    # 隨機挑選一個單字當題目
    q_word = df.sample(1).iloc[0]
    correct_ans = q_word['translation']
    
    st.info(f"請問這個單字的意思是： **{q_word['word']}**")
    st.caption(f"提示：[{q_word['pos']}] | 情境：{q_word['scenario']}")

    # 生成干擾選項 (從同情境找 3 個錯誤答案)
    wrong_options = df[df['scenario'] == q_word['scenario']]['translation'].unique().tolist()
    if correct_ans in wrong_options: wrong_options.remove(correct_ans)
    
    options = random.sample(wrong_options, min(len(wrong_options), 3)) + [correct_ans]
    random.shuffle(options)

    # 顯示按鈕
    ans = st.radio("選擇答案：", options)

    if st.button("提交答案"):
        if ans == correct_ans:
            st.success("✅ 太強了！答對了！")
        else:
            st.error(f"❌ 答錯囉！正確答案是：{correct_ans}")
            # 紀錄到弱點區
            if q_word['word'] not in st.session_state.wrong_words:
                st.session_state.wrong_words.append(q_word['word'])
    
    if st.button("下一題"):
        st.rerun()

# --- 模式 2：弱點分析 (遺忘曲線) ---
elif mode == "弱點分析":
    st.subheader("🕵️ 弱點偵察機")
    if not st.session_state.wrong_words:
        st.write("目前沒有錯題，繼續保持！")
    else:
        st.warning(f"目前累積 {len(st.session_state.wrong_words)} 個不熟單字：")
        st.write(", ".join(st.session_state.wrong_words))
        
        if st.button("清空弱點紀錄"):
            st.session_state.wrong_words = []
            st.rerun()

# --- 模式 3：原本的單字刷題 ---
else:
    # 這裡放你原本寫的單字卡功能...
    st.write("（這裡放置原本的隨機抽卡邏輯）")
