# -*- coding: utf-8 -*-
"""
한신 초등 이야기 메이커 (OpenAI 전용, 자동 표시 최종 버전)
"""
import os
import re
import streamlit as st
from openai import OpenAI

# ---------------------------------------
# 페이지 설정
# ---------------------------------------
st.set_page_config(page_title="한신 초등 이야기 메이커 (OpenAI)", page_icon="✨")

if os.path.exists("logo.PNG"):
    st.image("logo.PNG", width=120)

st.title("✨ 한신 초등학교 친구들의 이야기 실력을 볼까요?")
st.caption("좋아하는 단어로 주인공을 만들고, 각 칸의 버튼으로 이야기를 이어가요!")

# ---------------------------------------
# OpenAI API 설정
# ---------------------------------------
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    st.error("❌ OPENAI_API_KEY가 설정되지 않았어요. Streamlit Secrets에 추가해 주세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_KEY)

# ---------------------------------------
# 학생 정보
# ---------------------------------------
st.subheader("👧 학생 정보 입력")
c1, c2, c3 = st.columns(3)
cls = c1.text_input("학급 (예: 3-2)")
num = c2.text_input("번호")
name = c3.text_input("이름")

# ---------------------------------------
# 금칙어 필터
# ---------------------------------------
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


# ---------------------------------------
# 주인공 만들기
# ---------------------------------------
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
            "초등학교 3학년이 읽기 쉬운 한국어로, "
            f"'{words[0]}', '{words[1]}', '{words[2]}' 세 단어를 모두 사용해서 "
            "주인공의 이름, 성격, 좋아하는 일, 사는 곳을 3~4문장으로 소개해 주세요. "
            "부드럽고 따뜻한 말투로 써 주세요."
        )
        try:
            resp = client.responses.create(
                model="gpt-4o-mini",
                input=prompt,
                max_output_tokens=400,
            )
            desc = getattr(resp, "output_text", "").strip() or (
                resp.output[0].content[0].text.strip() if getattr(resp, "output", None) else ""
            )
            if desc:
                st.session_state["character_desc"] = desc
                st.success("💫 주인공이 완성되었어요!")
                st.rerun()
            else:
                st.warning("응답은 성공했지만 내용이 비어 있어요. 잠시 후 다시 시도해 주세요.")
        except Exception as e:
            st.error(f"주인공 생성 중 문제가 발생했어요: {e}")

# ---------------------------------------
# 주인공 설명 출력
# ---------------------------------------
if st.session_state["character_desc"]:
    st.markdown("### 👤 주인공 소개")
    st.write(st.session_state["character_desc"])
else:
    st.info("먼저 단어 3개로 주인공을 만들어 주세요.")

# ---------------------------------------
# 8단 이야기
# ---------------------------------------
if st.session_state["character_desc"]:
    st.divider()
    st.subheader("2️⃣ 주인공의 이야기를 써 볼까요? ✍️")

    TITLES = [
        "옛날에", "그리고 매일", "그러던 어느 날",
        "그래서", "그래서", "그래서", "마침내", "그날 이후"
    ]

    for i in range(8):
        st.session_state.setdefault(f"story_{i}", "")

    # 이전 칸 내용 연결
    def build_prev_context(idx):
        return " ".join(
            [st.session_state[f"story_{j}"] for j in range(idx) if st.session_state[f"story_{j}"]]
        ).strip()

    # 자동 생성 함수 (수정된 버전: 생성 후 바로 표시)
    def generate_auto(title_prefix, idx):
        character = st.session_state["character_desc"]
        prev_all = build_prev_context(idx)
        prompt = (
            f"첫 문장은 반드시 '{title_prefix}'로 시작하고, "
            "초등학교 3학년이 이해하기 쉬운 따뜻한 문체로 "
            "200~300자 분량의 문단을 작성해 주세요. "
            "주인공 정보와 지금까지의 이야기를 자연스럽게 이어 주세요.\n\n"
            f"주인공 정보:\n{character}\n\n지금까지의 이야기:\n{prev_all}"
        )

        try:
            resp = client.responses.create(model="gpt-4o-mini", input=prompt, max_output_tokens=600)
            text = getattr(resp, "output_text", "").strip() or (
                resp.output[0].content[0].text.strip() if getattr(resp, "output", None) else ""
            )
            if not text:
                st.warning("응답이 비어 있어요. 잠시 후 다시 시도해 주세요.")
                return
            if not text.startswith(title_prefix):
                text = f"{title_prefix} " + text
            st.session_state[f"story_{idx}"] = text
            st.success(f"✨ '{title_prefix}' 이야기 자동 생성 완료!")
            st.rerun()  # ✅ 새로고침으로 바로 표시
        except Exception as e:
            st.error(f"자동 생성 중 오류 발생: {e}")

    # 입력 칸 출력
    for i, title in enumerate(TITLES):
        st.markdown(f"#### {title}")
        is_auto = i in [0, 2, 4]  # 1,3,5번째 칸 자동
        if is_auto:
            st.text_area(
                f"{title} (자동 생성 결과)",
                value=st.session_state[f"story_{i}"],
                height=120,
                disabled=True,
                key=f"auto_output_{i}",
            )
            if st.button(f"{title} 자동 생성 🪄", use_container_width=True, key=f"auto_btn_{i}"):
                generate_auto(title, i)
        else:
            st.session_state[f"story_{i}"] = st.text_area(
                f"{title} 내용을 적어보세요",
                value=st.session_state[f"story_{i}"],
                height=90,
                key=f"story_input_{i}",
            )

    # ---------------------------------------
    # 완성된 이야기 출력
    # ---------------------------------------
    if all(st.session_state[f"story_{i}"].strip() for i in range(8)):
        st.divider()
        st.subheader("🎉 완성된 이야기")

        story_text = "\n\n".join(
            f"**{TITLES[i]}**\n{st.session_state[f'story_{i}']}" for i in range(8)
        )

        try:
            polish_prompt = (
                "다음 8단 이야기를 자연스럽게 하나의 이야기로 정리해 주세요. "
                "초등학교 3학년이 이해하기 쉬운 문장으로 써 주세요.\n\n"
                + story_text
            )
            resp = client.responses.create(model="gpt-4o-mini", input=polish_prompt, max_output_tokens=700)
            final_story = getattr(resp, "output_text", "").strip() or (
                resp.output[0].content[0].text.strip() if getattr(resp, "output", None) else story_text
            )
        except Exception:
            final_story = story_text

        st.write(final_story)
        safe_name = f"{cls}_{num}_{name}_story.txt".replace(" ", "_") or "my_story.txt"
        st.download_button(
            "📥 완성된 이야기 저장하기 (txt)",
            data=final_story,
            file_name=safe_name,
            mime="text/plain",
        )
