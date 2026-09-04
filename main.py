import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="KBO 3D 프로야구", page_icon="⚾", layout="wide")

# 사이드바에서 구속 및 구종 설정
st.sidebar.header("⚙️ 경기 & 투구 설정")
pitch_type = st.sidebar.selectbox("구종 선택", ["직구", "슬라이더", "커브", "포크볼", "체인지업"])
pitch_speed = st.sidebar.slider("구속 설정 (km/h)", 130, 165, 152)

st.title("⚾ 3D KBO 모바일 스타일 실전 야구 게임")

# HTML/Three.js + 모바일 야구 UI 연출
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        body {{ margin: 0; overflow: hidden; background: #000; font-family: 'Malgun Gothic', sans-serif; user-select: none; }}
        #game-container {{ width: 100vw; height: 680px; position: relative; background: #111; }}

        /* --- 1. 좌상단 스코어보드 --- */
        .scoreboard {{
            position: absolute; top: 15px; left: 15px; width: 220px;
            background: rgba(15, 23, 42, 0.85); border: 2px solid #334155; border-radius: 8px;
            color: white; padding: 10px; z-index: 10; font-size: 13px;
        }}
        .team-score {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
        .team-flag {{ padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }}
        .kia {{ background: #ea1d2c; color: white; }}
        .nexen {{ background: #820024; color: #eaa000; }}
        .inning-tag {{ background: #1e293b; padding: 2px 8px; border-radius: 4px; font-size: 11px; color: #94a3b8; text-align: center; margin-bottom: 6px; }}

        /* --- 2. 좌/우 선수 카드리턴 UI --- */
        .player-card {{
            position: absolute; top: 110px; width: 170px;
            background: linear-gradient(180deg, rgba(30,41,59,0.9) 0%, rgba(15,23,42,0.95) 100%);
            border: 2px solid #64748b; border-radius: 10px; color: white; padding: 8px; z-index: 10;
            box-shadow: 0 8px 20px rgba(0,0,0,0.6);
        }}
        .card-left {{ left: 15px; border-color: #ea1d2c; }}
        .card-right {{ right: 15px; border-color: #820024; }}
        .card-header {{ display: flex; justify-content: space-between; font-size: 11px; color: #fbbf24; font-weight: bold; margin-bottom: 4px; }}
        .card-img-placeholder {{
            width: 100%; height: 110px; background: #334155; border-radius: 6px; margin-bottom: 6px;
            display: flex; align-items: center; justify-content: center; font-size: 32px;
        }}
        .player-name {{ font-size: 14px; font-weight: bold; text-align: center; border-bottom: 1px solid #475569; padding-bottom: 4px; margin-bottom: 6px; }}
        .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2px; font-size: 10px; text-align: center; color: #cbd5e1; }}
        .stat-val {{ font-weight: bold; color: #fff; font-size: 11px; }}

        /* --- 3. 하단 상세 전광판 --- */
        .bottom-bar {{
            position: absolute; bottom: 15px; left: 15px; right: 15px;
            display: flex; justify-content: space-between; gap: 10px; z-index: 10;
        }}
        .bottom-box {{
            background: rgba(15, 23, 42, 0.9); border: 1px solid #475569; border-radius: 6px;
            color: white; padding: 8px 14px; font-size: 11px; flex: 1;
        }}
        .mission-box {{
            background: linear-gradient(90deg, #1e1b4b, #312e81); border: 1px solid #6366f1;
            text-align: center; flex: 1.2;
        }}

        /* --- 4. 중앙 카운트다운 & 버튼 --- */
        #countdown {{
            position: absolute; top: 30%; left: 50%; transform: translate(-50%, -50%);
            font-size: 72px; font-weight: 900; color: #facc15; text-shadow: 0 0 25px rgba(0,0,0,0.9); z-index: 20;
        }}
        #hit-result {{
            position: absolute; top: 42%; left: 50%; transform: translate(-50%, -50%);
            font-size: 40px; font-weight: 900; text-shadow: 0 0 20px #000; display: none; z-index: 20;
        }}
        #pitch-btn {{
            position: absolute; bottom: 70px; left: 50%; transform: translateX(-50%);
            padding: 12px 35px; font-size: 18px; font-weight: bold; color: white;
            background: linear-gradient(135deg, #dc2626, #991b1b); border: 2px solid #f87171;
            border-radius: 25px; cursor: pointer; z-index: 20; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }}
        #pitch-btn:disabled {{ background: #475569; border-color: #64748b; cursor: not-allowed; opacity: 0.6; }}
    </style>
</head>
<body>
    <div id="game-container">
        <!-- 1. 스코어보드 -->
        <div class="scoreboard">
            <div class="inning-tag">1회 초 | B:0 S:0 O:0</div>
            <div class="team-score"><span class="team-flag kia">KIA</span> <span>0</span></div>
            <div class="team-score"><span class="team-flag nexen">넥센</span> <span>0</span></div>
        </div>

        <!-- 2. 좌측 타자 카드 -->
        <div class="player-card card-left">
            <div class="card-header"><span>★1 NORMAL</span> <span>RF</span></div>
            <div class="card-img-placeholder">⚾</div>
            <div class="player-name">신종길 '16</div>
            <div class="stat-grid">
                <div>정확 <span class="stat-val">62</span></div>
                <div>파워 <span class="stat-val">60</span></div>
                <div>선구 <span class="stat-val">61</span></div>
                <div>주력 <span class="stat-val">65</span></div>
            </div>
        </div>

        <!-- 3. 우측 투수 카드 -->
        <div class="player-card card-right">
            <div class="card-header"><span>★1 NORMAL</span> <span>SP</span></div>
            <div class="card-img-placeholder">🧢</div>
            <div class="player-name">피어밴드 '16</div>
            <div class="stat-grid">
                <div>제구 <span class="stat-val">67</span></div>
                <div>구위 <span class="stat-val">62</span></div>
                <div>체력 <span class="stat-val">72</span></div>
                <div>직구 <span class="stat-val">65</span></div>
            </div>
        </div>

        <!-- 4. 하단 기록 전광판 -->
        <div class="bottom-bar">
            <div class="bottom-box">
                <div style="color:#94a3b8; font-weight:bold;">1번 타자 (신종길)</div>
                <div>타율 .000 | 홈런 0 | 타점 0</div>
            </div>
            <div class="bottom-box mission-box">
                <div style="color:#a5b4fc; font-size:10px;">미션 도전하세요!</div>
                <div style="font-size:14px; font-weight:bold; color:#facc15;">3연속 파울 성공시 500p</div>
            </div>
            <div class="bottom-box">
                <div style="color:#94a3b8; font-weight:bold;">투수 체력 (피어밴드)</div>
                <div>방어율 0.00 | 승 0 | 탈삼진 0</div>
            </div>
        </div>

        <div id="countdown"></div>
        <div id="hit-result"></div>
        <button id="pitch-btn" onclick="startPitchSequence()">🔥 투구 시작 (5초 대기)</button>
    </div>

    <script>
        // --- 3D THREE.JS 엔진 (스크린샷 구도 완벽 재현) ---
        const container = document.getElementById('game-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a0f1d);

        // 돔구장 타자 뒤쪽 카메라인 시점 (사진과 동일한 화각 연출)
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.set(-0.6, 1.45, 2.2); // 약간 좌측에서 우타자를 바라보는 시점
        camera.lookAt(0, 1.25, -18.44);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);

        // 조명
        const light = new THREE.DirectionalLight(0xffffff, 1.2);
        light.position.set(10, 20, 10);
        scene.add(light);
        scene.add(new THREE.AmbientLight(0x555555));

        // --- 돔구장 야구장 3D 구현 ---
        // 1. 잔디 필드
        const fieldGeo = new THREE.PlaneGeometry(100, 100);
        const fieldMat = new THREE.MeshLambertMaterial({{ color: 0x225522 }});
        const field = new THREE.Mesh(fieldGeo, fieldMat);
        field.rotation.x = -Math.PI / 2;
        scene.add(field);

        // 2. 흙 인필드 다이아몬드
        const dirtGeo = new THREE.PlaneGeometry(10, 24);
        const dirtMat = new THREE.MeshLambertMaterial({{ color: 0x664422 }});
        const dirt = new THREE.Mesh(dirtGeo, dirtMat);
        dirt.rotation.x = -Math.PI / 2;
        dirt.position.set(0, 0.01, -10);
        scene.add(dirt);

        // 3. 관중석 & 외야 펜스
        const fenceGeo = new THREE.CylinderGeometry(40, 40, 8, 32, 1, true, -Math.PI/2.5, Math.PI/1.25);
        const fenceMat = new THREE.MeshLambertMaterial({{ color: 0x112233, side: THREE.DoubleSide }});
        const fence = new THREE.Mesh(fenceGeo, fenceMat);
        fence.position.set(0, 4, -20);
        scene.add(fence);

        // 4. 중앙 대형 전광판 (GOCHEOK SKY DOME)
        const boardGeo = new THREE.BoxGeometry(16, 6, 0.5);
        const boardMat = new THREE.MeshLambertMaterial({{ color: 0x050505 }});
        const board = new THREE.Mesh(boardGeo, boardMat);
        board.position.set(0, 12, -35);
        scene.add(board);

        // --- 선수 3D 재현 ---
        const PITCHER_Z = -18.44;

        // 1. 마운드 위 투수 (피어밴드)
        const pitcherGroup = new THREE.Group();
        const pBody = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 1.3), new THREE.MeshLambertMaterial({{ color: 0xffffff }}));
        pBody.position.y = 0.65;
        pitcherGroup.add(pBody);
        pitcherGroup.position.set(0, 0, PITCHER_Z);
        scene.add(pitcherGroup);

        // 2. 우타석 타자 (신종길 - 빨간 유니폼, 흰 바지 재현)
        const batterGroup = new THREE.Group();
        // 상의 (빨간색)
        const bTop = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.2, 0.7), new THREE.MeshLambertMaterial({{ color: 0xea1d2c }}));
        bTop.position.y = 1.05;
        // 하의 (흰색)
        const bBottom = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.18, 0.7), new THREE.MeshLambertMaterial({{ color: 0xffffff }}));
        bBottom.position.y = 0.35;
        batterGroup.add(bTop);
        batterGroup.add(bBottom);
        batterGroup.position.set(0.65, 0, -0.2); // 우타석 위치
        scene.add(batterGroup);

        // 3. 타자가 들고 있는 검은색 배트
        const batGroup = new THREE.Group();
        const bat = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.012, 0.95), new THREE.MeshLambertMaterial({{ color: 0x222222 }}));
        bat.position.set(0, 0.45, 0);
        batGroup.add(bat);
        batGroup.position.set(0.55, 1.2, -0.1);
        batGroup.rotation.z = -Math.PI / 3;
        batGroup.rotation.x = Math.PI / 6;
        scene.add(batGroup);

        // 4. 야구공
        const ball = new THREE.Mesh(new THREE.SphereGeometry(0.08, 16, 16), new THREE.MeshBasicMaterial({{ color: 0xffffff }}));
        ball.position.set(0, 1.5, PITCHER_Z);
        scene.add(ball);

        // --- 피칭 & 타격 로직 (5초 대기 후 초고속 피칭) ---
        let isWaiting = false;
        let isPitching = false;
        let countdownVal = 5;
        let pitchStartTime = 0;
        let hasSwung = false;

        const pitchSpeed = {pitch_speed};
        const flightTime = (18.44 / (pitchSpeed * 1000 / 3600)) * 1000; // 구속 반영 비행 시간

        function startPitchSequence() {{
            if (isWaiting || isPitching) return;
            isWaiting = true;
            hasSwung = false;
            countdownVal = 5;

            document.getElementById('pitch-btn').disabled = true;
            document.getElementById('hit-result').style.display = 'none';
            document.getElementById('countdown').innerText = countdownVal;

            ball.position.set(0, 1.5, PITCHER_Z);
            batGroup.rotation.y = 0;

            const timer = setInterval(() => {{
                countdownVal--;
                if (countdownVal > 0) {{
                    document.getElementById('countdown').innerText = countdownVal;
                }} else {{
                    clearInterval(timer);
                    document.getElementById('countdown').innerText = "PITCH!";
                    setTimeout(() => {{ document.getElementById('countdown').innerText = ""; }}, 500);
                    
                    // 5초 종료 ➔ 공 투구
                    isWaiting = false;
                    isPitching = true;
                    pitchStartTime = Date.now();
                }}
            }}, 1000);
        }}

        // 스페이스바 타격
        window.addEventListener('keydown', (e) => {{
            if (e.code === 'Space' && (isPitching || isWaiting) && !hasSwung) {{
                hasSwung = true;
                batGroup.rotation.y = -Math.PI / 1.2; // 풀스윙 애니메이션

                if (isPitching) {{
                    const elapsed = Date.now() - pitchStartTime;
                    const diff = Math.abs(elapsed - (flightTime * 0.85));

                    if (diff < 45) {{
                        showResult("💥 대형 홈런!!", "#facc15");
                        ball.position.set(0, 20, -50);
                    }} else if (diff < 100) {{
                        showResult("⚾ 안타!", "#4ade80");
                    }} else if (diff < 160) {{
                        showResult("💨 파울!", "#fbbf24");
                    }} else {{
                        showResult("❌ 헛스윙 삼진!", "#f87171");
                    }}
                }} else {{
                    showResult("💨 너무 빠릅니다!", "#f87171");
                }}
            }}
        }});

        function showResult(text, color) {{
            const el = document.getElementById('hit-result');
            el.innerText = text;
            el.style.color = color;
            el.style.display = 'block';
        }}

        // 애니메이션 루프
        function animate() {{
            requestAnimationFrame(animate);

            if (isPitching) {{
                const elapsed = Date.now() - pitchStartTime;
                const progress = elapsed / flightTime;

                if (progress <= 1.0) {{
                    ball.position.z = PITCHER_Z + (0 - PITCHER_Z) * progress;
                }} else {{
                    if (!hasSwung) showResult("⚾ 루킹 스트라이크!", "#fbbf24");
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

components.html(html_code, height=700)
