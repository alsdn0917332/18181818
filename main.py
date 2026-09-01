import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="KBO 3D 리얼 피칭&타격 게임", page_icon="⚾", layout="wide")

# 1. KBO 구단별 투수 / 타자 명단 완전 분리 및 대폭 추가
ROSTER = {
    "기아": {
        "투수": ["양현종", "윤영철", "정해영", "전상현", "곽도규"],
        "타자": ["김도영", "최형우", "나성범", "김선빈", "소크라테스"]
    },
    "한화": {
        "투수": ["류현진", "문동주", "김서현", "주현상", "정우주"],
        "타자": ["노시환", "채은성", "안치홍", "페라자", "최인호"]
    },
    "삼성": {
        "투수": ["원태인", "코너", "레예스", "김재윤", "배찬승"],
        "타자": ["구자욱", "김영웅", "이재현", "박병호", "강민호"]
    },
    "kt": {
        "투수": ["고영표", "박영현", "엄상백", "쿠에바스", "김동현"],
        "타자": ["강백호", "로하스", "장성우", "황재균", "배정대"]
    },
    "키움": {
        "투수": ["안우진", "하영민", "조상우", "김선기", "정현우"],
        "타자": ["송성문", "이주형", "김혜성", "최주환", "도슨"]
    }
}

# 구종 및 특징
PITCH_TYPES = {
    "직구 (Four-Seam)": {"curve": "none"},
    "슬라이더 (Slider)": {"curve": "right"},
    "커브 (Curveball)": {"curve": "down"},
    "포크볼 (Forkball)": {"curve": "drop"},
    "체인지업 (Changeup)": {"curve": "left"}
}

st.title("⚾ 3D KBO 리얼 피칭 & 타격 시뮬레이터")

# 사이드바 설정
st.sidebar.header("⚙️ 경기 라인업 & 투구 설정")

# 투수 선택
pitcher_team = st.sidebar.selectbox("투수 구단", list(ROSTER.keys()), index=0)
pitcher_name = st.sidebar.selectbox("선택 투수 (투수 전용)", ROSTER[pitcher_team]["투수"])

st.sidebar.markdown("---")

# 타자 선택
batter_team = st.sidebar.selectbox("타자 구단", list(ROSTER.keys()), index=1)
batter_name = st.sidebar.selectbox("선택 타자 (타자 전용)", ROSTER[batter_team]["타자"])

st.sidebar.markdown("---")

# 구종 및 구속 설정
pitch_type_name = st.sidebar.selectbox("투구 구종 선택", list(PITCH_TYPES.keys()))
custom_speed = st.sidebar.slider("🔥 구속 직접 설정 (km/h)", min_value=120, max_value=165, value=152, step=1)

chosen_pitch = {
    "name": pitch_type_name,
    "speed": custom_speed,
    "curve": PITCH_TYPES[pitch_type_name]["curve"]
}

st.sidebar.markdown("""
---
### 🎮 게임 플레이 방법
1. **[🔥 투구 준비]** 버튼을 누릅니다.
2. 화면에 **5... 4... 3... 2... 1... 카운트다운**이 진행됩니다.
3. 5초 후 공이 **초고속으로 날아올 때 타이밍에 맞춰 [스페이스바]**를 눌러 타격하세요!
""")

# Three.js 기반 3D 야구장 & 타이밍 시스템
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        body {{ margin: 0; overflow: hidden; background: #050b14; font-family: 'Malgun Gothic', sans-serif; }}
        #game-container {{ width: 100vw; height: 580px; position: relative; }}
        #ui-overlay {{
            position: absolute; top: 15px; left: 15px; color: white;
            background: rgba(0,0,0,0.75); padding: 14px 22px; border-radius: 12px;
            font-size: 15px; border: 1px solid #333; z-index: 10;
        }}
        #countdown-display {{
            position: absolute; top: 35%; left: 50%; transform: translate(-50%, -50%);
            font-size: 80px; font-weight: 900; color: #ffeb3b;
            text-shadow: 0 0 30px rgba(255,235,59,0.8); z-index: 15; pointer-events: none;
        }}
        #hit-result {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            font-size: 42px; font-weight: 900; text-shadow: 0 0 20px #000;
            display: none; z-index: 20; text-align: center;
        }}
        #pitch-btn {{
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
            padding: 16px 45px; font-size: 22px; font-weight: bold; color: white;
            background: linear-gradient(135deg, #e63946, #b71c1c); border: none;
            border-radius: 35px; cursor: pointer; box-shadow: 0 5px 20px rgba(230,57,70,0.6);
            z-index: 10; transition: all 0.2s;
        }}
        #pitch-btn:disabled {{ background: #444; cursor: not-allowed; box-shadow: none; color: #888; }}
    </style>
