import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="KBO 3D 리얼 야구장", page_icon="⚾", layout="wide")

st.sidebar.header("⚙️ 경기 & 투구 설정")
pitch_type = st.sidebar.selectbox("구종 선택", [
    "직구 (Four-Seam)", 
    "슬라이더 (Slider)", 
    "커브 (Curveball)", 
    "포크볼 (Forkball)",
    "체인지업 (Changeup)"
])
pitch_speed = st.sidebar.slider("구속 설정 (km/h)", 120, 165, 150)

st.title("⚾ 3D KBO 야간 경기장 실전 시뮬레이터")

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        body {{ margin: 0; overflow: hidden; background: #000; font-family: 'Malgun Gothic', sans-serif; user-select: none; }}
        #game-container {{ width: 100vw; height: 750px; position: relative; background: #020617; }}

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
            <div class="bottom-box" style="text-align:right;">
                <div style="color:#facc15; font-weight:bold;">🎮 조작 안내</div>
                <div>[1키]: 투구 준비 | [스페이스바]: 타격</div>
            </div>
        </div>

        <div id="countdown"></div>
        <div id="hit-result"></div>
        <button id="pitch-btn" onclick="startPitchSequence()">🔥 투구 시작 ('1' 키 누름 / 5초 대기)</button>
    </div>

    <script>
        const container = document.getElementById('game-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x020617); // 야간 하늘

        // --- 카메라 시점: 홈플레이트 & 스트라이크 존 화면 정중앙 배치 ---
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.set(0, 1.4, 2.1);
        camera.lookAt(0, 1.2, -18.44);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // --- 야간 경기장 조명 타워 (4개) ---
        function createLightTower(x, z) {{
            const tower = new THREE.Group();
            
            // 철골 구조 트러스 느낌
            const poleGeo = new THREE.CylinderGeometry(0.3, 0.6, 22, 8);
            const poleMat = new THREE.MeshLambertMaterial({{ color: 0x334155 }});
            const pole = new THREE.Mesh(poleGeo, poleMat);
            pole.position.y = 11;
            tower.add(pole);

            // 조명 패널 프레임
            const headGeo = new THREE.BoxGeometry(5, 3, 0.6);
            const headMat = new THREE.MeshBasicMaterial({{ color: 0xf8fafc }});
            const head = new THREE.Mesh(headGeo, headMat);
            head.position.set(0, 22, 0);
            tower.add(head);

            // 실제 광원
            const light = new THREE.SpotLight(0xffffff, 1.4);
            light.position.set(x, 22, z);
            light.target.position.set(0, 0, -10);
            scene.add(light);

            tower.position.set(x, 0, z);
            scene.add(tower);
        }}

        createLightTower(-35, -30);
        createLightTower(35, -30);
        createLightTower(-30, 5);
        createLightTower(30, 5);

        scene.add(new THREE.AmbientLight(0x475569));

        // --- 발전된 리얼 야구장 구조물 ---
        // 1. 메인 잔디 필드 (스트라이프 패턴 구현)
        const fieldGeo = new THREE.PlaneGeometry(120, 120, 20, 20);
        const fieldMat = new THREE.MeshLambertMaterial({{ color: 0x15803d }});
        const field = new THREE.Mesh(fieldGeo, fieldMat);
        field.rotation.x = -Math.PI / 2;
        scene.add(field);

        // 잔디 줄무늬 패치 추가
        for(let i = -50; i < 50; i += 8) {{
            const stripeGeo = new THREE.PlaneGeometry(120, 4);
            const stripeMat = new THREE.MeshLambertMaterial({{ color: 0x166534, transparent: true, opacity: 0.3 }});
            const stripe = new THREE.Mesh(stripeGeo, stripeMat);
            stripe.rotation.x = -Math.PI / 2;
            stripe.position.set(0, 0.005, i);
            scene.add(stripe);
        }}

        // 2. 다이아몬드 내야 흙 및 워닝 트랙
        const dirtGeo = new THREE.PlaneGeometry(18, 28);
        const dirtMat = new THREE.MeshLambertMaterial({{ color: 0x9a3412 }});
        const dirt = new THREE.Mesh(dirtGeo, dirtMat);
        dirt.rotation.x = -Math.PI / 2;
        dirt.position.set(0, 0.01, -11);
        scene.add(dirt);

        // 3. 중앙 스트라이크 존 박스
        const szGeo = new THREE.BoxGeometry(0.52, 0.72, 0.01);
        const szMat = new THREE.MeshBasicMaterial({{ color: 0x06b6d4, wireframe: true, transparent: true, opacity: 0.6 }});
        const sz = new THREE.Mesh(szGeo, szMat);
        sz.position.set(0, 1.2, -0.4);
        scene.add(sz);

        // 4. 홈플레이트 & 타자석 라인
        const hp = new THREE.Mesh(new THREE.BoxGeometry(0.43, 0.02, 0.43), new THREE.MeshBasicMaterial({{ color: 0xffffff }}));
        hp.position.set(0, 0.02, 0);
        scene.add(hp);

        // 타석 분크 라인 (좌/우 타석)
        const boxLineGeo = new THREE.BoxGeometry(0.8, 0.01, 1.8);
        const lineMat = new THREE.MeshBasicMaterial({{ color: 0xffffff, transparent: true, opacity: 0.8 }});
        
        const rBox = new THREE.Mesh(boxLineGeo, lineMat);
        rBox.position.set(0.65, 0.015, -0.2);
        scene.add(rBox);

        const lBox = new THREE.Mesh(boxLineGeo, lineMat);
        lBox.position.set(-0.65, 0.015, -0.2);
        scene.add(lBox);

        // 5. 외야 펜스 & 광고판 패널 & 관중석 구조
        const fenceGeo = new THREE.CylinderGeometry(45, 45, 5, 32, 1, true, -Math.PI/2.5, Math.PI/1.25);
        const fenceMat = new THREE.MeshLambertMaterial({{ color: 0x0f172a, side: THREE.DoubleSide }});
        const fence = new THREE.Mesh(fenceGeo, fenceMat);
        fence.position.set(0, 2.5, -20);
        scene.add(fence);

        // 광고 띠 패널
        const adPanelGeo = new THREE.CylinderGeometry(44.8, 44.8, 1.2, 32, 1, true, -Math.PI/2.5, Math.PI/1.25);
        const adPanelMat = new THREE.MeshBasicMaterial({{ color: 0x1e3a8a, side: THREE.DoubleSide }});
        const adPanel = new THREE.Mesh(adPanelGeo, adPanelMat);
        adPanel.position.set(0, 3, -20);
        scene.add(adPanel);

        // 관중석 3단계 스탠드
        for(let s = 1; s <= 3; s++) {{
            const standGeo = new THREE.CylinderGeometry(45 + s*6, 45 + s*6, 3, 32, 1, true, -Math.PI/2.3, Math.PI/1.15);
            const standMat = new THREE.MeshLambertMaterial({{ color: 0x334155, side: THREE.DoubleSide }});
            const stand = new THREE.Mesh(standGeo, standMat);
            stand.position.set(0, 3 + s*3, -20);
            scene.add(stand);
        }}

        // 대형 전광판
        const board = new THREE.Mesh(
            new THREE.BoxGeometry(24, 10, 0.5),
            new THREE.MeshLambertMaterial({{ color: 0x020617 }})
        );
        board.position.set(0, 15, -38);
        scene.add(board);

        // 전광판 화면 (LED 표현)
        const boardScreen = new THREE.Mesh(
            new THREE.PlaneGeometry(22, 8.5),
            new THREE.MeshBasicMaterial({{ color: 0x1e293b }})
        );
        boardScreen.position.set(0, 15, -37.7);
        scene.add(boardScreen);


        // --- 디테일 3D 사람 캐릭터 (얼굴 디테일, 헬멧/모자, 글러브 구현) ---
        function createRealisticHuman(jerseyColor, pantsColor, isBatter) {{
            const group = new THREE.Group();
            const matJersey = new THREE.MeshLambertMaterial({{ color: jerseyColor }});
            const matPants = new THREE.MeshLambertMaterial({{ color: pantsColor }});
            const matSkin = new THREE.MeshLambertMaterial({{ color: 0xfd3d1d }}); // 피부톤
            const matDark = new THREE.MeshBasicMaterial({{ color: 0x111111 }});

            // 1. 머리 & 리얼한 얼굴 디테일
            const head = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), matSkin);
            head.position.y = 1.45;
            group.add(head);

            // 눈
            const eyeGeo = new THREE.SphereGeometry(0.02, 8, 8);
            const eyeL = new THREE.Mesh(eyeGeo, matDark);
            eyeL.position.set(-0.04, 1.47, 0.1);
            const eyeR = new THREE.Mesh(eyeGeo, matDark);
            eyeR.position.set(0.04, 1.47, 0.1);
            group.add(eyeL);
            group.add(eyeR);

            // 코
            const nose = new THREE.Mesh(new THREE.ConeGeometry(0.02, 0.04, 8), matSkin);
            nose.position.set(0, 1.44, 0.12);
            nose.rotation.x = Math.PI / 2;
            group.add(nose);

            // 헬멧 또는 모자
            const capColor = isBatter ? 0xea1d2c : 0x0066b2;
            const capMat = new THREE.MeshLambertMaterial({{ color: capColor }});
            const cap = new THREE.Mesh(new THREE.SphereGeometry(0.13, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2), capMat);
            cap.position.y = 1.46;
            group.add(cap);

            // 모자 챙
            const visor = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.01, 0.1), capMat);
            visor.position.set(0, 1.5, 0.15);
            visor.rotation.x = -0.1;
            group.add(visor);

            // 2. 상체 유니폼
            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.15, 0.55), matJersey);
            torso.position.y = 1.05;
            group.add(torso);

            // 3. 팔 & 손/글러브
            const armR = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.45), matJersey);
            armR.position.set(-0.22, 1.1, 0);
            group.add(armR);

            const armL = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.45), matJersey);
            armL.position.set(0.22, 1.1, 0);
            group.add(armL);

            let glove = null;
            if(!isBatter) {{
                // 투수의 왼손 야구 글러브 착용
                const gloveGeo = new THREE.BoxGeometry(0.12, 0.14, 0.1);
                const gloveMat = new THREE.MeshLambertMaterial({{ color: 0x78350f }}); // 브라운 글러브
                glove = new THREE.Mesh(gloveGeo, gloveMat);
                glove.position.set(0.25, 0.9, 0.08);
                group.add(glove);
            }}

            // 4. 하체
            const legR = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.6), matPants);
            legR.position.set(-0.1, 0.4, 0);
            group.add(legR);

            const legL = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.6), matPants);
            legL.position.set(0.1, 0.4, 0);
            group.add(legL);

            return {{ group, armR, armL, torso, glove }};
        }}

        const PITCHER_Z = -18.44;

        // 투수 (삼성 유니폼 + 글러브)
        const pitcherChar = createRealisticHuman(0x0066b2, 0xffffff, false);
        pitcherChar.group.position.set(0, 0, PITCHER_Z);
        scene.add(pitcherChar.group);

        // 타자 (KIA 유니폼 + 얼굴 디테일 + 헬멧)
        const batterChar = createRealisticHuman(0xea1d2c, 0xffffff, true);
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

        // --- 구종 및 물리 상태 변수 ---
        let isWaiting = false;
        let isWindup = false;
        let isPitching = false;
        let isHitBallMoving = false;
        
        let countdownVal = 5;
        let pitchStartTime = 0;
        let windupStartTime = 0;
        let hasSwung = false;

        const pitchTypeStr = "{pitch_type}";
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

        // 키보드 키 이벤트: '1' 키로 투구 시작, '스페이스바'로 타격
        window.addEventListener('keydown', (e) => {{
            if (e.key === '1') {{
                startPitchSequence();
            }} else if (e.code === 'Space' && (isPitching || isWindup) && !hasSwung) {{
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

        function toggleFullScreen() {{
            const elem = document.getElementById('game-container');
            if (!document.fullscreenElement) {{
                elem.requestFullscreen().catch(err => alert(err.message));
            }} else {{
                document.exitFullscreen();
            }}
        }}

        // --- 애니메이션 및 구종별 궤적 처리 루프 ---
        function animate() {{
            requestAnimationFrame(animate);

            // 1. 투수 와인드업 애니메이션 (글러브 모았다가 양팔 휘두름)
            if (isWindup) {{
                const elapsed = Date.now() - windupStartTime;
                if (elapsed < 700) {{
                    const ratio = elapsed / 700;
                    pitcherChar.armR.rotation.x = -Math.PI * ratio * 1.2; // 오른팔 크게 회전
                    if(pitcherChar.glove) {{
                        pitcherChar.glove.position.y = 0.9 + Math.sin(ratio * Math.PI) * 0.4; // 글러브 모으기 동작
                    }}
                }} else {{
                    isWindup = false;
                    isPitching = true;
                    pitchStartTime = Date.now();
                    document.getElementById('countdown').innerText = "PITCH!";
                    setTimeout(() => {{ document.getElementById('countdown').innerText = ""; }}, 400);
                }}
            }}

            // 2. 구종별 세부 3D 비행 궤적 (직구, 슬라이더, 커브, 포크볼, 체인지업)
            if (isPitching) {{
                const elapsed = Date.now() - pitchStartTime;
                const progress = elapsed / flightTime;

                if (progress <= 1.0) {{
                    // Z축 기본 이동
                    ball.position.z = PITCHER_Z + (0 - PITCHER_Z) * progress;

                    // 구종별 변화구 궤적 계산
                    if (pitchTypeStr.includes("슬라이더")) {{
                        // 슬라이더: 타자 가까이 와서 우타자 바깥쪽(오른쪽)으로 꺾임
                        ball.position.x = Math.pow(progress, 2) * 0.75;
                    }} else if (pitchTypeStr.includes("커브")) {{
                        // 커브: 위로 떠올랐다가 타석 앞에서 커다란 포물선 그리며 큰 폭으로 종낙하
                        ball.position.y = 1.5 + Math.sin(progress * Math.PI) * 0.8 - Math.pow(progress, 2) * 0.9;
                    }} else if (pitchTypeStr.includes("포크볼")) {{
                        // 포크볼: 직구처럼 오다가 홈플레이트 바로 앞에서 뚝 떨어짐
                        const dropTrigger = Math.max(0, progress - 0.5);
                        ball.position.y = 1.5 - Math.pow(dropTrigger * 2, 3) * 0.8;
                    }} else if (pitchTypeStr.includes("체인지업")) {{
                        // 체인지업: 좌타자 바깥쪽(왼쪽)으로 가라앉으며 꺾임
                        ball.position.x = -Math.pow(progress, 2) * 0.45;
                        ball.position.y = 1.5 - Math.sin(progress * Math.PI) * 0.3;
                    }} else {{
                        // 직구 (Four-Seam): 직선형 궤적
                        ball.position.x = 0;
                        ball.position.y = 1.5 - progress * 0.2;
                    }}
                }} else {{
                    if (!hasSwung) showResult("⚾ 루킹 스트라이크!", "#fbbf24");
                    isPitching = false;
                    document.getElementById('pitch-btn').disabled = false;
                }}
            }}

            // 3. 타구 이동
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
# ==========================================
# [맨 밑에 추가할 오디오 전용 재생 코드]
# ==========================================
import streamlit.components.v1 as components

# 이미지의 YouTube 동영상 ID
YOUTUBE_VIDEO_ID = "kdtmY_4pd2E"

# 경기장 레이아웃에 영향을 주지 않도록 독립된 플레이스홀더 생성
sound_container = st.empty()

if any(keyword in st.session_state.get('last_result', '') for keyword in ["깡", "홈런", "안타", "아웃"]):
    with sound_container:
        components.html(
            f"""
            <div style="display:none;">
                <iframe width="0" height="0" 
                        src="https://www.youtube-nocookie.com/embed/{YOUTUBE_VIDEO_ID}?autoplay=1&controls=0" 
                        allow="autoplay">
                </iframe>
            </div>
            """,
            height=0,
            width=0
        )
