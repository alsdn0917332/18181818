import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="KBO 3D 리얼 프로야구", page_icon="⚾", layout="wide")

st.sidebar.header("⚙️ 경기 & 투구 설정")
pitch_type = st.sidebar.selectbox("구종 선택", ["직구 (Fastball)", "슬라이더 (Slider)", "커브 (Curveball)", "포크볼 (Forkball)"])
pitch_speed = st.sidebar.slider("구속 설정 (km/h)", 130, 165, 150)

st.title("⚾ 3D KBO 모바일 스타일 리얼 야구 게임")

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        body {{ margin: 0; overflow: hidden; background: #000; font-family: 'Malgun Gothic', sans-serif; user-select: none; }}
        #game-container {{ width: 100vw; height: 720px; position: relative; background: #050b14; }}

        /* 1. 스코어보드 UI */
        .scoreboard {{
            position: absolute; top: 15px; left: 15px; width: 220px;
            background: rgba(15, 23, 42, 0.9); border: 2px solid #334155; border-radius: 8px;
            color: white; padding: 10px; z-index: 10; font-size: 13px;
        }}
        .team-score {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
        .team-flag {{ padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }}
        .kia {{ background: #ea1d2c; color: white; }}
        .nexen {{ background: #820024; color: #eaa000; }}
        .inning-tag {{ background: #1e293b; padding: 2px 8px; border-radius: 4px; font-size: 11px; color: #94a3b8; text-align: center; margin-bottom: 6px; }}

        /* 2. 좌/우 선수 프로필 카드 */
        .player-card {{
            position: absolute; top: 110px; width: 160px;
            background: linear-gradient(180deg, rgba(30,41,59,0.95) 0%, rgba(15,23,42,0.95) 100%);
            border: 2px solid #64748b; border-radius: 10px; color: white; padding: 8px; z-index: 10;
        }}
        .card-left {{ left: 15px; border-color: #ea1d2c; }}
        .card-right {{ right: 15px; border-color: #820024; }}
        .card-header {{ display: flex; justify-content: space-between; font-size: 11px; color: #fbbf24; font-weight: bold; margin-bottom: 4px; }}
        .card-img-placeholder {{
            width: 100%; height: 100px; background: #334155; border-radius: 6px; margin-bottom: 6px;
            display: flex; align-items: center; justify-content: center; font-size: 32px;
        }}
        .player-name {{ font-size: 13px; font-weight: bold; text-align: center; border-bottom: 1px solid #475569; padding-bottom: 4px; margin-bottom: 6px; }}
        .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2px; font-size: 10px; text-align: center; color: #cbd5e1; }}
        .stat-val {{ font-weight: bold; color: #fff; font-size: 11px; }}

        /* 3. 하단 상세 전광판 */
        .bottom-bar {{
            position: absolute; bottom: 15px; left: 15px; right: 15px;
            display: flex; justify-content: space-between; gap: 10px; z-index: 10;
        }}
        .bottom-box {{
            background: rgba(15, 23, 42, 0.9); border: 1px solid #475569; border-radius: 6px;
            color: white; padding: 8px 14px; font-size: 11px; flex: 1;
        }}

        /* 4. 카운트다운 & 타격 결과 */
        #countdown {{
            position: absolute; top: 30%; left: 50%; transform: translate(-50%, -50%);
            font-size: 80px; font-weight: 900; color: #facc15; text-shadow: 0 0 30px rgba(0,0,0,0.9); z-index: 20;
        }}
        #hit-result {{
            position: absolute; top: 42%; left: 50%; transform: translate(-50%, -50%);
            font-size: 42px; font-weight: 900; text-shadow: 0 0 20px #000; display: none; z-index: 20;
        }}
        #pitch-btn {{
            position: absolute; bottom: 70px; left: 50%; transform: translateX(-50%);
            padding: 14px 40px; font-size: 20px; font-weight: bold; color: white;
            background: linear-gradient(135deg, #dc2626, #991b1b); border: 2px solid #f87171;
            border-radius: 30px; cursor: pointer; z-index: 20; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }}
        #pitch-btn:disabled {{ background: #475569; border-color: #64748b; cursor: not-allowed; opacity: 0.6; }}
    </style>
</head>
<body>
    <div id="game-container">
        <!-- UI 파트 -->
        <div class="scoreboard">
            <div class="inning-tag">1회 초 | B:0 S:0 O:0</div>
            <div class="team-score"><span class="team-flag kia">KIA</span> <span>0</span></div>
            <div class="team-score"><span class="team-flag nexen">넥센</span> <span>0</span></div>
        </div>

        <div class="player-card card-left">
            <div class="card-header"><span>★1 LIVE</span> <span>RF</span></div>
            <div class="card-img-placeholder">⚾</div>
            <div class="player-name">김도영 '24</div>
            <div class="stat-grid">
                <div>정확 <span class="stat-val">92</span></div>
                <div>파워 <span class="stat-val">88</span></div>
                <div>선구 <span class="stat-val">85</span></div>
                <div>주력 <span class="stat-val">95</span></div>
            </div>
        </div>

        <div class="player-card card-right">
            <div class="card-header"><span>★1 LIVE</span> <span>SP</span></div>
            <div class="card-img-placeholder">🧢</div>
            <div class="player-name">류현진 '24</div>
            <div class="stat-grid">
                <div>제구 <span class="stat-val">90</span></div>
                <div>구위 <span class="stat-val">86</span></div>
                <div>체력 <span class="stat-val">88</span></div>
                <div>직구 <span class="stat-val">87</span></div>
            </div>
        </div>

        <div class="bottom-bar">
            <div class="bottom-box">
                <div style="color:#94a3b8; font-weight:bold;">1번 타자 (김도영)</div>
                <div>타율 .347 | 홈런 38 | 타점 109</div>
            </div>
            <div class="bottom-box">
                <div style="color:#94a3b8; font-weight:bold;">투수 정보 (류현진)</div>
                <div>구속 {pitch_speed} km/h | 구종: {pitch_type}</div>
            </div>
        </div>

        <div id="countdown"></div>
        <div id="hit-result"></div>
        <button id="pitch-btn" onclick="startPitchSequence()">🔥 투구 시작 (5초 대기)</button>
    </div>

    <script>
        const container = document.getElementById('game-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x061121);

        // 스크린샷과 동일한 타자 후방 3D 카메라 뷰
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.set(-0.7, 1.45, 2.3);
        camera.lookAt(0, 1.25, -18.44);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);

        // 조명 연출
        const light = new THREE.DirectionalLight(0xffffff, 1.3);
        light.position.set(10, 25, 10);
        scene.add(light);
        scene.add(new THREE.AmbientLight(0x666666));

        // --- 1. 디테일 3D 야구장 인프라 ---
        // 내야 잔디 & 외야 잔디 패턴
        const fieldGeo = new THREE.PlaneGeometry(120, 120);
        const fieldMat = new THREE.MeshLambertMaterial({{ color: 0x1e5631 }});
        const field = new THREE.Mesh(fieldGeo, fieldMat);
        field.rotation.x = -Math.PI / 2;
        scene.add(field);

        // 흙 다이아몬드 (인필드)
        const dirtGeo = new THREE.PlaneGeometry(12, 26);
        const dirtMat = new THREE.MeshLambertMaterial({{ color: 0x8b5a2b }});
        const dirt = new THREE.Mesh(dirtGeo, dirtMat);
        dirt.rotation.x = -Math.PI / 2;
        dirt.position.set(0, 0.01, -11);
        scene.add(dirt);

        // 홈플레이트
        const hpGeo = new THREE.BoxGeometry(0.4, 0.02, 0.4);
        const hpMat = new THREE.MeshBasicMaterial({{ color: 0xffffff }});
        const hp = new THREE.Mesh(hpGeo, hpMat);
        hp.position.set(0, 0.02, 0);
        scene.add(hp);

        // 스트라이크 존 박스 프레임
        const szGeo = new THREE.BoxGeometry(0.5, 0.7, 0.01);
        const szMat = new THREE.MeshBasicMaterial({{ color: 0x00f5d4, wireframe: true, transparent: true, opacity: 0.5 }});
        const sz = new THREE.Mesh(szGeo, szMat);
        sz.position.set(0, 1.2, -0.4);
        scene.add(sz);

        // 외야 펜스 및 돔구장 벽면
        const fenceGeo = new THREE.CylinderGeometry(45, 45, 6, 32, 1, true, -Math.PI/2.5, Math.PI/1.25);
        const fenceMat = new THREE.MeshLambertMaterial({{ color: 0x0f172a, side: THREE.DoubleSide }});
        const fence = new THREE.Mesh(fenceGeo, fenceMat);
        fence.position.set(0, 3, -20);
        scene.add(fence);

        // 중앙 고척 스카이돔 스타일 대형 전광판
        const boardGeo = new THREE.BoxGeometry(20, 8, 0.5);
        const boardMat = new THREE.MeshLambertMaterial({{ color: 0x020617 }});
        const board = new THREE.Mesh(boardGeo, boardMat);
        board.position.set(0, 14, -38);
        scene.add(board);

        // --- 2. 사람 형태 3D 캐릭터 생성 함수 (투수 & 타자) ---
        function createHumanCharacter(jerseyColor, pantsColor) {{
            const group = new THREE.Group();
            const matJersey = new THREE.MeshLambertMaterial({{ color: jerseyColor }});
            const matPants = new THREE.MeshLambertMaterial({{ color: pantsColor }});
            const matSkin = new THREE.MeshLambertMaterial({{ color: 0xffdbac }});

            // 머리
            const head = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), matSkin);
            head.position.y = 1.45;
            group.add(head);

            // 상체 (유니폼)
            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.15, 0.55), matJersey);
            torso.position.y = 1.05;
            group.add(torso);

            // 팔 (오른팔/왼팔)
            const armR = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.45), matJersey);
            armR.position.set(-0.22, 1.1, 0);
            group.add(armR);

            const armL = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.45), matJersey);
            armL.position.set(0.22, 1.1, 0);
            group.add(armL);

            // 하체 (바지)
            const legR = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.6), matPants);
            legR.position.set(-0.1, 0.4, 0);
            group.add(legR);

            const legL = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.6), matPants);
            legL.position.set(0.1, 0.4, 0);
            group.add(legL);

            return {{ group, armR, armL, torso }};
        }}

        const PITCHER_Z = -18.44;

        // 투수 생성 (버건디 유니폼, 마운드 위치)
        const pitcherChar = createHumanCharacter(0x820024, 0xffffff);
        pitcherChar.group.position.set(0, 0, PITCHER_Z);
        scene.add(pitcherChar.group);

        // 타자 생성 (레드 유니폼, 우타석 위치)
        const batterChar = createHumanCharacter(0xea1d2c, 0xffffff);
        batterChar.group.position.set(0.6, 0, -0.2);
        batterChar.group.rotation.y = -Math.PI / 6;
        scene.add(batterChar.group);

        // 3D 배트 (타자 팔에 연결)
        const batGeo = new THREE.CylinderGeometry(0.025, 0.012, 0.95);
        const batMat = new THREE.MeshLambertMaterial({{ color: 0x111111 }});
        const bat = new THREE.Mesh(batGeo, batMat);
        bat.position.set(0.55, 1.25, -0.05);
        bat.rotation.z = -Math.PI / 3.5;
        scene.add(bat);

        // 야구공
        const ball = new THREE.Mesh(new THREE.SphereGeometry(0.08, 16, 16), new THREE.MeshBasicMaterial({{ color: 0xffffff }}));
        ball.position.set(0, 1.5, PITCHER_Z);
        scene.add(ball);

        // --- 3. 변수 및 애니메이션 로직 ---
        let isWaiting = false;
        let isWindup = false;
        let isPitching = false;
        let isHitBallMoving = false;
        
        let countdownVal = 5;
        let pitchStartTime = 0;
        let windupStartTime = 0;
        let hasSwung = false;

        const pitchSpeedVal = {pitch_speed};
        const flightTime = (18.44 / (pitchSpeedVal * 1000 / 3600)) * 1000;

        // 타구 물리학 변수
        let ballVel = new THREE.Vector3();
        let ballGravity = -9.8;

        function startPitchSequence() {{
            if (isWaiting || isWindup || isPitching || isHitBallMoving) return;

            isWaiting = true;
            hasSwung = false;
            isHitBallMoving = false;
            countdownVal = 5;

            document.getElementById('pitch-btn').disabled = true;
            document.getElementById('hit-result').style.display = 'none';
            document.getElementById('countdown').innerText = countdownVal;

            ball.position.set(0, 1.5, PITCHER_Z);
            bat.rotation.y = 0;
            bat.position.set(0.55, 1.25, -0.05);

            const timer = setInterval(() => {{
                countdownVal--;
                if (countdownVal > 0) {{
                    document.getElementById('countdown').innerText = countdownVal;
                }} else {{
                    clearInterval(timer);
                    document.getElementById('countdown').innerText = "WINDUP!";
                    
                    // 와인드업 동작 후 투구
                    isWaiting = false;
                    isWindup = true;
                    windupStartTime = Date.now();
                }}
            }}, 1000);
        }}

        // 스페이스바 부드러운 스윙 & 타구 궤적 제어
        window.addEventListener('keydown', (e) => {{
            if (e.code === 'Space' && (isPitching || isWindup) && !hasSwung) {{
                hasSwung = true;
                
                // 배트 및 타자 상체 스윙 회전
                bat.rotation.y = -Math.PI / 1.1;
                bat.position.x = 0.2;

                if (isPitching) {{
                    const elapsed = Date.now() - pitchStartTime;
                    const diff = Math.abs(elapsed - (flightTime * 0.82));

                    isPitching = false;
                    isHitBallMoving = true;

                    if (diff < 40) {{
                        showResult("💥 대형 홈런!! (HOMERUN)", "#facc15");
                        ballVel.set(0, 18, -35); // 높고 멀리 날아가는 궤적
                    }} else if (diff < 90) {{
                        showResult("⚾ 안타! (HIT)", "#4ade80");
                        ballVel.set((Math.random() - 0.5) * 15, 8, -25); // 안타 궤적
                    }} else if (diff < 150) {{
                        showResult("💨 파울! (FOUL)", "#fbbf24");
                        ballVel.set(15, 10, -5); // 측면 파울 궤적
                    }} else {{
                        showResult("❌ 헛스윙 삼진!", "#f87171");
                        isHitBallMoving = false;
                        document.getElementById('pitch-btn').disabled = false;
                    }}
                }} else {{
                    showResult("💨 너무 빠른 타이밍! (헛스윙)", "#f87171");
                }}
            }}
        }});

        function showResult(text, color) {{
            const el = document.getElementById('hit-result');
            el.innerText = text;
            el.style.color = color;
            el.style.display = 'block';
        }}

        // --- 4. 렌더링 애니메이션 루프 ---
        function animate() {{
            requestAnimationFrame(animate);

            // 1. 투수 와인드업 애니메이션 (0.6초)
            if (isWindup) {{
                const elapsed = Date.now() - windupStartTime;
                if (elapsed < 600) {{
                    pitcherChar.armR.rotation.x = -Math.PI * (elapsed / 600); // 오른팔 뒤로 올림
                }} else {{
                    isWindup = false;
                    isPitching = true;
                    pitchStartTime = Date.now();
                    document.getElementById('countdown').innerText = "PITCH!";
                    setTimeout(() => {{ document.getElementById('countdown').innerText = ""; }}, 400);
                }}
            }}

            // 2. 공 투구 이동 애니메이션
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

            // 3. 타격 후 공의 포물선 비행 애니메이션
            if (isHitBallMoving) {{
                const dt = 0.016; // 프레임당 시간
                ball.position.x += ballVel.x * dt;
                ball.position.y += ballVel.y * dt;
                ball.position.z += ballVel.z * dt;

                ballVel.y += ballGravity * dt; // 중력 적용

                // 땅에 부딪히거나 외야에 도착 시 정지
                if (ball.position.y <= 0.1) {{
                    ball.position.y = 0.1;
                    isHitBallMoving = false;
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

components.html(html_code, height=750)
