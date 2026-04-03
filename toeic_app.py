import streamlit as st
import pandas as pd
import random
from gtts import gTTS
import io

# 1. 網頁基礎設定 (優化手機顯示)
st.set_page_config(page_title="育漢的多益戰情室", layout="centered", initial_sidebar_state="collapsed")

# 2. 語音功能函數
def speak(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3')
    except Exception as e:
        st.error("暫時無法讀取語音，請檢查網路連線。")

# 3. 資料讀取與去重 (工程師的資料清洗)
@st.cache_data
def load_data():
    try:
        # 讀取你的 toeic_data.csv
        df = pd.read_csv('toeic_data.csv')
        # 強制清理標頭：去空格、轉小寫
        df.columns = [c.strip().lower() for c in df.columns]
        # 自動去重：只要單字相同就只留下一筆
        df = df.drop_duplicates(subset=['word'], keep='first')
        return df
    except Exception as e:
        st.error(f"讀取資料庫失敗：{e}")
        return None

df = load_data()

# 4. 初始化 Session State (跨頁面紀錄數據)
if 'wrong_words' not in st.session_state:
    st.session_state.wrong_words = []
if 'current_card' not in st.session_state:
    st.session_state.current_card = None
if 'quiz_word' not in st.session_state:
    st.session_state.quiz_word = None

# --- 主選單 ---
st.title("🎯 育漢的多益戰情室")
mode = st.sidebar.radio("切換模式", ["🎴 單字刷題", "✍️ 模擬測驗", "🕵️ 弱點分析"])

if df is not None:
    # --- 模式 A：單字刷題 ---
    if mode == "🎴 單字刷題":
        st.subheader("隨機單字卡")
        
        # 情境篩選
        scenarios = ["全部"] + list(df['scenario'].unique())
        sel_scenario = st.selectbox("選擇情境", scenarios)
        filtered_df = df if sel_scenario == "全部" else df[df['scenario'] == sel_scenario]
        
        if st.button("🔄 抽下一張"):
            st.session_state.current_card = filtered_df.sample(1).iloc[0]

        if st.session_state.current_card is not None:
            card = st.session_state.current_card
            st.info(f"### {card['word']}")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("📢 聽發音"):
                    speak(card['word'])
            with col2:
                st.write(f"**音性：** {card['pos']} | **情境：** {card['scenario']}")
            
            with st.expander("點擊查看翻譯與例句"):
                st.success(f"**中文翻譯：** {card['translation']}")
                st.markdown(f"**例句：** \n> {card['example']}")
                if st.button("🗣️ 讀例句"):
                    speak(card['example'])
                st.write(f"---")
                st.caption(f"**筆記：** {card['note']}")

    # --- 模式 B：模擬測驗 ---
    elif mode == "✍️ 模擬測驗":
        st.subheader("隨機模擬練習")
        
        if st.button("🆕 下一題") or st.session_state.quiz_word is None:
            st.session_state.quiz_word = df.sample(1).iloc[0]
            st.session_state.quiz_answered = False

        q = st.session_state.quiz_word
        st.info(f"請問這個單字的意思是： **{q['word']}**")
        
        if st.button("📢 聽題目發音"):
            speak(q['word'])

        # 生成四選一選項
        correct_ans = q['translation']
        wrong_pool = df[df['translation'] != correct_ans]['translation'].unique().tolist()
        options = random.sample(wrong_pool, 3) + [correct_ans]
        random.shuffle(options)

        ans = st.radio("選擇答案：", options, key="quiz_radio")

        if st.button("提交答案"):
            if ans == correct_ans:
                st.success("✅ 答對了！太強了！")
            else:
                st.error(f"❌ 答錯囉！正確答案是：{correct_ans}")
                if q['word'] not in st.session_state.wrong_words:
                    st.session_state.wrong_words.append(q['word'])
        
    # --- 模式 C：弱點分析 ---
    elif mode == "🕵️ 弱點分析":
        st.subheader("弱點偵察機 (已紀錄錯題)")
        if not st.session_state.wrong_words:
            st.write("目前沒有錯題紀錄，你是多益戰神！")
        else:
            st.warning(f"目前累積 {len(st.session_state.wrong_words)} 個不熟單字：")
            st.write("、".join(st.session_state.wrong_words))
            
            if st.button("🗑️ 清空所有弱點紀錄"):
                st.session_state.wrong_words = []
                st.rerun()

st.sidebar.write("---")
st.sidebar.caption("育漢專屬 · 2027 外商 AE 衝刺工具")
