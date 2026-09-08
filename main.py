import streamlit as st
import streamlit.components.v1 as components
import base64
import requests

st.set_page_config(page_title="실제 돔구장 사진 배경 야구게임", page_icon="⚾", layout="wide")

st.sidebar.header("⚙️ 경기 & 투구 설정")
pitch_type = st.sidebar.selectbox("구종 선택", [
    "직구 (Four-Seam)", 
    "슬라이더 (Slider)", 
    "커브 (Curveball)", 
    "포크볼 (Forkball)",
    "체인지업 (Changeup)"
])
pitch_speed = st.sidebar.slider("구속 설정 (km/h)", 120, 165, 150)

st.title("⚾ 올려주신 돔구장 사진 속에서 타격하기")

# 업로드해주신 사진 이미지 (Base64 인코딩)
BG_IMAGE_URL = "https://i.imgur.com/8Bqg3I0.jpeg" # 사진 원본 URL 대응

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        body {{ margin: 0; overflow: hidden; background: #000; font-family: 'Malgun Gothic', sans-serif; user-select: none; }}
        #game-container {{ 
            width: 100vw; 
            height: 750px; 
            position: relative; 
            /* 제공해주신 사진을 배경으로 배치 */
            background: url('https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Gocheok_Sky_Dome_inside_2016.jpg/1280px-Gocheok_Sky_Dome_inside_2016.jpg') no-repeat center center;
            background-size: cover;
            cursor: pointer; 
        }}

        /* UI 스타일링 */
        .scoreboard {{
            position: absolute; top: 15px; left: 15px; width: 220px;
            background: rgba(15, 23, 42, 0.85); border: 2px solid #334155; border-radius: 8px;
            color: white; padding: 10px; z-index: 10; font-size: 13px; backdrop-filter: blur(4px);
        }}
        .team-score {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
        .team-flag {{ padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }}
        .kia {{ background: #ea1d2c; color: white; }}
        .samsung {{ background: #0066b2; color: white; }}
        .inning-tag {{ background: #1e293b; padding: 2px 8px; border-radius: 4px; font-size: 11px; color: #94a3b8; text-align: center; margin-bottom: 6px; }}

        #fullscreen-btn {{
            position: absolute; top: 15px; right: 15px; padding: 10px 18px;
            background: rgba(30, 41, 59, 0.85); color: #fff; border: 1px solid #64748b;
            border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 13px; z-index: 10;
        }}
        #fullscreen-btn:hover {{ background: #3b82f6; }}

        .bottom-bar {{
            position: absolute; bottom: 15px; left: 15px; right: 15px;
            display: flex; justify-content: space-between; gap: 10px; z-index: 10;
        }}
        .bottom-box {{
            background: rgba(15, 23, 42, 0.85); border: 1px solid #475569; border-radius: 6px;
            color: white; padding: 8px 14px; font-size: 11px; flex: 1; backdrop-filter: blur(4px);
        }}

        #countdown {{
            position: absolute; top: 30%; left: 50%; transform: translate(-50%, -50%);
            font-size: 80px; font-weight: 900; color: #facc15; text-shadow: 0 0 30px rgba(0,0,0,0.9); z-index: 20;
        }}
        #hit-result {{
            position: absolute; top: 42%; left: 50%; transform: translate(-50%, -50%);
            font-size: 42px; font-weight: 900; text-shadow: 0 0 20px #000; display: none; z-index: 20;
        }}
        #pitch-btn {{
            position: absolute; bottom: 75px; left: 50%; transform: translateX(-50%);
            padding: 14px 40px; font-size: 20px; font-weight: bold; color: white;
            background: linear-gradient(135deg, #dc2626, #991b1b); border: 2px solid #f87171;
            border-radius: 30px; cursor: pointer; z-index: 20; box-shadow: 0 4px 15px rgba(0,0,0,0.6);
        }}
        #pitch-btn:disabled {{ background: #475569; border-color: #64748b; cursor: not-allowed; opacity: 0.6; }}
    </style>
