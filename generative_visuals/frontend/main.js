/**
 * Silent Dialogues of Care - 境界なき対話
 * Three.jsを使用した感情視覚化モジュール
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
import { createRenderer, isWebGPUSupported } from './webgpu_renderer.js';
import { EnhancedParticleSystem } from './enhanced_particles.js';
import { EnhancedTextSystem } from './enhanced_text.js';
import { calculateVisualParameters, analyzeText } from './emotion_analysis.js';
import { updateVisualSystems } from './visual_systems.js';

// グローバル変数
let scene, camera, renderer, composer;
let controls;
let enhancedParticles, enhancedText;
let currentEmotionData = null;
let currentTextData = null;
let emotionTransitionTime = 2.0; // 感情遷移の時間（秒）
let lastUpdateTime = 0;
let isWebGPUEnabled = false;

// WebSocket接続
let socket;
const serverUrl = 'ws://localhost:8765/ws';

// デバッグモード
let isDebugMode = false;

// 色のマッピング（感情ごとの色）
const emotionColors = {
    // 基本感情
    'neutral': { color: new THREE.Color(0x888888), intensity: 0.5 },
    'happy': { color: new THREE.Color(0xffee00), intensity: 1.2 },
    'sad': { color: new THREE.Color(0x0066cc), intensity: 0.7 },
    'surprise': { color: new THREE.Color(0xff00ff), intensity: 1.5 },
    'fear': { color: new THREE.Color(0x660066), intensity: 0.9 },
    'anger': { color: new THREE.Color(0xff0000), intensity: 1.3 },
    'disgust': { color: new THREE.Color(0x006600), intensity: 0.8 },
    'contempt': { color: new THREE.Color(0x555500), intensity: 0.6 },
    
    // 拡張感情
    'interest': { color: new THREE.Color(0x00ccff), intensity: 1.0 },
    'amusement': { color: new THREE.Color(0xffaa00), intensity: 1.1 },
    'awe': { color: new THREE.Color(0xaa00ff), intensity: 1.2 },
    'contentment': { color: new THREE.Color(0x00aa88), intensity: 0.9 },
    'desire': { color: new THREE.Color(0xff6600), intensity: 1.1 },
    'disappointment': { color: new THREE.Color(0x664400), intensity: 0.7 },
    'doubt': { color: new THREE.Color(0x777777), intensity: 0.6 },
    'elation': { color: new THREE.Color(0xffff00), intensity: 1.4 },
    'pain': { color: new THREE.Color(0x990000), intensity: 0.8 },
    'sadness': { color: new THREE.Color(0x0066aa), intensity: 0.7 },
    'tiredness': { color: new THREE.Color(0x445566), intensity: 0.4 },
    'triumph': { color: new THREE.Color(0xffdd00), intensity: 1.5 }
};

// 初期化処理
async function init() {
    // シーンの作成
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);
    
    // カメラの設定
    const aspect = window.innerWidth / window.innerHeight;
    camera = new THREE.PerspectiveCamera(70, aspect, 0.1, 1000);
    camera.position.z = 15;
    
    // WebGPU対応レンダラーの作成
    const canvasContainer = document.getElementById('canvas-container');
    renderer = await createRenderer(canvasContainer);
    
    // WebGPUサポート状況を表示
    isWebGPUEnabled = renderer.constructor.name === 'WebGPURenderer';
    console.log(`レンダラータイプ: ${isWebGPUEnabled ? 'WebGPU' : 'WebGL'}`);
    
    // レンダラーの設定
    if (!isWebGPUEnabled) {
        // WebGLの場合、追加設定
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        if (renderer.outputEncoding !== undefined) {  // THREE.js r152以降は非推奨
            renderer.outputEncoding = THREE.sRGBEncoding;
        }
    }
    
    // OrbitControlsの設定
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.5;
    
    // ポストプロセッシングの設定
    setupPostProcessing();
    
    // 拡張パーティクルシステムの作成
    enhancedParticles = new EnhancedParticleSystem(scene, {
        particleCount: 10000,
        particleSize: 0.08,
        particleSpeed: 0.5,
        waveIntensity: 0.5,
        particleShape: 'circle',
        turbulence: 0.5,
        harmonyFactor: 0.5,
        expansionRate: 1.0
    });
    
    // 拡張テキストシステムの作成
    enhancedText = new EnhancedTextSystem(scene, {
        textComplexity: 0.5,
        textRhythm: 0.5,
        textEmphasis: 0.5,
        textGeometry: 'float',
        textAnimation: 'fade',
        textDensity: 1.0
    });
    
    // 環境光の追加
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
    scene.add(ambientLight);
    
    // 点光源の追加
    const pointLight = new THREE.PointLight(0xffffff, 1);
    pointLight.position.set(0, 0, 0);
    scene.add(pointLight);
    
    // ウィンドウリサイズイベントの設定
    window.addEventListener('resize', onWindowResize);
    
    // WebSocket接続
    connectWebSocket();
    
    // デバッグパネルの初期化
    initDebugPanel();
    
    // 初期感情の設定（ニュートラル）
    updateEmotionState({
        primary_emotion: 'neutral',
        valence: 0,
        activation: 0
    });
    
    // アニメーションループの開始
    animate();
}

// ポストプロセッシングのセットアップ
function setupPostProcessing() {
    // エフェクトコンポーザーの作成
    composer = new EffectComposer(renderer);
    
    // レンダーパスの追加
    const renderPass = new RenderPass(scene, camera);
    composer.addPass(renderPass);
    
    // ブルームエフェクトの追加
    const bloomPass = new UnrealBloomPass(
        new THREE.Vector2(window.innerWidth, window.innerHeight),
        0.8,  // 強度
        0.3,  // 半径
        0.9   // 閾値
    );
    composer.addPass(bloomPass);
    
    // カスタムシェーダーパスの追加（色彩収差エフェクト）
    const chromaticAberrationShader = {
        uniforms: {
            'tDiffuse': { value: null },
            'resolution': { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
            'aberration': { value: 0.01 }
        },
        vertexShader: `
            varying vec2 vUv;
            void main() {
                vUv = uv;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform sampler2D tDiffuse;
            uniform vec2 resolution;
            uniform float aberration;
            varying vec2 vUv;
            
            void main() {
                vec2 uv = vUv;
                
                vec2 direction = normalize(uv - 0.5);
                vec2 distortion = direction * aberration;
                
                vec4 r = texture2D(tDiffuse, uv - distortion);
                vec4 g = texture2D(tDiffuse, uv);
                vec4 b = texture2D(tDiffuse, uv + distortion);
                
                gl_FragColor = vec4(r.r, g.g, b.b, 1.0);
            }
        `
    };
    
    const chromaticAberrationPass = new ShaderPass(chromaticAberrationShader);
    composer.addPass(chromaticAberrationPass);
}

// パーティクルシステムの作成
function createParticleSystem() {
    const particleCount = 10000;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    
    const color = new THREE.Color();
    
    for (let i = 0; i < particleCount; i++) {
        // ランダムな球体状の配置
        const radius = 10 * Math.pow(Math.random(), 1/3);
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        
        positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = radius * Math.cos(phi);
        
        // 初期色（ニュートラル）
        color.set(emotionColors.neutral.color);
        colors[i * 3] = color.r;
        colors[i * 3 + 1] = color.g;
        colors[i * 3 + 2] = color.b;
        
        // ランダムなサイズ
        sizes[i] = Math.random() * 0.1 + 0.05;
    }
    
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    
    // パーティクルシェーダー
    const particleMaterial = new THREE.ShaderMaterial({
        uniforms: {
            time: { value: 0 },
            pointTexture: { value: new THREE.TextureLoader().load('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAB3RJTUUH5AQEFDkd6QJ7JQAABb1JREFUWMOtl3uMVFcZxX/n3jvzvAP7gGEXZmGXgVUeLlIwFBqkCkGNklottGq1EbRJG+OfpqY21Q6JaWqitraJtjHGPozBaLFVaRS1ohg1aKkKVGAV5DUw+2BmZ3dmdh537r1+f8wMs8vD1HqSk5v7OPd+53zn+757RVUZjbZuXa1FIrNQnWuMmSEiM1R1sqrmAAXCqtoniF0xONAf5NTW9/fS3t7O/v3vjkaKjBTAli0rZPz48ZSUlCzxPG+ZMeYxY8ydqjoZQEQAOP2fTi5dukRPTw8NDQ1cbrxMyG9ZXHQHFRUVPDDvfqoXVGMco8YYKisrRzQOIwDYvHmZVFZWEovFFvq+/4Qx5jFVzQXo7Ozk3LlzNDU1cau7G1QREbK0m/rMi2T7QzQ3N9Nys4Vbt25hjCEvL4/77ruP0lml5OXlEY/Hqa+vHxHIbQA2bXpI5syZE/Q87zFjzHeBWwC1tbU0NDTQ3t5OYGCAYEcbFgMmQEaDRAZiPHDhEXKcbPxRPxmZGRQWFjJp0iQEoaWlhWvXrtHZ2YkTcCgsLGTu3LnMnDkTz/P47LPPRgVgAGTjxsflwQcf/Knv+38AvgZQV1fH2bNnaW1tJRAIMNDRhs/naYhDZpDHfRMhpxfCDuTkQTwAzVeh3yUUClFSUsLs2bMZN24c0WiUxsZGrl69SiwWwwk4ZGdnU1paSnFxMY2NjYMMpAFs2LBOampqfu953i5gsojw/vvvc+LECSKRCOFwGDsSRrUPx0C2H+b7IZwLWXkQmQDFhbDWwOUYXD0DcZecnBzmz59PcXExvb29NDU1cfnyZTo6OgiFQjiOQzAYpKKigrlz59LV1UVtbe0QAAOwfv132L179x7f938jIo7v+5w4cYILFy4QDocJhkKQSGA0BiokLJSGYIoPbg6ETBQXvmMg0wPvAnE/RGJCYWEh5eXlFBQUEI1Gk0y0tHDz5k3C4TCO4+A4DpMnT6aqqoqCggKOHTvGmTNnhgEQEXnyyXV6+PDhXxtjfqmqZGRksH//flpaWsjLyyOYmYnb1YFKDBHBVzAWwv0wBTA9IHkQGg95Efimwu1+iEUhEYecnByqqqooLCzE8zzC4TD19fXJbAiHCQaDZGZmkp+fT3V1NVVVVXR3d3P06NFhAETkm0DYcZwvbdq06Y+e5/0MIJOkUhsbG8nJySGjsIjA1a9hbD+CkoghWCDhQsKC70IiBjIAEgNJ6FAAg+q3Q2GwFnJycpg/fz7Z2dlYa4nFYnR0dKSyIhgMkpmZCcDkyZOprq6mtLQUay2HDh2ip6cnBcAYUyEimxYuXHgKeAMoB9i3bx+dnZ3k5+eTV1hMZlM9JhHFSYCJu9i4i4m7SLwfcSPgeoj2JQcx4EegPwaedchSa8nJyRnEQl9fX4qFYDCYYmHSpEmUl5dTVlZGJBLh8OHDRKPRlCnvNsb8BPB93/8+ydR77733hrAgQmDKNJzGOkRcJB7FxKOYRBQTd5FYP+L2It4AknARt1cFzADwJdS6Af1fV5dUVtQnAcQHWHA6OzuHsGCtJScnh/vvv5+ysrLULkppQYb8NzIacnNnDnYv0NPTw8GDB+nu7iY/P5+CwkIiGYYexwCw+/DRzs5OVBXX9ZOuXZc9e/Zw/PhxAKy1AKgqruum7qPRaOreWpt6xuAWHGzgDLKyQgDdQHdHRwcHDhwYYWcP3sSsVQCstSkHicFMDL6PRqPDHA9OpSHGR97EBsAH+q21Lw3ueJ7HkSNHkl/O9u3b+eyzs5hAJvF4HGvjWGux1qbuu7q6eOedd9JMI1gbi39HLf9SAXyDHbcDjuM8ZYz5yrRp05w33niDU6dOpfZvXl4ec+bM4csvT3P9+nWstbS1tXHixAlisRjbtm1j+/btYwonAMYYaYfJf/7wGRO9ZrXru35+QUG7MaaIVP37/59U9Rrw5a44Bf4L/MkhRTK8XAIAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjAtMDQtMDRUMjA6NTc6MjkrMDA6MDBjlJQSAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDIwLTA0LTA0VDIwOjU3OjI5KzAwOjAwEsksvgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAAASUVORK5CYII=') }
        },
        vertexShader: `
            attribute float size;
            attribute vec3 color;
            varying vec3 vColor;
            uniform float time;
            
            void main() {
                vColor = color;
                
                // 時間に基づく位置のアニメーション
                vec3 pos = position;
                float pulseFactor = sin(time * 0.5) * 0.05 + 1.0;
                
                // 感情の活性度に応じた波動を加える
                vec4 mvPosition = modelViewMatrix * vec4(pos * pulseFactor, 1.0);
                
                gl_PointSize = size * (300.0 / length(mvPosition.xyz));
                gl_Position = projectionMatrix * mvPosition;
            }
        `,
        fragmentShader: `
            uniform sampler2D pointTexture;
            varying vec3 vColor;
            
            void main() {
                gl_FragColor = vec4(vColor, 1.0) * texture2D(pointTexture, gl_PointCoord);
            }
        `,
        blending: THREE.AdditiveBlending,
        depthTest: false,
        transparent: true,
        vertexColors: true
    });
    
    particleSystem = new THREE.Points(geometry, particleMaterial);
    scene.add(particleSystem);
}

// 感情状態の更新
function updateEmotionState(emotionData, text) {
    if (!emotionData) return;
    
    // 前回の更新時間を記録
    lastUpdateTime = Date.now() / 1000;
    
    // 現在の感情データを保存
    currentEmotionData = emotionData;
    currentTextData = text || null;
    
    // UIの更新
    updateEmotionUI(emotionData);
    
    // 感情と言語分析に基づくビジュアルパラメータの計算
    const visualParams = calculateVisualParameters(emotionData, text);
    
    // パーティクルシステムの更新
    updateVisualSystems(visualParams);
}

// 感情UIの更新
function updateEmotionUI(emotionData) {
    const emotionLabel = document.getElementById('emotion-label');
    const emotionValue = document.getElementById('emotion-value');
    
    // 感情ラベルの設定
    let emotionName = '';
    switch (emotionData.primary_emotion) {
        case 'neutral': emotionName = '中立'; break;
        case 'happy': emotionName = '幸せ'; break;
        case 'sad': emotionName = '悲しみ'; break;
        case 'surprise': emotionName = '驚き'; break;
        case 'fear': emotionName = '恐怖'; break;
        case 'anger': emotionName = '怒り'; break;
        case 'disgust': emotionName = '嫌悪'; break;
        case 'contempt': emotionName = '軽蔑'; break;
        case 'interest': emotionName = '興味'; break;
        case 'amusement': emotionName = '楽しさ'; break;
        case 'awe': emotionName = '畏敬'; break;
        case 'contentment': emotionName = '満足'; break;
        case 'desire': emotionName = '欲望'; break;
        case 'disappointment': emotionName = '失望'; break;
        case 'doubt': emotionName = '疑い'; break;
        case 'elation': emotionName = '高揚'; break;
        case 'pain': emotionName = '痛み'; break;
        case 'tiredness': emotionName = '疲労'; break;
        case 'triumph': emotionName = '勝利'; break;
        default: emotionName = emotionData.primary_emotion; break;
    }
    
    emotionLabel.textContent = emotionName;
    emotionValue.textContent = `感情価: ${emotionData.valence.toFixed(2)}, 活性度: ${emotionData.activation.toFixed(2)}`;
    
    // 感情に応じた色をCSSに設定
    const colorInfo = emotionColors[emotionData.primary_emotion] || emotionColors.neutral;
    document.documentElement.style.setProperty('--emotion-color', `#${colorInfo.color.getHexString()}`);
}

// パーティクル色の更新
function updateParticleColors(emotionData) {
    if (!particleSystem) return;
    
    const colorInfo = emotionColors[emotionData.primary_emotion] || emotionColors.neutral;
    const targetColor = colorInfo.color;
    const intensity = colorInfo.intensity;
    
    // 感情の次元（感情価と活性度）に基づく色の調整
    const valence = emotionData.valence; // -1.0〜1.0
    const activation = emotionData.activation; // -1.0〜1.0
    
    // 感情価に基づく色相の調整
    let hsl = { h: 0, s: 0, l: 0 };
    targetColor.getHSL(hsl);
    
    // 活性度に基づく彩度と輝度の調整
    const saturationFactor = Math.max(0.3, 0.5 + activation * 0.5);
    const lightnessFactor = Math.max(0.3, 0.5 + valence * 0.2);
    
    // 新しい色の作成
    const adjustedColor = new THREE.Color().setHSL(
        hsl.h,
        hsl.s * saturationFactor,
        hsl.l * lightnessFactor
    );
    
    // ポストプロセッシングの調整
    const bloomPass = composer.passes[1];
    bloomPass.strength = 0.8 + Math.abs(activation) * 0.7;
    bloomPass.radius = 0.3 + Math.abs(valence) * 0.4;
    
    const chromaticAberrationPass = composer.passes[2];
    chromaticAberrationPass.uniforms.aberration.value = 0.01 + Math.abs(activation) * 0.02;
    
    // パーティクルの色を徐々に変化させる（アニメーションは animate() 関数で行う）
    particleSystem.userData.targetColor = adjustedColor;
    particleSystem.userData.intensity = intensity;
}

// メッセージの表示
function showMessage(userMessage, aiResponse) {
    const userMessageEl = document.getElementById('user-message');
    const aiResponseEl = document.getElementById('ai-response');
    const messageContainer = document.getElementById('message-container');
    
    // メッセージコンテナを表示
    messageContainer.style.opacity = '1';
    
    if (userMessage) {
        userMessageEl.textContent = userMessage;
        userMessageEl.style.display = 'block';
    } else {
        userMessageEl.style.display = 'none';
    }
    
    if (aiResponse) {
        aiResponseEl.textContent = aiResponse;
        aiResponseEl.style.display = 'block';
        
        // 拡張テキストシステムを使用してテキストを表示
        if (enhancedText) {
            enhancedText.createText(aiResponse, { x: 0, y: 0, z: -5 }, 0xffffff);
        }
    } else {
        aiResponseEl.style.display = 'none';
    }
    
    // 一定時間後にフェードアウト
    setTimeout(() => {
        messageContainer.style.opacity = '0';
    }, 10000);
}

// 3Dテキストの作成
function createFloatingText(text) {
    // 古いテキストメッシュを削除
    textMeshes.forEach(mesh => scene.remove(mesh));
    textMeshes = [];
    
    // テキストが長すぎる場合は分割
    let lines = [];
    if (text.length > 50) {
        const words = text.split(' ');
        let currentLine = '';
        
        words.forEach(word => {
            if ((currentLine + word).length < 50) {
                currentLine += (currentLine ? ' ' : '') + word;
            } else {
                if (currentLine) lines.push(currentLine);
                currentLine = word;
            }
        });
        
        if (currentLine) lines.push(currentLine);
    } else {
        lines = [text];
    }
    
    // フォントローダー
    const loader = new FontLoader();
    
    // デフォルトのヘルベチカフォントを使用
    loader.load('https://threejs.org/examples/fonts/helvetiker_regular.typeface.json', function(font) {
        const material = new THREE.MeshBasicMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.8
        });
        
        lines.forEach((line, index) => {
            const geometry = new TextGeometry(line, {
                font: font,
                size: 0.2,
                height: 0.05,
                curveSegments: 12,
                bevelEnabled: false
            });
            
            geometry.computeBoundingBox();
            const centerOffset = -0.5 * (geometry.boundingBox.max.x - geometry.boundingBox.min.x);
            
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.x = centerOffset;
            mesh.position.y = -index * 0.3;
            mesh.position.z = -5;
            
            // ランダムな回転を追加
            mesh.rotation.x = Math.random() * 0.2 - 0.1;
            mesh.rotation.y = Math.random() * 0.2 - 0.1;
            
            scene.add(mesh);
            textMeshes.push(mesh);
        });
    });
}

// ウィンドウリサイズ処理
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    composer.setSize(window.innerWidth, window.innerHeight);
}

// WebSocket接続
function connectWebSocket() {
    socket = new WebSocket(serverUrl);
    
    socket.onopen = function() {
        console.log('WebSocket接続が確立されました');
        document.getElementById('connection-status').textContent = 'WebSocket: 接続済み';
    };
    
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log('WebSocketからデータを受信:', data);
        
        if (data.type === 'emotion_update') {
            // 感情データの更新
            updateEmotionState(data.emotion);
            
            // テキストデータがあれば表示
            if (data.text && data.text.text) {
                let userMessage = data.text.text;
                let aiResponse = data.response ? data.response.response : '';
                
                showMessage(userMessage, aiResponse);
            }
        }
    };
    
    socket.onclose = function() {
        console.log('WebSocket接続が閉じられました');
        document.getElementById('connection-status').textContent = 'WebSocket: 切断';
        
        // 一定時間後に再接続
        setTimeout(connectWebSocket, 5000);
    };
    
    socket.onerror = function(error) {
        console.error('WebSocketエラー:', error);
        document.getElementById('connection-status').textContent = 'WebSocket: エラー';
    };
}

// デバッグパネルの初期化
function initDebugPanel() {
    const debugToggle = document.getElementById('debug-toggle');
    const debugPanel = document.getElementById('debug-panel');
    const debugApply = document.getElementById('debug-apply');
    
    // バレンス（感情価）スライダー
    const valenceSlider = document.getElementById('debug-valence');
    const valenceValue = document.getElementById('debug-valence-value');
    
    valenceSlider.addEventListener('input', function() {
        valenceValue.textContent = this.value;
    });
    
    // 活性度スライダー
    const activationSlider = document.getElementById('debug-activation');
    const activationValue = document.getElementById('debug-activation-value');
    
    activationSlider.addEventListener('input', function() {
        activationValue.textContent = this.value;
    });
    
    // デバッグパネルの表示/非表示
    debugToggle.addEventListener('click', function() {
        if (debugPanel.style.display === 'none' || !debugPanel.style.display) {
            debugPanel.style.display = 'block';
            debugToggle.style.display = 'none';
            isDebugMode = true;
        } else {
            debugPanel.style.display = 'none';
            isDebugMode = false;
        }
    });
    
    // デバッグ値の適用
    debugApply.addEventListener('click', function() {
        const emotionSelect = document.getElementById('debug-emotion');
        const valence = parseFloat(valenceSlider.value);
        const activation = parseFloat(activationSlider.value);
        const message = document.getElementById('debug-message').value;
        const response = document.getElementById('debug-response').value;
        
        // 感情データの更新
        updateEmotionState({
            primary_emotion: emotionSelect.value,
            valence: valence,
            activation: activation
        });
        
        // メッセージ表示
        if (message || response) {
            showMessage(message, response);
        }
    });
}

// アニメーションループ
function animate() {
    requestAnimationFrame(animate);
    
    // 現在の時間
    const time = Date.now() / 1000;
    
    // コントロール更新
    controls.update();
    
    // パーティクルアニメーション
    if (particleSystem) {
        // 時間の更新
        particleSystem.material.uniforms.time.value = time;
        
        // 色の徐々な変化
        if (particleSystem.userData.targetColor) {
            const targetColor = particleSystem.userData.targetColor;
            const intensity = particleSystem.userData.intensity || 1.0;
            
            // 経過時間に基づく補間係数（0〜1）
            const elapsed = time - lastUpdateTime;
            const t = Math.min(elapsed / emotionTransitionTime, 1.0);
            
            // パーティクルの色を徐々に変化
            const colors = particleSystem.geometry.attributes.color;
            const count = colors.count;
            
            for (let i = 0; i < count; i++) {
                const i3 = i * 3;
                
                // 現在の色
                const currentR = colors.array[i3];
                const currentG = colors.array[i3 + 1];
                const currentB = colors.array[i3 + 2];
                
                // 目標色への補間
                colors.array[i3] = currentR + (targetColor.r - currentR) * t;
                colors.array[i3 + 1] = currentG + (targetColor.g - currentG) * t;
                colors.array[i3 + 2] = currentB + (targetColor.b - currentB) * t;
            }
            
            colors.needsUpdate = true;
            
            // パーティクルのサイズアニメーション
            const sizes = particleSystem.geometry.attributes.size;
            
            for (let i = 0; i < sizes.count; i++) {
                // 活性度に基づくサイズの変動
                const pulseFactor = 1.0 + (currentEmotionData ? Math.abs(currentEmotionData.activation) * 0.5 : 0);
                const randomOffset = Math.sin(time + i * 0.1) * 0.2;
                
                // ベースサイズ * 強度 * 脈動 + ランダム変動
                sizes.array[i] = (Math.random() * 0.05 + 0.05) * intensity * pulseFactor + randomOffset * pulseFactor;
            }
            
            sizes.needsUpdate = true;
        }
    }
    
    // 3Dテキストのアニメーション
    textMeshes.forEach(mesh => {
        mesh.rotation.x += 0.001;
        mesh.rotation.y += 0.001;
        
        // 徐々に透明化
        if (mesh.material.opacity > 0) {
            mesh.material.opacity -= 0.001;
        }
    });
    
    // ポストプロセッシングを使用してレンダリング
    composer.render();
}

// ページロード時に初期化
window.addEventListener('load', init);
