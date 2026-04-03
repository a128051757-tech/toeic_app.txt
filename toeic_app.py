import streamlit as st
import pandas as pd
import random
from gtts import gTTS
import io
import re

# --- 1. 頁面優化設定 ---
st.set_page_config(page_title="育漢的多益戰情室", layout="centered")

# --- 2. 語音核心函數 ---
def speak(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3')
    except:
        st.error("語音讀取暫時發生錯誤。")

# --- 3. 資料載入與清理 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('toeic_data.csv')
        df.columns = [c.strip().lower() for c in df.columns]
        # 自動刪除重複單字，保持資料庫純淨
        df = df.drop_duplicates(subset=['word'], keep='first')
        return df
    except Exception as e:
        st.error(f"請確認 toeic_data.csv 檔案是否存在且格式正確。錯誤: {e}")
        return None

df = load_data()

# --- 4. 初始化 Session State (修正選項亂跳的關鍵) ---
if 'wrong_words' not in st.session_state: st.session_state.wrong_words = []
if 'quiz_word' not in st.session_state: st.session_state.quiz_word = None
if 'quiz_options' not in st.session_state: st.session_state.quiz_options = []
if 'cloze_word' not in st.session_state: st.session_state.cloze_word = None
if 'current_card' not in st.session_state: st.session_state.current_card = None

# --- 5. 主選單介面 ---
st.title("🎯 育漢的多益 AI 戰情室")
mode = st.sidebar.radio("切換模式", ["🎴 單字刷題", "✍️ 四選一測驗", "🧠 填空挑戰", "🕵️ 弱點分析"])

if df is not None:
    # --- 模式 A：單字刷題 ---
    if mode == "🎴 單字刷題":
        st.subheader("隨機單字卡")
        scenarios = ["全部"] + list(df['scenario'].unique())
        sel_scenario = st.selectbox("選擇情境", scenarios)
        
        if st.button("🔄 抽下一張") or st.session_state.current_card is None:
            filtered_df = df if sel_scenario == "全部" else df[df['scenario'] == sel_scenario]
            st.session_state.current_card = filtered_df.sample(1).iloc[0]

        c = st.session_state.current_card
        st.info(f"### {c['word']}")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("📢 聽發音"): speak(c['word'])
        with col2:
            st.write(f"**詞性：** {c['pos']} | **情境：** {c['scenario']}")
        
        with st.expander("點擊查看詳細內容"):
            st.success(f"**中文翻譯：** {c['translation']}")
            st.markdown(f"**例句：** \n> {c['example']}")
            if st.button("🗣️ 讀整句例句"): speak(c['example'])
            st.caption(f"**筆記：** {c['note']}")

    # --- 模式 B：四選一測驗 (已修正選項跳動 Bug) ---
    elif mode == "✍️ 四選一測驗":
        st.subheader("多益模擬選擇題")
        
        # 換題邏輯：只有點擊「下一題」或初始狀態才會重新產生選項
        if st.button("🆕 下一題") or st.session_state.quiz_word is None:
            st.session_state.quiz_word = df.sample(1).iloc[0]
            # 產生固定的選項並存在 Session State
            correct = st.session_state.quiz_word['translation']
            others = df[df['translation'] != correct]['translation'].unique().tolist()
            options = random.sample(others, min(len(others), 3)) + [correct]
            random.shuffle(options)
            st.session_state.quiz_options = options

        q = st.session_state.quiz_word
        st.info(f"請問這個單字的意思是： **{q['word']}**")
        
        # 使用存好的固定選項
        user_choice = st.radio("請選擇正確翻譯：", st.session_state.quiz_options, key="mcq_radio")

        if st.button("提交答案"):
            if user_choice == q['translation']:
                st.success("✅ 太強了，答對了！")
                speak(q['word'])
            else:
                st.error(f"❌ 答錯囉！正確答案是：{q['translation']}")
                if q['word'] not in st.session_state.wrong_words:
                    st.session_state.wrong_words.append(q['word'])

    # --- 模式 C：填空挑戰 (Part 5/6 強化) ---
    elif mode == "🧠 填空挑戰":
        st.subheader("上下句填空練習")
        
        if st.button("🆕 隨機出題") or st.session_state.cloze_word is None:
            # 確保有例句可以練習
            valid_df = df[df['example'].notna()]
            st.session_state.cloze_word = valid_df.sample(1).iloc[0]

        w = st.session_state.cloze_word
        # 使用正則表達式把句子中的單字隱藏 (不分大小寫)
        hidden_sentence = re.sub(w['word'], "__________", w['example'], flags=re.IGNORECASE)
        
        st.warning(f"### {hidden_sentence}")
        st.caption(f"提示：[{w['pos']}] {w['translation']}")
        
        user_input = st.text_input("請輸入正確單字：").strip()

        if st.button("檢查"):
            if user_input.lower() == w['word'].lower():
                st.success(f"🎊 正確！單字就是 **{w['word']}**")
                speak(w['word'])
            else:
                st.error(f"❌ 答錯了，正確答案是：**{w['word']}**")
                if w['word'] not in st.session_state.wrong_words:
                    st.session_state.wrong_words.append(w['word'])

    # --- 模式 D：弱點分析 ---
    elif mode == "🕵️ 弱點分析":
        st.subheader("偵測到的不熟單字")
        if not st.session_state.wrong_words:
            st.write("目前沒有錯題紀錄，繼續保持！")
        else:
            st.write(f"你目前有 {len(st.session_state.wrong_words)} 個弱點：")
            st.warning("、".join(st.session_state.wrong_words))
            if st.button("🗑️ 清空紀錄"):
                st.session_state.wrong_words = []
                st.rerun()

st.sidebar.write("---")
st.sidebar.caption("育漢專屬 · 2027 外商 AE 衝刺工具")