</head>
<body>
    <div id="game-container">
        <div id="ui-overlay">
            <div><b>투수:</b> [{pitcher_team}] {pitcher_name}</div>
            <div><b>타자:</b> [{batter_team}] {batter_name}</div>
            <div style="color:#ffb703; margin-top:4px;"><b>구종:</b> {chosen_pitch['name']} ({chosen_pitch['speed']} km/h)</div>
            <div style="color: #4ea8de; margin-top: 6px;">💡 타격 키: <b>[스페이스바]</b></div>
        </div>
        
        <div id="countdown-display"></div>
        <div id="hit-result"></div>
        
        <button id="pitch-btn" onclick="startCountdown()">🔥 투구 준비 (5초 후 대기!)</button>
    </div>

    <script>
        const container = document.getElementById('game-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a192f); // 야간 경기 분위기

        // 카메라 (타자 타석 뒤쪽 연출 시점)
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.set(0, 1.35, 1.8);
        camera.lookAt(0, 1.2, -18.44);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);

        // 조명 (야간 조명 탑 효과)
        const light1 = new THREE.DirectionalLight(0xffffff, 1.2);
        light1.position.set(15, 30, 10);
        scene.add(light1);
        const light2 = new THREE.DirectionalLight(0x88aaff, 0.6);
        light2.position.set(-15, 30, -20);
        scene.add(light2);
        scene.add(new THREE.AmbientLight(0x404040));

        // --- 3D 야구장 인프라 생성 ---
        // 잔디
        const fieldGeo = new THREE.PlaneGeometry(120, 120);
        const fieldMat = new THREE.MeshLambertMaterial({{ color: 0x1b4332 }});
        const field = new THREE.Mesh(fieldGeo, fieldMat);
        field.rotation.x = -Math.PI / 2;
        scene.add(field);

        // 흙 다이아몬드
        const dirtGeo = new THREE.PlaneGeometry(8, 22);
        const dirtMat = new THREE.MeshLambertMaterial({{ color: 0x7f5539 }});
        const dirt = new THREE.Mesh(dirtGeo, dirtMat);
        dirt.rotation.x = -Math.PI / 2;
        dirt.position.set(0, 0.01, -10);
        scene.add(dirt);

        // 외야 외벽 (홈런 펜스)
        const fenceGeo = new THREE.CylinderGeometry(45, 45, 4, 32, 1, true, -Math.PI/3, Math.PI/1.5);
        const fenceMat = new THREE.MeshLambertMaterial({{ color: 0x003049, side: THREE.DoubleSide }});
        const fence = new THREE.Mesh(fenceGeo, fenceMat);
        fence.position.set(0, 2, -20);
        scene.add(fence);

        // 홈플레이트 & 스트라이크 존
        const zoneGeo = new THREE.BoxGeometry(0.5, 0.7, 0.02);
        const zoneMat = new THREE.MeshBasicMaterial({{ color: 0x00f5d4, wireframe: true, transparent: true, opacity: 0.4 }});
        const zone = new THREE.Mesh(zoneGeo, zoneMat);
        zone.position.set(0, 1.2, -0.5);
        scene.add(zone);

        // 야구공
        const ballGeo = new THREE.SphereGeometry(0.08, 16, 16);
        const ballMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.3 }});
        const ball = new THREE.Mesh(ballGeo, ballMat);
        const PITCHER_Z = -18.44;
        const BATTER_Z = 0;
        ball.position.set(0, 1.5, PITCHER_Z);
        scene.add(ball);

        // 3D 투수
        const pitcherGroup = new THREE.Group();
        const pBody = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 1.3), new THREE.MeshLambertMaterial({{ color: 0xd62828 }}));
        pBody.position.y = 0.65;
        pitcherGroup.add(pBody);
        pitcherGroup.position.set(0, 0, PITCHER_Z);
        scene.add(pitcherGroup);

        // 3D 배트
        const batGroup = new THREE.Group();
        const bat = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.015, 0.95), new THREE.MeshLambertMaterial({{ color: 0xe0a96d }}));
        bat.position.set(0, 0.45, 0);
        batGroup.add(bat);
        batGroup.position.set(0.45, 0.9, 0.1);
        batGroup.rotation.z = -Math.PI / 4;
        scene.add(batGroup);

        // --- 변수 및 시스템 ---
        let isWaiting = false;
        let isPitching = false;
        let countdownValue = 5;
        let countdownTimer = null;
        let pitchStartTime = 0;
        let hasSwung = false;

        const pitchData = {json.dumps(chosen_pitch)};
        // 구속(km/h)을 바탕으로 공이 날아오는 실제 비행 시간 계산 (초고속 연출)
        // 150km/h = 약 0.44초 만에 타석 도착
        const flightDuration = (18.44 / (pitchData.speed * 1000 / 3600)) * 1000; 

        function startCountdown() {{
            if (isWaiting || isPitching) return;
            
            isWaiting = true;
            hasSwung = false;
            countdownValue = 5;
            
            document.getElementById('pitch-btn').disabled = true;
            document.getElementById('hit-result').style.display = 'none';
            document.getElementById('countdown-display').innerText = countdownValue;

            ball.position.set(0, 1.5, PITCHER_Z);
            batGroup.rotation.y = 0;

            countdownTimer = setInterval(() => {{
                countdownValue--;
                if (countdownValue > 0) {{
                    document.getElementById('countdown-display').innerText = countdownValue;
                }} else {{
                    clearInterval(countdownTimer);
                    document.getElementById('countdown-display').innerText = "PITCH!";
                    setTimeout(() => {{ document.getElementById('countdown-display').innerText = ""; }}, 600);
                    
                    // 5초 카운트다운 종료 후 실제 초고속 투구 시작
                    launchPitch();
                }}
            }}, 1000);
        }}

        function launchPitch() {{
            isWaiting = false;
            isPitching = true;
            pitchStartTime = Date.now();
        }}

        // 스페이스바 타격 이벤트
        window.addEventListener('keydown', (e) => {{
            if (e.code === 'Space' && (isPitching || isWaiting) && !hasSwung) {{
                hasSwung = true;
                const swingTime = Date.now();
                
                // 배트 휘두르기
                batGroup.rotation.y = -Math.PI / 1.3;

                if (isPitching) {{
                    const elapsed = swingTime - pitchStartTime;
                    const diff = Math.abs(elapsed - (flightDuration * 0.85)); // 적정 타격 타이밍

                    let resText = "";
                    let resColor = "#ffeb3b";

                    if (diff < 40) {{
                        resText = "💥 대형 홈런 (HOMERUN)!!";
                        resColor = "#00f5d4";
                        ball.position.set(0, 25, -60); // 펜스 밖으로 날아감
                    }} else if (diff < 90) {{
                        resText = "⚾ 안타 (HIT)!";
                        resColor = "#52b788";
                    }} else if (diff < 150) {{
                        resText = "💨 파울 (FOUL)!";
                        resColor = "#ffb703";
                    }} else {{
                        resText = "❌ 헛스윙 삼진 (STRIKE)!";
                        resColor = "#e63946";
                    }}
                    showResult(resText, resColor);
                }} else if (isWaiting) {{
                    // 공이 날아오기 전에 성급하게 휘두른 경우
                    showResult("💨 너무 빠릅니다! (헛스윙)", "#e63946");
                }}
            }}
        }});

        function showResult(text, color) {{
            const el = document.getElementById('hit-result');
            el.innerText = text;
            el.style.color = color;
            el.style.display = 'block';
        }}

        // 렌더링 루프
        function animate() {{
            requestAnimationFrame(animate);

            if (isPitching) {{
                const elapsed = Date.now() - pitchStartTime;
                const progress = elapsed / flightDuration;

                if (progress <= 1.0) {{
                    // 구속에 따른 초고속 이동
                    ball.position.z = PITCHER_Z + (BATTER_Z - PITCHER_Z) * progress;

                    // 변화구 궤적
                    if (pitchData.curve === 'right') {{
                        ball.position.x = Math.sin(progress * Math.PI) * 0.6;
                    }} else if (pitchData.curve === 'left') {{
                        ball.position.x = -Math.sin(progress * Math.PI) * 0.6;
                    }} else if (pitchData.curve === 'drop' || pitchData.curve === 'down') {{
                        ball.position.y = 1.5 - Math.sin(progress * Math.PI) * 0.5;
                    }}
                }} else {{
                    if (!hasSwung) {{
                        showResult("⚾ 루킹 스트라이크!", "#ffb703");
                    }}
                    isPitching = false;
                    document.getElementById('pitch-btn').disabled = false;
                }}
            }}

            renderer.render(scene, camera);
        }}

        animate();
    </script>
</body>
</html>
"""

components.html(html_code, height=600)
