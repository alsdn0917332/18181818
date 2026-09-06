import streamlit as st
import numpy as np
import plotly.graph_objects as go
import random

# 페이지 기본 설정
st.set_page_config(page_title="KBO 3D 야구 게임", layout="wide")

# 1. 세션 상태 초기화
if 'inning' not in st.session_state:
    st.session_state.inning = 1
    st.session_state.is_top = True
    st.session_state.score = {'HOME': 0, 'AWAY': 0}
    st.session_state.batter_hits = [0] * 9
    st.session_state.current_batter_idx = 0
    st.session_state.strikes = 0
    st.session_state.balls = 0
    st.session_state.outs = 0
    st.session_state.last_result = "투구 대기 중..."

# 2. 사이드바 설정
st.sidebar.header("⚙️ 경기 및 투구 설정")
pitch_type = st.sidebar.selectbox("구종 선택", ["직구 (Four-Seam)", "슬라이더 (Slider)"])
is_pitcher_mode = st.sidebar.checkbox("투수 모드 (직접 조준)", value=False)

if is_pitcher_mode:
    target_x = st.sidebar.slider("좌우 로케이션 (X)", -1.5, 1.5, 0.0, 0.1)
    target_y = st.sidebar.slider("상하 로케이션 (Y)", -1.5, 1.5, 0.0, 0.1)
else:
    target_x = round(random.uniform(-1.2, 1.2), 2)
    target_y = round(random.uniform(-1.2, 1.2), 2)

# 3. 게임 규칙 처리 함수
def reset_count():
    st.session_state.strikes = 0
    st.session_state.balls = 0
    st.session_state.current_batter_idx = (st.session_state.current_batter_idx + 1) % 9

def check_rules():
    if st.session_state.strikes >= 3:
        st.session_state.outs += 1
        st.session_state.last_result = "삼진 아웃!"
        reset_count()
    elif st.session_state.balls >= 4:
        st.session_state.last_result = "볼넷 (출루)"
        reset_count()

    if st.session_state.outs >= 3:
        st.session_state.outs = 0
        reset_count()
        if not st.session_state.is_top:
            st.session_state.inning += 1
        st.session_state.is_top = not st.session_state.is_top
        st.session_state.last_result = f"3아웃! {st.session_state.inning}이닝으로 교대합니다."

def process_pitch(did_swing, timing):
    final_x = target_x + random.uniform(-0.1, 0.1)
    final_y = target_y + random.uniform(-0.1, 0.1)
    
    is_in_strike = (-0.8 <= final_x <= 0.8) and (-0.8 <= final_y <= 0.8)
    
    if not did_swing:
        if is_in_strike:
            st.session_state.strikes += 1
            st.session_state.last_result = "스트라이크! (루킹)"
        else:
            st.session_state.balls += 1
            st.session_state.last_result = "볼!"
    else:
        abs_timing = abs(timing)
        if abs_timing < 0.1:
            st.session_state.last_result = "홈런!!"
            st.session_state.batter_hits[st.session_state.current_batter_idx] += 1
            st.session_state.score['AWAY' if st.session_state.is_top else 'HOME'] += 1
            reset_count()
        elif abs_timing < 0.25:
            st.session_state.last_result = "안타!"
            st.session_state.batter_hits[st.session_state.current_batter_idx] += 1
            reset_count()
        elif abs_timing < 0.4:
            st.session_state.last_result = "아웃 (땅볼/플라이)"
            st.session_state.outs += 1
            reset_count()
        else:
            st.session_state.strikes += 1
            st.session_state.last_result = "헛스윙 스트라이크!"

    check_rules()
    return final_x, final_y

# 4. 화면 UI
st.title("⚾ 3D KBO 야구 경기장")

half = "초" if st.session_state.is_top else "말"
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.info(f"**전광판** | {st.session_state.inning}회{half} | AWAY: **{st.session_state.score['AWAY']}** vs HOME: **{st.session_state.score['HOME']}**")
with col2:
    st.warning(f"**카운트** | S: {st.session_state.strikes} | B: {st.session_state.balls} | O: {st.session_state.outs}")
with col3:
    st.success(f"**현재 타자**: {st.session_state.current_batter_idx + 1}번 타자")

hits_display = " ".join([f"[{i+1}번:{h}안타]" for i, h in enumerate(st.session_state.batter_hits)])
st.caption(f"📊 타자별 안타 현황: {hits_display}")

col_act1, col_act2 = st.columns(2)
with col_act1:
    timing_val = st.slider("스윙 타이밍 (-0.5: 빠름, 0.0: 정타, 0.5: 느림)", -0.5, 0.5, 0.0, 0.05)
with col_act2:
    st.write("")
    st.write("")
    btn_swing = st.button("⚾ 스윙 하기!", use_container_width=True)
    btn_look = st.button("👀 지켜보기", use_container_width=True)

pitched_x, pitched_y = target_x, target_y
if btn_swing:
    pitched_x, pitched_y = process_pitch(did_swing=True, timing=timing_val)
elif btn_look:
    pitched_x, pitched_y = process_pitch(did_swing=False, timing=0.0)

st.subheader(f"판정 결과: {st.session_state.last_result}")

# 5. 3D 궤적 그래픽 (Plotly)
z_range = np.linspace(18.4, 0, 30)
x_path, y_path = [], []

for z in z_range:
    progress = (18.4 - z) / 18.4
    break_x = 0
    if "슬라이더" in pitch_type and progress > 0.5:
        break_x = ((progress - 0.5) ** 2) * 1.5
        
    curr_x = (pitched_x * progress) + break_x
    curr_y = (pitched_y * progress) + (1.2 * (1 - progress))
    x_path.append(curr_x)
    y_path.append(curr_y)

fig = go.Figure()

# 스트라이크 존 3D
fig.add_trace(go.Scatter3d(
    x=[-0.8, 0.8, 0.8, -0.8, -0.8, -0.8, 0.8, 0.8, -0.8, -0.8],
    y=[-0.8, -0.8, 0.8, 0.8, -0.8, -0.8, -0.8, 0.8, 0.8, -0.8],
    z=[0, 0, 0, 0, 0, 0.1, 0.1, 0.1, 0.1, 0.1],
    mode='lines',
    line=dict(color='red', width=4),
    name='스트라이크 존'
))

# 3D 투구 궤적
fig.add_trace(go.Scatter3d(
    x=x_path, y=y_path, z=z_range,
    mode='lines+markers',
    marker=dict(size=4, color='white'),
    line=dict(color='yellow', width=6),
    name='투구 궤적'
))

# 최종 위치
fig.add_trace(go.Scatter3d(
    x=[pitched_x], y=[pitched_y], z=[0],
    mode='markers',
    marker=dict(size=10, color='red'),
    name='최종 로케이션'
))

fig.update_layout(
    scene=dict(
        xaxis=dict(title='좌/우 (X)', range=[-2, 2]),
        yaxis=dict(title='상/하 (Y)', range=[-2, 2]),
        zaxis=dict(title='투수판 -> 홈 (Z)', range=[0, 20]),
        aspectratio=dict(x=1, y=1, z=2)
    ),
    margin=dict(l=0, r=0, b=0, t=0),
    height=500
)

st.plotly_chart(fig, use_container_width=True)