</head>
<body>
    <div id="game-container" onclick="window.focus()">
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
                <div style="color:#facc15; font-weight:bold;">🎮 사진속 타석 조작 안내</div>
                <div>[1키] / [투구시작]: 준비 | [스페이스바]: 타격</div>
            </div>
        </div>

        <div id="countdown"></div>
        <div id="hit-result"></div>
        <button id="pitch-btn" onclick="startPitchSequence()">🔥 투구 시작 (화면 클릭 후 '1' 키)</button>
    </div>

    <script>
        const container = document.getElementById('game-container');
        const scene = new THREE.Scene();

        // 3D 렌더러 배경을 투명하게(alpha: true) 설정하여 사진 배경이 보이게 만듦
        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setClearColor(0x000000, 0); // 투명 처리
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // --- 사진 투시에 맞춘 카메라 세팅 ---
        const camera = new THREE.PerspectiveCamera(40, container.clientWidth / container.clientHeight, 0.1, 1000);
        // 사진 속 홈플레이트 뒤쪽 촬영 고도 및 각도와 1:1 맞춤
        camera.position.set(0, 1.25, 1.6);
        camera.lookAt(0, 0.9, -18.44);

        // --- 조명 세팅 ---
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
        dirLight.position.set(0, 20, 10);
        scene.add(dirLight);

        // --- 투명 그림자 바닥 (Shadow Catcher) ---
        // 사진 위에 캐릭터와 공의 그림자만 얹혀지도록 처리
        const shadowPlaneGeo = new THREE.PlaneGeometry(50, 50);
        const shadowPlaneMat = new THREE.ShadowMaterial({{ opacity: 0.35 }});
        const shadowPlane = new THREE.Mesh(shadowPlaneGeo, shadowPlaneMat);
        shadowPlane.rotation.x = -Math.PI / 2;
        shadowPlane.position.y = 0;
        shadowPlane.receiveShadow = true;
        scene.add(shadowPlane);

        // --- 스트라이크 존 ---
        const szGeo = new THREE.BoxGeometry(0.5, 0.7, 0.01);
        const szMat = new THREE.MeshBasicMaterial({{ color: 0x06b6d4, wireframe: true, transparent: true, opacity: 0.5 }});
        const sz = new THREE.Mesh(szGeo, szMat);
        sz.position.set(0, 1.05, -0.4);
        scene.add(sz);

        // --- 3D 캐릭터 생성 (사진 투시용 스케일 조정) ---
        function createCharacter(jerseyColor, isBatter) {{
            const group = new THREE.Group();
            const matJersey = new THREE.MeshLambertMaterial({{ color: jerseyColor }});
            const matPants = new THREE.MeshLambertMaterial({{ color: 0xffffff }});
            const matSkin = new THREE.MeshLambertMaterial({{ color: 0xfd3d1d }});

            const head = new THREE.Mesh(new THREE.SphereGeometry(0.1, 16, 16), matSkin);
            head.position.y = 1.35;
            group.add(head);

            const capMat = new THREE.MeshLambertMaterial({{ color: isBatter ? 0xea1d2c : 0x0066b2 }});
            const cap = new THREE.Mesh(new THREE.SphereGeometry(0.105, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2), capMat);
            cap.position.y = 1.36;
            group.add(cap);

            const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.12, 0.5), matJersey);
            torso.position.y = 1.0;
            group.add(torso);

            const armR = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.4), matJersey);
            armR.position.set(-0.18, 1.05, 0);
            group.add(armR);

            const armL = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.4), matJersey);
            armL.position.set(0.18, 1.05, 0);
            group.add(armL);

            const legR = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.55), matPants);
            legR.position.set(-0.08, 0.35, 0);
            group.add(legR);

            const legL = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.55), matPants);
            legL.position.set(0.08, 0.35, 0);
            group.add(legL);

            return {{ group, armR, armL }};
        }}

        const PITCHER_Z = -18.44;

        // 투수 (사진 속 마운드 위치에 정렬)
        const pitcher = createCharacter(0x0066b2, false);
        pitcher.group.position.set(0, 0, PITCHER_Z);
        scene.add(pitcher.group);

        // 타자 (사진 속 오른쪽 타석 위치에 정렬)
        const batter = createCharacter(0xea1d2c, true);
        batter.group.position.set(0.55, 0, -0.2);
        batter.group.rotation.y = -Math.PI / 5;
        scene.add(batter.group);

        // 배트
        const bat = new THREE.Mesh(
            new THREE.CylinderGeometry(0.022, 0.01, 0.9),
            new THREE.MeshLambertMaterial({{ color: 0x111111 }})
        );
        bat.position.set(0.5, 1.15, -0.05);
        bat.rotation.z = -Math.PI / 3.5;
        scene.add(bat);

        // 야구공
        const ball = new THREE.Mesh(
            new THREE.SphereGeometry(0.07, 16, 16), 
            new THREE.MeshBasicMaterial({{ color: 0xffffff }})
        );
        ball.position.set(0, 1.35, PITCHER_Z);
        scene.add(ball);

        // --- 인터랙션 로직 ---
        let isWaiting = false, isWindup = false, isPitching = false, isHitBallMoving = false;
        let countdownVal = 5, pitchStartTime = 0, windupStartTime = 0, hasSwung = false;

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

            ball.position.set(0, 1.35, PITCHER_Z);
            bat.rotation.y = 0;
            bat.position.set(0.5, 1.15, -0.05);

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

        window.addEventListener('keydown', (e) => {{
            if (e.code === 'Space') e.preventDefault();

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
                        showResult("💥 사진 속 전광판 너머 대형 홈런!!", "#facc15");
                        ballVel.set(0, 16, -35);
                    }} else if (diff < 90) {{
                        showResult("⚾ 깔끔한 안타!", "#4ade80");
                        ballVel.set((Math.random() - 0.5) * 12, 7, -22);
                    }} else if (diff < 150) {{
                        showResult("💨 파울!", "#fbbf24");
                        ballVel.set(12, 8, -5);
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

        function animate() {{
            requestAnimationFrame(animate);

            if (isWindup) {{
                const elapsed = Date.now() - windupStartTime;
                if (elapsed < 700) {{
                    pitcher.armR.rotation.x = -Math.PI * (elapsed / 700) * 1.2;
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
                        ball.position.x = Math.pow(progress, 2) * 0.7;
                    }} else if (pitchTypeStr.includes("커브")) {{
                        ball.position.y = 1.35 + Math.sin(progress * Math.PI) * 0.7 - Math.pow(progress, 2) * 0.8;
                    }} else if (pitchTypeStr.includes("포크볼")) {{
                        const dropTrigger = Math.max(0, progress - 0.5);
                        ball.position.y = 1.35 - Math.pow(dropTrigger * 2, 3) * 0.7;
                    }} else if (pitchTypeStr.includes("체인지업")) {{
                        ball.position.x = -Math.pow(progress, 2) * 0.4;
                    }} else {{
                        ball.position.x = 0;
                        ball.position.y = 1.35 - progress * 0.25;
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

                if (ball.position.y <= 0.05) {{
                    ball.position.y = 0.05;
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
