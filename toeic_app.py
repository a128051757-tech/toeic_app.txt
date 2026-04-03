import streamlit as st
import pandas as pd
import random

# 設定網頁標題與手機優化
st.set_page_config(page_title="育漢的多益戰情室", layout="centered")

@st.cache_data
def load_data():
    # 讀取 CSV 並處理格式
    df = pd.read_csv('toeic_data.csv')
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.drop_duplicates(subset=['word'])
    return df

df = load_data()

# 初始化 Session State
if 'wrong_words' not in st.session_state:
    st.session_state.wrong_words = []

st.title("🚀 育漢的多益 AI 戰情室")
mode = st.sidebar.radio("切換模式", ["單字刷題", "模擬測驗", "弱點分析"])

# --- 模式 1：單字刷題 (原本的功能補回) ---
if mode == "單字刷題":
    st.subheader("🎴 隨機單字卡")
    
    # 增加篩選功能
    scenarios = ["全部"] + list(df['scenario'].unique())
    sel_scenario = st.selectbox("選擇情境", scenarios)
    
    filtered_df = df if sel_scenario == "全部" else df[df['scenario'] == sel_scenario]
    
    if st.button("抽一張單字卡") or 'current_card' not in st.session_state:
        st.session_state.current_card = filtered_df.sample(1).iloc[0]

    card = st.session_state.current_card
    
    # 顯示單字卡介面
    st.info(f"### {card['word']}")
    st.write(f"**音性：** {card['pos']} | **情境：** {card['scenario']}")
    
    with st.expander("點擊查看翻譯與例句"):
        st.success(f"**中文翻譯：** {card['translation']}")
        st.write(f"**例句：** \n{card['example']}")
        st.write(f"**筆記：** {card['note']}")

# --- 模式 2：模擬測驗 (題目設計) ---
elif mode == "模擬測驗":
    st.subheader("✍️ 隨機模擬練習")
    
    if st.button("開始新題目") or 'quiz_word' not in st.session_state:
        st.session_state.quiz_word = df.sample(1).iloc[0]
        st.session_state.quiz_answered = False

    q = st.session_state.quiz_word
    st.info(f"請問這個單字的意思是： **{q['word']}**")
    
    # 產生選項
    correct_ans = q['translation']
    wrong_pool = df[df['translation'] != correct_ans]['translation'].unique().tolist()
    options = random.sample(wrong_pool, 3) + [correct_ans]
    random.shuffle(options)

    ans = st.radio("選擇答案：", options, key="quiz_radio")

    if st.button("提交答案"):
        st.session_state.quiz_answered = True
        if ans == correct_ans:
            st.success("✅ 答對了！")
        else:
            st.error(f"❌ 答錯囉！正確答案是：{correct_ans}")
            if q['word'] not in st.session_state.wrong_words:
                st.session_state.wrong_words.append(q['word'])

# --- 模式 3：弱點分析 ---
else:
    st.subheader("🕵️ 弱點偵察機")
    if not st.session_state.wrong_words:
        st.write("目前沒有錯題紀錄。")
    else:
        st.warning(f"目前累積 {len(st.session_state.wrong_words)} 個弱點單字")
        st.write(", ".join(st.session_state.wrong_words))
        if st.button("清除紀錄"):
            st.session_state.wrong_words = []
            st.rerun()
