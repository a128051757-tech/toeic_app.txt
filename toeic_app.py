import streamlit as st
import pandas as pd
import random
from gtts import gTTS
import io
import re

# 頁面基礎設定
st.set_page_config(page_title="育漢的多益戰情室", layout="centered")

def speak(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3')
    except:
        st.error("語音暫時無法使用。")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv('toeic_data.csv')
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.drop_duplicates(subset=['word'], keep='first')
        return df
    except:
        return None

df = load_data()

# 初始化所有 Session State
states = ['wrong_words', 'quiz_word', 'quiz_options', 'cloze_word', 'cloze_options', 'current_card']
for s in states:
    if s not in st.session_state: st.session_state[s] = None if 'word' in s or 'card' in s else []

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

    # --- 模式 C：填空挑戰 (新增提示與選擇功能) ---
    if mode == "🧠 填空挑戰":
        st.subheader("上下文填空 (Part 5/6 強化)")
        
        # 難度設定
        quiz_type = st.radio("選擇練習方式：", ["手寫填空 (有提示)", "選擇填空 (4選1)"], horizontal=True)
        
        if st.button("🆕 換一題") or st.session_state.cloze_word is None:
            valid_df = df[df['example'].notna()]
            st.session_state.cloze_word = valid_df.sample(1).iloc[0]
            # 為「選擇填空」準備選項
            correct = st.session_state.cloze_word['word']
            others = df[df['word'] != correct]['word'].unique().tolist()
            opts = random.sample(others, 3) + [correct]
            random.shuffle(opts)
            st.session_state.cloze_options = opts

        w = st.session_state.cloze_word
        hidden_sentence = re.sub(w['word'], "__________", w['example'], flags=re.IGNORECASE)
        
        st.warning(f"### {hidden_sentence}")
        st.caption(f"中文翻譯：{w['translation']} ({w['pos']})")

        if quiz_type == "手寫填空 (有提示)":
            # 提示邏輯：顯示首字母 + 長度
            hint = f"{w['word'][0]} " + "_ " * (len(w['word']) - 1)
            st.code(f"提示 (長度 {len(w['word'])}): {hint}")
            user_input = st.text_input("請輸入正確單字：", key="cloze_text").strip()
            
            if st.button("檢查答案"):
                if user_input.lower() == w['word'].lower():
                    st.success(f"🎊 正確！答案是 {w['word']}")
                    speak(w['word'])
                else:
                    st.error(f"❌ 答錯了，再想一下？ (正確答案：{w['word']})")
                    if w['word'] not in st.session_state.wrong_words:
                        st.session_state.wrong_words.append(w['word'])

        else: # 選擇填空
            user_choice = st.radio("請從下方選出正確單字：", st.session_state.cloze_options)
            if st.button("確認選擇"):
                if user_choice == w['word']:
                    st.success(f"✅ 答對了！{w['word']}")
                    speak(w['word'])
                else:
                    st.error(f"❌ 不對喔，正確答案是：{w['word']}")
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
    # --- 模式 E：文法特訓 (New!) ---
    if mode == "📑 文法特訓":
        st.subheader("多益 Part 5 詞性變化專區")
        
        # 只過濾出文法題
        grammar_df = df[df['type'] == 'grammar']
        
        if st.button("🆕 下一題") or st.session_state.grammar_word is None:
            if not grammar_df.empty:
                st.session_state.grammar_word = grammar_df.sample(1).iloc[0]
                # 解析四個選項
                opts = st.session_state.grammar_word['options_hint'].split(',')
                random.shuffle(opts)
                st.session_state.grammar_options = opts
            else:
                st.warning("目前 CSV 中沒有 type 為 grammar 的資料。")

        if st.session_state.grammar_word is not None:
            g = st.session_state.grammar_word
            # 隱藏題目中的答案
            hidden_sentence = re.sub(g['word'], "__________", g['example'], flags=re.IGNORECASE)
            
            st.info(f"### {hidden_sentence}")
            st.caption(f"提示：情境 - {g['scenario']} | 翻譯：{g['translation']}")
            
            user_choice = st.radio("請選擇最符合語法的詞性：", st.session_state.grammar_options)
            
            if st.button("提交"):
                if user_choice.strip() == g['word']:
                    st.success(f"✅ 正確！這裡需要一個 {g['pos']}。")
                    speak(g['word'])
                else:
                    st.error(f"❌ 不對喔，正確答案是：{g['word']} ({g['pos']})")
                    if g['word'] not in st.session_state.wrong_words:
                        st.session_state.wrong_words.append(g['word'])
st.sidebar.write("---")
st.sidebar.caption("育漢專屬 · 2027 外商 AE 衝刺工具")
