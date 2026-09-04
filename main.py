import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="KBO 3D 리얼 야구장", page_icon="⚾", layout="wide")

st.sidebar.header("⚙️ 경기 & 투구 설정")
pitch_type = st.sidebar.selectbox("구종 선택", ["직구 (Fastball)", "슬라이더 (Slider)", "커브 (Curveball)", "포크볼 (Forkball)"])
pitch_speed = st.sidebar.slider("구속 설정 (km/h)", 130, 165, 150)

st.title("⚾ 3D KBO 야간 경기장 실전 시뮬레이터")

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        body {{ margin: 0; overflow: hidden; background: #000; font-family: 'Malgun Gothic', sans-serif; user-select: none; }}
        #game-container {{ width: 100vw; height: 750px; position: relative; background: #030712; }}

        /* 1. 스코어보드 UI */
        .scoreboard {{
            position: absolute; top: 15px; left: 15px; width: 220px;
            background: rgba(15, 23, 42, 0.9); border: 2px solid #334155; border-radius: 8px;
            color: white; padding: 10px; z-index: 10; font-size: 13px;
        }}
        .team-score {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
        .team-flag {{ padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }}
        .kia {{ background: #ea1d2c; color: white; }}
        .samsung {{ background: #0066b2; color: white; }}
        .inning-tag {{ background: #1e293b; padding: 2px 8px; border-radius: 4px; font-size: 11px; color: #94a3b8; text-align: center; margin-bottom: 6px; }}

        /* 2. 전체화면 버튼 */
        #fullscreen-btn {{
            position: absolute; top: 15px; right: 15px; padding: 10px 18px;
            background: rgba(30, 41, 59, 0.9); color: #fff; border: 1px solid #64748b;
            border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 13px; z-index: 10;
        }}
        #fullscreen-btn:hover {{ background: #3b82f6; }}

        /* 3. 하단 세부 정보 UI */
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
            position: absolute; top: 28%; left: 50%; transform: translate(-50%, -50%);
            font-size: 80px; font-weight: 900; color: #facc15; text-shadow: 0 0 30px rgba(0,0,0,0.9); z-index: 20;
        }}
        #hit-result {{
            position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%);
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
        <!-- UI 요소 -->
        <div class="scoreboard">
            <div class="inning-tag">1회 초 | B:0 S:0 O:0</div>
            <div class="team-score"><span class="team-flag kia">KIA</span> <span>0</span></div>
            <div class="team-score"><span class="team-flag samsung">삼성</span> <span>0</span></div>
        </div>

        <button id="fullscreen-btn" onclick="toggleFullScreen()">🖥️ 전체화면</button>

        <div class="bottom-bar">
            <div class="bottom-box">
                <div style="color:#94a3b8; font-weight:bold;">타자 (김도영)</div>
                <div>타율 .347 | 홈런 38 | 타점 109</div>
            </div>
            <div class="bottom-box">
                <div style="color:#94a3b8; font-weight:bold;">투수 (원태인)</div>
                <div>구속: {pitch_speed} km/h | 구종: {pitch_type}</div>
            </div>
        </div>

        <div id="countdown"></div>
        <div id="hit-result"></div>
        <button id="pitch-btn" onclick="startPitchSequence()">🔥 투구 시작 (5초 대기)</button>
    </div>

    <script>
        const container = document.getElementById('game-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x020617); // 야간 하늘

        // --- 카메라 시점: 홈플레이트 & 스트라이크 존 화면 정중앙 배치 ---
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.set(0, 1.4, 2.1); // 중앙 구도
        camera.lookAt(0, 1.2, -18.44);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);

        // --- 야간 경기장 전용 야간 조명 타워 (4개) ---
        function createLightTower(x, z) {{
            const tower = new THREE.Group();
            const poleGeo = new THREE.CylinderGeometry(0.3, 0.5, 20);
            const poleMat = new THREE.MeshLambertMaterial({{ color: 0x475569 }});
            const pole = new THREE.Mesh(poleGeo, poleMat);
            pole.position.y = 10;
            tower.add(pole);

            // 조명 패널
            const headGeo = new THREE.BoxGeometry(4, 2.5, 0.5);
            const headMat = new THREE.MeshBasicMaterial({{ color: 0xffffff }});
            const head = new THREE.Mesh(headGeo, headMat);
            head.position.set(0, 20, 0);
            tower.add(head);

            // 실체 조명 광원
            const light = new THREE.SpotLight(0xffffff, 1.2);
            light.position.set(x, 20, z);
            light.target.position.set(0, 0, -10);
            scene.add(light);

            tower.position.set(x, 0, z);
            scene.add(tower);
        }}

        // 조명 탑 배치 (좌/우 외야, 좌/우 내야)
        createLightTower(-35, -30);
        createLightTower(35, -30);
        createLightTower(-30, 5);
        createLightTower(30, 5);

        scene.add(new THREE.AmbientLight(0x556677));

        // --- 야구장 인프라 디테일 재현 ---
        // 1. 잔디 필드
        const fieldGeo = new THREE.PlaneGeometry(120, 120);
        const fieldMat = new THREE.MeshLambertMaterial({{ color: 0x15803d }});
        const field = new THREE.Mesh(fieldGeo, fieldMat);
        field.rotation.x = -Math.PI / 2;
        scene.add(field);

        // 2. 다이아몬드 내야 흙 및 투수 마운드 흙
        const dirtGeo = new THREE.PlaneGeometry(16, 26);
        const dirtMat = new THREE.MeshLambertMaterial({{ color: 0x9a3412 }});
        const dirt = new THREE.Mesh(dirtGeo, dirtMat);
        dirt.rotation.x = -Math.PI / 2;
        dirt.position.set(0, 0.01, -11);
        scene.add(dirt);

        // 3. 중앙 스트라이크 존 박스 (화면 중앙 정렬)
        const szGeo = new THREE.BoxGeometry(0.52, 0.72, 0.01);
        const szMat = new THREE.MeshBasicMaterial({{ color: 0x06b6d4, wireframe: true, transparent: true, opacity: 0.6 }});
        const sz = new THREE.Mesh(szGeo, szMat);
        sz.position.set(0, 1.2, -0.4);
        scene.add(sz);

        // 4. 홈플레이트
        const hp = new THREE.Mesh(new THREE.BoxGeometry(0.43, 0.02, 0.43), new THREE.MeshBasicMaterial({{ color: 0xffffff }}));
        hp.position.set(0, 0.02, 0);
        scene.add(hp);

        // 5. 외야 펜스 및 전광판
        const fence = new THREE.Mesh(
            new THREE.CylinderGeometry(45, 45, 5, 32, 1, true, -Math.PI/2.5, Math.PI/1.25),
            new THREE.MeshLambertMaterial({{ color: 0x0f172a, side: THREE.DoubleSide }})
        );
        fence.position.set(0, 2.5, -20);
        scene.add(fence);

        const board = new THREE.Mesh(
            new THREE.BoxGeometry(22, 9, 0.5),
            new THREE.MeshLambertMaterial({{ color: 0x020617 }})
        );
        board.position.set(0, 14, -38);
        scene.add(board);

        // --- 사람 형태 3D 캐릭터 생성 ---
        function createHumanCharacter(jerseyColor, pantsColor) {{
            const group = new THREE.Group();
            const matJersey = new THREE.MeshLambertMaterial({{ color: jerseyColor }});
            const matPants = new THREE.MeshLambertMaterial({{ color: pantsColor }});
            const matSkin = new THREE.MeshLambertMaterial({{ color: 0xffdbac }});

            const head = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), matSkin);
            head.position.y = 1.45;
            group.add(head);

            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.15, 0.55), matJersey);
            torso.position.y = 1.05;
            group.add(torso);

            const armR = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.45), matJersey);
            armR.position.set(-0.22, 1.1, 0);
            group.add(armR);

            const armL = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.45), matJersey);
            armL.position.set(0.22, 1.1, 0);
            group.add(armL);

            const legR = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.6), matPants);
            legR.position.set(-0.1, 0.4, 0);
            group.add(legR);

            const legL = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.6), matPants);
            legL.position.set(0.1, 0.4, 0);
            group.add(legL);

            return {{ group, armR, armL }};
        }}

        const PITCHER_Z = -18.44;

        // 투수 (삼성 유니폼)
        const pitcherChar = createHumanCharacter(0x0066b2, 0xffffff);
        pitcherChar.group.position.set(0, 0, PITCHER_Z);
        scene.add(pitcherChar.group);

        // 타자 (KIA 유니폼, 스트라이크존 우측 중앙 정렬)
        const batterChar = createHumanCharacter(0xea1d2c, 0xffffff);
        batterChar.group.position.set(0.5, 0, -0.2);
        batterChar.group.rotation.y = -Math.PI / 6;
        scene.add(batterChar.group);

        // 배트
        const bat = new THREE.Mesh(
            new THREE.CylinderGeometry(0.025, 0.012, 0.95),
            new THREE.MeshLambertMaterial({{ color: 0x111111 }})
        );
        bat.position.set(0.48, 1.25, -0.05);
        bat.rotation.z = -Math.PI / 3.5;
        scene.add(bat);

        // 야구공
        const ball = new THREE.Mesh(new THREE.SphereGeometry(0.08, 16, 16), new THREE.MeshBasicMaterial({{ color: 0xffffff }}));
        ball.position.set(0, 1.5, PITCHER_Z);
        scene.add(ball);

        // --- 변수 및 로직 ---
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
        let ballVel = new THREE.Vector3();

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
            bat.position.set(0.48, 1.25, -0.05);

            const timer = setInterval(() => {{
                countdownVal--;
                if (countdownVal > 0) {{
                    document.getElementById('countdown').innerText = countdownVal;
                }} else {{
                    clearInterval(timer);
                    document.getElementById('countdown').innerText = "WINDUP!";
                    
                    isWaiting = false;
                    isWindup = true;
                    windupStartTime = Date.now();
                }}
            }}, 1000);
        }}

        // 스페이스바 타격
        window.addEventListener('keydown', (e) => {{
            if (e.code === 'Space' && (isPitching || isWindup) && !hasSwung) {{
                hasSwung = true;
                bat.rotation.y = -Math.PI / 1.1;
                bat.position.x = 0.15;

                if (isPitching) {{
                    const elapsed = Date.now() - pitchStartTime;
                    const diff = Math.abs(elapsed - (flightTime * 0.82));

                    isPitching = false;
                    isHitBallMoving = true;

                    if (diff < 40) {{
                        showResult("💥 대형 홈런!! (HOMERUN)", "#facc15");
                        ballVel.set(0, 18, -35);
                    }} else if (diff < 90) {{
                        showResult("⚾ 안타! (HIT)", "#4ade80");
                        ballVel.set((Math.random() - 0.5) * 15, 8, -25);
                    }} else if (diff < 150) {{
                        showResult("💨 파울! (FOUL)", "#fbbf24");
                        ballVel.set(15, 10, -5);
                    }} else {{
                        showResult("❌ 헛스윙 삼진!", "#f87171");
                        isHitBallMoving = false;
                        document.getElementById('pitch-btn').disabled = false;
                    }}
                }} else {{
                    showResult("💨 너무 빠른 타이밍!", "#f87171");
                }}
            }}
        }});

        function showResult(text, color) {{
            const el = document.getElementById('hit-result');
            el.innerText = text;
            el.style.color = color;
            el.style.display = 'block';
        }}

        // 전체화면 토글
        function toggleFullScreen() {{
            const elem = document.getElementById('game-container');
            if (!document.fullscreenElement) {{
                elem.requestFullscreen().catch(err => alert(err.message));
            }} else {{
                document.exitFullscreen();
            }}
        }}

        // 애니메이션 루프
        function animate() {{
            requestAnimationFrame(animate);

            if (isWindup) {{
                const elapsed = Date.now() - windupStartTime;
                if (elapsed < 600) {{
                    pitcherChar.armR.rotation.x = -Math.PI * (elapsed / 600);
                }} else {{
                    isWindup = false;
                    isPitching = true;
                    pitchStartTime = Date.now();
                    document.getElementById('countdown').innerText = "PITCH!";
                    setTimeout(() => {{ document.getElementById('countdown').innerText = ""; }}, 400);
                }}
            }}

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

            if (isHitBallMoving) {{
                const dt = 0.016;
                ball.position.x += ballVel.x * dt;
                ball.position.y += ballVel.y * dt;
                ball.position.z += ballVel.z * dt;
                ballVel.y += -9.8 * dt;

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

components.html(html_code, height=780)
