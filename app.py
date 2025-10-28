# -*- coding: utf-8 -*-
"""
한신 초등 이야기 메이커 (AI와 아이가 번갈아 쓰는 버전)
"""
import os
import re
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="한신 초등 이야기 메이커", page_icon="✨")

# 로고 표시
if os.path.exists("logo.PNG"):
    st.image("logo.PNG", width=120)

st.title("✨ 한신 초등학교 친구들의 이야기 실력을 볼까요?")
st.caption("AI와 함께 번갈아가며 멋진 이야기를 만들어 봐요!")

# OpenAI 연결
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    st.error("❌ OPENAI_API_KEY가 설정되지 않았어요. Streamlit Secrets에 추가해 주세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_KEY)

# 학생 정보
st.subheader("👧 학생 정보 입력")
c1, c2, c3 = st.columns(3)
cls = c1.text_input("학급 (예: 3-2)")
num = c2.text_input("번호")
name = c3.text_input("이름")

# 금칙어 필터
BANNED_PATTERNS = [
    r"살인", r"죽이", r"폭력", r"피바다", r"학대", r"총", r"칼", r"폭탄",
    r"kill", r"murder", r"gun", r"knife", r"blood", r"assault", r"bomb",
    r"성\s*행위", r"야동", r"포르노", r"음란", r"가슴", r"성기", r"자위",
    r"porn", r"sex", r"xxx", r"nude", r"naked",
]
BAN_RE = re.compile("|".join(BANNED_PATTERNS), re.IGNORECASE)

def words_valid(words):
    for w in words:
        if not w:
            return False, "단어 3개를 모두 입력해 주세요."
        if BAN_RE.search(w):
            return False, "적절하지 않은 단어입니다. 다시 입력해 주세요."
    return True, "OK"


# 주인공 만들기
st.subheader("1️⃣ 좋아하는 단어 3개로 주인공 만들기")
col1, col2, col3 = st.columns(3)
w1 = col1.text_input("단어 1", max_chars=12)
w2 = col2.text_input("단어 2", max_chars=12)
w3 = col3.text_input("단어 3", max_chars=12)

st.session_state.setdefault("character_desc", "")

if st.button("주인공 만들기 👤✨", use_container_width=True):
    words = [w1.strip(), w2.strip(), w3.strip()]
    ok, msg = words_valid(words)
    if not ok:
        st.error(msg)
    else:
        prompt = (
            f"'{words[0]}', '{words[1]}', '{words[2]}' 세 단어를 모두 사용해서 "
            "초등학교 3학년이 이해하기 쉬운 말로 주인공의 이름, 성격, 좋아하는 일, 사는 곳을 소개해 주세요."
        )
        try:
            resp = client.responses.create(model="gpt-4o-mini", input=prompt, max_output_tokens=400)
            desc = getattr(resp, "output_text", "").strip() or resp.output[0].content[0].text.strip()
            st.session_state["character_desc"] = desc
            st.success("💫 주인공이 완성되었어요!")
        except Exception as e:
            st.error(f"주인공 생성 중 문제가 발생했어요: {e}")

if st.session_state["character_desc"]:
    st.markdown("### 👤 주인공 소개")
    st.write(st.session_state["character_desc"])

# 이야기 단계
TITLES = [
    "옛날에", "그리고 매일", "그러던 어느 날",
    "그래서", "그래서", "그래서", "마침내", "그날 이후"
]

st.divider()
st.subheader("2️⃣ AI와 함께 번갈아 이야기를 써요 ✍️")

for i in range(8):
    st.session_state.setdefault(f"story_{i}", "")

def build_prev_context(idx):
    """이전 단계까지의 내용을 합칩니다."""
    return " ".join(st.session_state[f"story_{j}"] for j in range(idx) if st.session_state[f"story_{j}"]).strip()

def generate_story(title, idx):
    """AI가 현재 단계에 맞는 이야기를 생성합니다."""
    character = st.session_state["character_desc"]
    prev_text = build_prev_context(idx)
    prompt = (
        f"지금까지의 이야기를 바탕으로 '{title}'로 시작하는 이야기를 써 주세요.\n"
        "초등학교 3학년이 이해하기 쉬운 따뜻한 문체로 200~300자 정도로 써 주세요.\n\n"
        f"주인공 정보:\n{character}\n\n지금까지의 이야기:\n{prev_text}"
    )
    try:
        with st.spinner("이야기를 만드는 중이에요..."):
            resp = client.responses.create(model="gpt-4o-mini", input=prompt, max_output_tokens=600)
        text = getattr(resp, "output_text", "").strip() or resp.output[0].content[0].text.strip()
        if not text.startswith(title):
            text = f"{title} " + text
        st.session_state[f"story_{idx}"] = text
    except Exception as e:
        st.error(f"이야기 생성 중 문제가 발생했어요: {e}")

# 본문 UI
for i, title in enumerate(TITLES):
    st.markdown(f"#### {title}")

    # AI가 생성해야 하는 칸
    if i in [0, 2, 4]:
        if st.button(f"{title} 자동 생성 🪄", key=f"auto_btn_{i}", use_container_width=True):
            generate_story(title, i)
        if st.session_state[f"story_{i}"]:
            st.markdown(f"🪄 **{title} 이야기**")
            st.write(st.session_state[f"story_{i}"])

    # 아이가 직접 쓰는 칸
    else:
        st.session_state[f"story_{i}"] = st.text_area(
            f"{title} 내용을 적어보세요",
            value=st.session_state[f"story_{i}"],
            height=100,
            key=f"story_input_{i}"
        )

# 완성된 이야기
if any(st.session_state[f"story_{i}"].strip() for i in range(8)):
    st.divider()
    st.subheader("🎉 지금까지 완성된 이야기")
    combined_story = "\n\n".join(
        f"**{TITLES[i]}**\n{st.session_state[f'story_{i}']}" for i in range(8) if st.session_state[f"story_{i}"].strip()
    )
    st.write(combined_story)
    filename = f"{cls}_{num}_{name}_story.txt".replace(" ", "_") or "my_story.txt"
    st.download_button("📥 이야기 저장하기 (txt)", data=combined_story, file_name=filename, mime="text/plain")
