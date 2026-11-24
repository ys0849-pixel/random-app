import random
import time

import pandas as pd
import streamlit as st

st.set_page_config(page_title="반응속도 테스트", layout="wide")

TRIALS = 5  # 차수당 측정 횟수

st.markdown(
    """
    <style>
    .st-key-box_black button, .st-key-box_yellow button {
        width: 100%; height: 300px; border-radius: 16px;
        font-size: 28px; font-weight: 700; border: none;
    }
    .st-key-box_black button { background-color: #000; color: #fff; }
    .st-key-box_black button:hover { background-color: #111; color: #fff; }
    .st-key-box_yellow button { background-color: #FFD400; color: #000; }
    .st-key-box_yellow button:hover { background-color: #FFD400; color: #000; }
    </style>
    """,
    unsafe_allow_html=True,
)

ss = st.session_state
ss.setdefault("round", 1)        # 현재 차수
ss.setdefault("times", [])       # 현재 차수 측정값(ms)
ss.setdefault("phase", "idle")   # idle / waiting / ready
ss.setdefault("t0", None)        # 노란색 표시 시각
ss.setdefault("history", {})     # {차수: [측정값]}
ss.setdefault("msg", "")


def next_round():
    ss.round += 1
    ss.times = []
    ss.phase = "idle"
    ss.t0 = None
    ss.msg = ""


def show_result():
    st.title(f"📊 {ss.round}차 테스트 결과")
    ss.history[ss.round] = ss.times

    rows = []
    for r, ts in ss.history.items():
        s = pd.Series(ts)
        rows.append({
            "차수": f"{r}차",
            "평균(ms)": round(s.mean(), 1),
            "최대(ms)": round(s.max(), 1),
            "최소(ms)": round(s.min(), 1),
            "편차(표준편차, ms)": round(s.std(ddof=0), 1),
        })
    df = pd.DataFrame(rows).set_index("차수")

    left, right = st.columns(2)
    with left:
        st.subheader("차수별 통계")
        st.dataframe(df, use_container_width=True)
        st.caption("이번 차수 측정값: " + ", ".join(f"{t:.0f}ms" for t in ss.times))
    with right:
        st.subheader("차수별 평균 반응속도 (ms)")
        st.line_chart(df[["평균(ms)"]])

    st.divider()
    st.button(f"{ss.round + 1}차 테스트 하러 가기", type="primary",
              use_container_width=True, on_click=next_round)


def show_test():
    st.title(f"⚡ 반응속도 테스트 - {ss.round}차")
    st.progress(len(ss.times) / TRIALS, text=f"{len(ss.times) + 1} / {TRIALS}회")
    if ss.msg:
        st.info(ss.msg)

    if ss.phase == "idle":
        if st.button("여기를 클릭하면 시작!\n노란색으로 바뀌면 최대한 빨리 클릭하세요", key="box_black"):
            ss.phase = "waiting"
            ss.msg = ""
            st.rerun()

    elif ss.phase == "waiting":
        # 대기 중 클릭하면 이 rerun이 sleep을 끊고 True로 들어옴 → 너무 빠른 클릭
        if st.button("기다리세요...", key="box_black"):
            ss.phase = "idle"
            ss.msg = "❌ 너무 일찍 클릭했어요! 다시 시도하세요."
            st.rerun()
        time.sleep(random.uniform(1.5, 5.0))   # 랜덤 대기
        ss.phase = "ready"
        ss.t0 = None
        st.rerun()

    elif ss.phase == "ready":
        clicked = st.button("지금 클릭!", key="box_yellow")
        if clicked and ss.t0 is not None:
            rt = (time.time() - ss.t0) * 1000
            ss.times.append(rt)
            ss.phase = "idle"
            ss.t0 = None
            ss.msg = f"✅ {rt:.0f} ms"
            st.rerun()
        elif ss.t0 is None:
            ss.t0 = time.time()   # 노란 상자가 그려진 직후부터 측정 시작


if len(ss.times) >= TRIALS:
    show_result()
else:
    show_test()
