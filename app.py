import random
import time

import pandas as pd
import streamlit as st

st.set_page_config(page_title="반응속도 테스트", layout="wide")

TRIALS = 5          # 차수당 측정 횟수
TIMEOUT_SEC = 5     # 노란색 표시 후 제한 시간(초)

st.markdown(
    """
    <style>
    .block-container { max-width: 100% !important; padding-left: 1rem; padding-right: 1rem; }

    .st-key-box_black, .st-key-box_yellow,
    .st-key-box_black div[data-testid="stButton"],
    .st-key-box_yellow div[data-testid="stButton"] { width: 100% !important; }

    .st-key-box_black button, .st-key-box_yellow button {
        width: 100% !important; height: 350px; border-radius: 16px;
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
ss.setdefault("phase", "idle")   # idle(시작 대기) / waiting(랜덤 대기) / ready(노란색)
ss.setdefault("t0", None)        # 노란색 표시 시각
ss.setdefault("ready_at", None)  # 노란색으로 바뀔 예정 시각
ss.setdefault("history", {})     # {차수: [측정값]}
ss.setdefault("msg", "")


def next_round():
    ss.round += 1
    ss.times = []
    ss.phase = "idle"
    ss.t0 = None
    ss.ready_at = None
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

    # 1) 시작 대기: 최초 1회만 클릭
    if ss.phase == "idle":
        if st.button("여기를 한 번 클릭하면 테스트가 시작됩니다\n"
                     "(이후엔 자동 진행 · 노란색이 되면 최대한 빨리 클릭!)",
                     key="box_black"):
            ss.phase = "waiting"
            ss.ready_at = None
            ss.msg = ""
            st.rerun()

    # 2) 랜덤 대기 (검은 상자) - 이 동안의 클릭은 완전히 무시
    elif ss.phase == "waiting":
        if ss.ready_at is None:   # 새 대기일 때만 랜덤 시간 결정
            ss.ready_at = time.time() + random.uniform(1.5, 5.0)

        st.button("기다리세요...", key="box_black")   # 클릭해도 반환값 무시

        # 클릭으로 재실행돼도 목표 시각은 그대로 → 남은 시간만큼만 대기
        time.sleep(max(0, ss.ready_at - time.time()))
        ss.ready_at = None
        ss.phase = "ready"
        ss.t0 = None
        st.rerun()

    # 3) 노란색: 클릭 시 측정, 5초 지나면 초기화
    elif ss.phase == "ready":
        clicked = st.button("지금 클릭!", key="box_yellow")

        if clicked and ss.t0 is not None:
            rt = (time.time() - ss.t0) * 1000
            ss.times.append(rt)
            ss.t0 = None
            ss.msg = f"✅ {rt:.0f} ms"
            ss.phase = "waiting"   # 클릭 없이 다음 측정 자동 시작
            st.rerun()
        else:
            if ss.t0 is None:
                ss.t0 = time.time()
            remaining = TIMEOUT_SEC - (time.time() - ss.t0)
            time.sleep(max(0, remaining))
            ss.times = []
            ss.t0 = None
            ss.phase = "idle"
            ss.msg = (f"⏰ {TIMEOUT_SEC}초 안에 클릭하지 않아 횟수를 초기화하고 멈췄습니다. "
                      "검은 상자를 클릭하면 처음부터 다시 시작합니다.")
            st.rerun()


if len(ss.times) >= TRIALS:
    show_result()
else:
    show_test()
