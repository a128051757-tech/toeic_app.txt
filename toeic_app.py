import streamlit as st
import pandas as pd
import random
from gtts import gTTS
import io
import re
import json
import os

# --- 1. 基礎設定與持久化邏輯 ---
st.set_page_config(page_title="育漢的多益戰情室", layout="centered")
PROGRESS_FILE = "learning_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=4)

def update_mastery(word, is_correct):
    progress = load_progress()
    current_score = progress.get(word, 0)
    if is_correct:
        new_score = min(current_score + 1, 5) # 最高 5 分
    else:
        new_score = 1 # 答錯重置回 1 分起跳
    progress[word] = new_score
    save_progress(progress)
    return new_score

# --- 2. 語音功能 ---
def speak(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3')
    except:
        st.error("語音讀取失敗")

# --- 3. 資料載入 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('toeic_data.csv')
        df.columns = [c.strip().lower() for c in df.columns]
        # 確保支援新舊 CSV 格式
        if 'type' not in df.columns: df['type'] = 'vocab'
        if 'options_hint' not in df.columns: df['options_hint'] = ""
        df['type'] = df['type'].fillna('vocab')
        #df = df.drop_duplicates(subset=['word'], keep='first')
        return df
    except Exception as e:
        st.error(f"資料讀取錯誤: {e}")
        return None

df = load_data()

# --- 4. 初始化 Session State (防止隨機選項跳動) ---
states = ['quiz_word', 'quiz_options', 'cloze_word', 'cloze_options', 'grammar_word', 'grammar_options', 'current_card']
for s in states:
    if s not in st.session_state: st.session_state[s] = None if 'word' in s or 'card' in s else []

# --- 5. 主選單 ---
st.title("🎯 育漢的多益 AI 戰情室")
mode = st.sidebar.radio("切換模式", ["🎴 單字刷題", "✍️ 四選一測驗", "🧠 填空挑戰", "📑 文法特訓", "🕵️ 弱點分析"])

if df is not None:
    # 模式 A：單字刷題
    if mode == "🎴 單字刷題":
        st.subheader("隨機單字卡")
        scenarios = ["全部"] + list(df['scenario'].unique())
        sel_scenario = st.selectbox("選擇情境", scenarios)
        if st.button("🔄 抽下一張") or st.session_state.current_card is None:
            f_df = df if sel_scenario == "全部" else df[df['scenario'] == sel_scenario]
            st.session_state.current_card = f_df.sample(1).iloc[0]
        
        c = st.session_state.current_card
        st.info(f"### {c['word']}")
        if st.button("📢 聽發音"): speak(c['word'])
        with st.expander("點擊查看詳情"):
            st.success(f"**中文翻譯：** {c['translation']}")
            st.markdown(f"**例句：** \n> {c['example']}")
            st.caption(f"**筆記：** {c['note']}")

    # 模式 B：四選一測驗
    elif mode == "✍️ 四選一測驗":
        if st.button("🆕 下一題") or st.session_state.quiz_word is None:
            st.session_state.quiz_word = df.sample(1).iloc[0]
            correct = st.session_state.quiz_word['translation']
            others = df[df['translation'] != correct]['translation'].unique().tolist()
            opts = random.sample(others, min(len(others), 3)) + [correct]
            random.shuffle(opts)
            st.session_state.quiz_options = opts

        q = st.session_state.quiz_word
        st.info(f"請問翻譯是： **{q['word']}**")
        ans = st.radio("選擇答案：", st.session_state.quiz_options, key="mcq")
        if st.button("提交答案"):
            if ans == q['translation']:
                st.success(f"✅ 正確！熟練度 +1")
                update_mastery(q['word'], True)
                speak(q['word'])
            else:
                st.error(f"❌ 錯誤。答案是：{q['translation']}")
                update_mastery(q['word'], False)

    # 模式 C：填空挑戰
    elif mode == "🧠 填空挑戰":
        q_type = st.radio("練習方式：", ["手寫提示", "四選一"], horizontal=True)
        if st.button("🆕 下一題") or st.session_state.cloze_word is None:
            st.session_state.cloze_word = df[df['example'].notna()].sample(1).iloc[0]
            correct = st.session_state.cloze_word['word']
            others = df[df['word'] != correct]['word'].unique().tolist()
            opts = random.sample(others, 3) + [correct]
            random.shuffle(opts)
            st.session_state.cloze_options = opts

        w = st.session_state.cloze_word
        hidden = re.sub(w['word'], "__________", w['example'], flags=re.IGNORECASE)
        st.warning(f"### {hidden}")
        st.caption(f"提示：{w['translation']} ({w['pos']})")

        if q_type == "手寫提示":
            hint = f"{w['word'][0]} " + "_ " * (len(w['word'])-1)
            st.code(f"提示：{hint}")
            u_input = st.text_input("輸入單字：").strip().lower()
            if st.button("檢查"):
                if u_input == w['word'].lower():
                    st.success("✅ 正確！")
                    update_mastery(w['word'], True)
                    speak(w['word'])
                else:
                    st.error(f"❌ 答案是：{w['word']}")
                    update_mastery(w['word'], False)
        else:
            u_choice = st.radio("選出正確單字：", st.session_state.cloze_options)
            if st.button("確認選擇"):
                if u_choice == w['word']:
                    st.success("✅ 正確！")
                    update_mastery(w['word'], True)
                    speak(w['word'])
                else:
                    st.error(f"❌ 答案是：{w['word']}")
                    update_mastery(w['word'], False)

    # 模式 D：文法特訓
    elif mode == "📑 文法特訓":
        g_df = df[df['type'] == 'grammar']
        if st.button("🆕 下一題") or st.session_state.grammar_word is None:
            if not g_df.empty:
                st.session_state.grammar_word = g_df.sample(1).iloc[0]
                opts = st.session_state.grammar_word['options_hint'].split(',')
                random.shuffle(opts)
                st.session_state.grammar_options = opts
        
        if st.session_state.grammar_word is not None:
            g = st.session_state.grammar_word
            hidden = re.sub(g['word'], "__________", g['example'], flags=re.IGNORECASE)
            st.info(f"### {hidden}")
            u_ans = st.radio("選擇詞性：", st.session_state.grammar_options)
            if st.button("提交"):
                if u_ans.strip() == g['word']:
                    st.success(f"✅ 正確！熟練度 +1")
                    update_mastery(g['word'], True)
                else:
                    st.error(f"❌ 答案是：{g['word']}")
                    update_mastery(g['word'], False)

    # 模式 E：弱點分析
    elif mode == "🕵️ 弱點分析":
        st.subheader("📊 學習進度戰情室")
        progress = load_progress()
        # 只顯示尚未精通 (小於 5 分) 的單字
        weak_words = {w: s for w, s in progress.items() if s < 5}
        
        if not weak_words:
            st.success("目前沒有弱點單字！")
        else:
            st.write(f"目前有 {len(weak_words)} 個單字正在攻克中：")
            for word, score in weak_words.items():
                col1, col2 = st.columns([1, 3])
                col1.write(f"**{word}**")
                col2.progress(score / 5)
            if st.button("🗑️ 重置所有進度"):
                if os.path.exists(PROGRESS_FILE): os.remove(PROGRESS_FILE)
                st.rerun()

st.sidebar.write("---")
total_mastered = len([s for s in load_progress().values() if s >= 5])
st.sidebar.metric("已精通單字", f"{total_mastered} / {len(df)}")
