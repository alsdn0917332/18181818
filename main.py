import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="KBO 3D 돔구장 리얼 야구장", page_icon="⚾", layout="wide")

st.sidebar.header("⚙️ 경기 & 투구 설정")
pitch_type = st.sidebar.selectbox("구종 선택", [
    "직구 (Four-Seam)", 
    "슬라이더 (Slider)", 
    "커브 (Curveball)", 
    "포크볼 (Forkball)",
    "체인지업 (Changeup)"
])
pitch_speed = st.sidebar.slider("구속 설정 (km/h)", 120, 165, 150)

st.title("⚾ 3D KBO 고척 돔구장 실전 시뮬레이터")

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        body {{ margin: 0; overflow: hidden; background: #000; font-family: 'Malgun Gothic', sans-serif; user-select: none; }}
        #game-container {{ width: 100vw; height: 750px; position: relative; background: #0f172a; cursor: pointer; }}

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
    <div id="game-container" onclick="window.focus()">
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
                <div style="color:#facc15; font-weight:bold;">🎮 조작 안내 (화면 클릭 후 입력)</div>
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
        scene.background = new THREE.Color(0x1e293b); // 돔구장 은은한 배경색

        // --- 카메라 시점 설정 ---
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        camera.position.set(0, 1.4, 2.1);
        camera.lookAt(0, 1.2, -18.44);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // --- 돔구장 내부 광원 세팅 ---
        const ambientLight = new THREE.AmbientLight(0x94a3b8, 0.8);
        scene.add(ambientLight);

        // 돔 천장 대형 조명 링
        function createDomeSpotlight(x, y, z) {{
            const light = new THREE.SpotLight(0xffffff, 1.2);
            light.position.set(x, y, z);
            light.target.position.set(0, 0, -15);
            light.angle = Math.PI / 3;
            scene.add(light);
        }}
        createDomeSpotlight(-20, 25, -10);
        createDomeSpotlight(20, 25, -10);
        createDomeSpotlight(-20, 25, -30);
        createDomeSpotlight(20, 25, -30);

        // --- 돔 스카이돔 천장 & 트러스 구조물 ---
        // 1. 돔 천장 돔 쉘
        const domeRoofGeo = new THREE.SphereGeometry(60, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2.2);
        const domeRoofMat = new THREE.MeshLambertMaterial({{ 
            color: 0x475569, 
            side: THREE.BackSide, 
            transparent: true, 
            opacity: 0.85 
        }});
        const domeRoof = new THREE.Mesh(domeRoofGeo, domeRoofMat);
        domeRoof.position.set(0, -5, -20);
        scene.add(domeRoof);

        // 2. 돔 천장 중앙 원형 천창 (Sky Light)
        const skylightGeo = new THREE.CircleGeometry(18, 32);
        const skylightMat = new THREE.MeshBasicMaterial({{ color: 0xcfe2fe, side: THREE.DoubleSide, transparent: true, opacity: 0.4 }});
        const skylight = new THREE.Mesh(skylightGeo, skylightMat);
        skylight.rotation.x = Math.PI / 2;
        skylight.position.set(0, 34, -20);
        scene.add(skylight);

        // 3. 돔 천장 격자 철골 구조 (Truss Grid)
        for (let i = 0; i < 12; i++) {{
            const angle = (i / 12) * Math.PI * 2;
            const ringGeo = new THREE.TorusGeometry(25 + (i % 3) * 10, 0.25, 8, 48);
            const ringMat = new THREE.MeshBasicMaterial({{ color: 0x334155 }});
            const ring = new THREE.Mesh(ringGeo, ringMat);
            ring.rotation.x = Math.PI / 2;
            ring.position.set(0, 15 + (i * 1.5), -20);
            scene.add(ring);
        }}

        // --- 돔구장 필드 및 내/외야 세팅 ---
        // 1. 인조잔디 메인 필드
        const fieldGeo = new THREE.PlaneGeometry(120, 120);
        const fieldMat = new THREE.MeshLambertMaterial({{ color: 0x166534 }});
        const field = new THREE.Mesh(fieldGeo, fieldMat);
        field.rotation.x = -Math.PI / 2;
        scene.add(field);

        // 잔디 패턴
        for(let i = -50; i < 50; i += 6) {{
            const stripeGeo = new THREE.PlaneGeometry(120, 3);
            const stripeMat = new THREE.MeshLambertMaterial({{ color: 0x15803d, transparent: true, opacity: 0.4 }});
            const stripe = new THREE.Mesh(stripeGeo, stripeMat);
            stripe.rotation.x = -Math.PI / 2;
            stripe.position.set(0, 0.005, i);
            scene.add(stripe);
        }}

        // 2. 내야 흙 다이아몬드 & 워닝트랙
        const dirtGeo = new THREE.PlaneGeometry(22, 32);
        const dirtMat = new THREE.MeshLambertMaterial({{ color: 0x9a3412 }});
        const dirt = new THREE.Mesh(dirtGeo, dirtMat);
        dirt.rotation.x = -Math.PI / 2;
        dirt.position.set(0, 0.01, -11);
        scene.add(dirt);

        // 홈플레이트 주변 흙 앙투파 원형
        const homeDirtGeo = new THREE.CircleGeometry(7, 32);
        const homeDirt = new THREE.Mesh(homeDirtGeo, dirtMat);
        homeDirt.rotation.x = -Math.PI / 2;
        homeDirt.position.set(0, 0.012, 0);
        scene.add(homeDirt);

        // 3. 스트라이크 존
        const szGeo = new THREE.BoxGeometry(0.52, 0.72, 0.01);
        const szMat = new THREE.MeshBasicMaterial({{ color: 0x06b6d4, wireframe: true, transparent: true, opacity: 0.6 }});
        const sz = new THREE.Mesh(szGeo, szMat);
        sz.position.set(0, 1.2, -0.4);
        scene.add(sz);

        // 4. 홈플레이트 & 타석 라인
        const hp = new THREE.Mesh(new THREE.BoxGeometry(0.43, 0.02, 0.43), new THREE.MeshBasicMaterial({{ color: 0xffffff }}));
        hp.position.set(0, 0.02, 0);
        scene.add(hp);

        const boxLineGeo = new THREE.BoxGeometry(0.8, 0.01, 1.8);
        const lineMat = new THREE.MeshBasicMaterial({{ color: 0xffffff, transparent: true, opacity: 0.8 }});
        
        const rBox = new THREE.Mesh(boxLineGeo, lineMat);
        rBox.position.set(0.65, 0.015, -0.2);
        scene.add(rBox);

        const lBox = new THREE.Mesh(boxLineGeo, lineMat);
        lBox.position.set(-0.65, 0.015, -0.2);
        scene.add(lBox);

        // 5. 돔 펜스, 블루 계열 구조물 및 대형 중앙 전광판
        const fenceGeo = new THREE.CylinderGeometry(45, 45, 4, 32, 1, true, -Math.PI/2.4, Math.PI/1.2);
        const fenceMat = new THREE.MeshLambertMaterial({{ color: 0x1e3a8a, side: THREE.DoubleSide }});
        const fence = new THREE.Mesh(fenceGeo, fenceMat);
        fence.position.set(0, 2, -20);
        scene.add(fence);

        // 관중석 3단 스탠드
        for(let s = 1; s <= 3; s++) {{
            const standGeo = new THREE.CylinderGeometry(45 + s*5, 45 + s*5, 3, 32, 1, true, -Math.PI/2.3, Math.PI/1.15);
            const standMat = new THREE.MeshLambertMaterial({{ color: 0x334155, side: THREE.DoubleSide }});
            const stand = new THREE.Mesh(standGeo, standMat);
            stand.position.set(0, 2 + s*2.5, -20);
            scene.add(stand);
        }}

        // 대형 돔 전광판 (고척 스카이돔 스타일)
        const board = new THREE.Mesh(
            new THREE.BoxGeometry(20, 8, 0.5),
            new THREE.MeshLambertMaterial({{ color: 0x0f172a }})
        );
        board.position.set(0, 16, -36);
        scene.add(board);

        const boardScreen = new THREE.Mesh(
            new THREE.PlaneGeometry(18.5, 6.8),
            new THREE.MeshBasicMaterial({{ color: 0x0284c7 }})
        );
        boardScreen.position.set(0, 16, -35.7);
        scene.add(boardScreen);

        // --- 3D 캐릭터 모델링 ---
        function createRealisticHuman(jerseyColor, pantsColor, isBatter) {{
            const group = new THREE.Group();
            const matJersey = new THREE.MeshLambertMaterial({{ color: jerseyColor }});
            const matPants = new THREE.MeshLambertMaterial({{ color: pantsColor }});
            const matSkin = new THREE.MeshLambertMaterial({{ color: 0xfd3d1d }});
            const matDark = new THREE.MeshBasicMaterial({{ color: 0x111111 }});

            const head = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 16), matSkin);
            head.position.y = 1.45;
            group.add(head);

            const eyeGeo = new THREE.SphereGeometry(0.02, 8, 8);
            const eyeL = new THREE.Mesh(eyeGeo, matDark);
            eyeL.position.set(-0.04, 1.47, 0.1);
            const eyeR = new THREE.Mesh(eyeGeo, matDark);
            eyeR.position.set(0.04, 1.47, 0.1);
            group.add(eyeL);
            group.add(eyeR);

            const capColor = isBatter ? 0xea1d2c : 0x0066b2;
            const capMat = new THREE.MeshLambertMaterial({{ color: capColor }});
            const cap = new THREE.Mesh(new THREE.SphereGeometry(0.13, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2), capMat);
            cap.position.y = 1.46;
            group.add(cap);

            const visor = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.01, 0.1), capMat);
            visor.position.set(0, 1.5, 0.15);
            visor.rotation.x = -0.1;
            group.add(visor);

            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.15, 0.55), matJersey);
            torso.position.y = 1.05;
            group.add(torso);

            const armR = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.45), matJersey);
            armR.position.set(-0.22, 1.1, 0);
            group.add(armR);

            const armL = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.45), matJersey);
            armL.position.set(0.22, 1.1, 0);
            group.add(armL);

            let glove = null;
            if(!isBatter) {{
                const gloveGeo = new THREE.BoxGeometry(0.12, 0.14, 0.1);
                const gloveMat = new THREE.MeshLambertMaterial({{ color: 0x78350f }});
                glove = new THREE.Mesh(gloveGeo, gloveMat);
                glove.position.set(0.25, 0.9, 0.08);
                group.add(glove);
            }}

            const legR = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.6), matPants);
            legR.position.set(-0.1, 0.4, 0);
            group.add(legR);

            const legL = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.6), matPants);
            legL.position.set(0.1, 0.4, 0);
            group.add(legL);

            return {{ group, armR, armL, torso, glove }};
        }}

        const PITCHER_Z = -18.44;

        const pitcherChar = createRealisticHuman(0x0066b2, 0xffffff, false);
        pitcherChar.group.position.set(0, 0, PITCHER_Z);
        scene.add(pitcherChar.group);

        const batterChar = createRealisticHuman(0xea1d2c, 0xffffff, true);
        batterChar.group.position.set(0.5, 0, -0.2);
        batterChar.group.rotation.y = -Math.PI / 6;
        scene.add(batterChar.group);

        const bat = new THREE.Mesh(
            new THREE.CylinderGeometry(0.025, 0.012, 0.95),
            new THREE.MeshLambertMaterial({{ color: 0x111111 }})
        );
        bat.position.set(0.48, 1.25, -0.05);
        bat.rotation.z = -Math.PI / 3.5;
        scene.add(bat);

        const ball = new THREE.Mesh(new THREE.SphereGeometry(0.08, 16, 16), new THREE.MeshBasicMaterial({{ color: 0xffffff }}));
        ball.position.set(0, 1.5, PITCHER_Z);
        scene.add(ball);

        // --- 물리 및 시뮬레이션 로직 ---
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

        // 키보드 이벤트 및 스크롤 방지
        window.addEventListener('keydown', (e) => {{
            if (e.code === 'Space') {{
                e.preventDefault(); // 스페이스바 스크롤 현상 방지
            }}

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
                        showResult("💥 대형 돔런!! (HOMERUN)", "#facc15");
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

        // 애니메이션 루프
        function animate() {{
            requestAnimationFrame(animate);

            if (isWindup) {{
                const elapsed = Date.now() - windupStartTime;
                if (elapsed < 700) {{
                    const ratio = elapsed / 700;
                    pitcherChar.armR.rotation.x = -Math.PI * ratio * 1.2;
                    if(pitcherChar.glove) {{
                        pitcherChar.glove.position.y = 0.9 + Math.sin(ratio * Math.PI) * 0.4;
                    }}
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

                    if (pitchTypeStr.includes("슬라이더")) {{
                        ball.position.x = Math.pow(progress, 2) * 0.75;
                    }} else if (pitchTypeStr.includes("커브")) {{
                        ball.position.y = 1.5 + Math.sin(progress * Math.PI) * 0.8 - Math.pow(progress, 2) * 0.9;
                    }} else if (pitchTypeStr.includes("포크볼")) {{
                        const dropTrigger = Math.max(0, progress - 0.5);
                        ball.position.y = 1.5 - Math.pow(dropTrigger * 2, 3) * 0.8;
                    }} else if (pitchTypeStr.includes("체인지업")) {{
                        ball.position.x = -Math.pow(progress, 2) * 0.45;
                        ball.position.y = 1.5 - Math.sin(progress * Math.PI) * 0.3;
                    }} else {{
                        ball.position.x = 0;
                        ball.position.y = 1.5 - progress * 0.2;
                    }}
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
