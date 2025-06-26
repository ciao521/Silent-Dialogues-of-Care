/**
 * Silent Dialogues of Care - 境界なき対話
 * 拡張パーティクルシステム
 */

import * as THREE from 'three';

// 拡張パーティクルシステムのクラス
export class EnhancedParticleSystem {
    constructor(scene, params = {}) {
        this.scene = scene;
        this.particleCount = params.particleCount || 10000;
        this.particleSize = params.particleSize || 0.08;
        this.particleSpeed = params.particleSpeed || 0.5;
        this.waveIntensity = params.waveIntensity || 0.5;
        this.particleShape = params.particleShape || 'circle';
        this.turbulence = params.turbulence || 0.5;
        this.harmonyFactor = params.harmonyFactor || 0.5;
        this.expansionRate = params.expansionRate || 1.0;
        
        this.particleSystem = null;
        this.currentColor = new THREE.Color(0x888888);
        this.targetColor = new THREE.Color(0x888888);
        this.colorTransitionSpeed = 0.05;
        
        // パーティクルシステムの初期化
        this.init();
    }
    
    // パーティクルシステムの初期化
    init() {
        // 既存のパーティクルシステムを削除
        if (this.particleSystem) {
            this.scene.remove(this.particleSystem);
        }
        
        // パーティクルのジオメトリ作成
        const geometry = new THREE.BufferGeometry();
        
        // 位置の配列
        const positions = new Float32Array(this.particleCount * 3);
        
        // 色の配列
        const colors = new Float32Array(this.particleCount * 3);
        
        // サイズの配列
        const sizes = new Float32Array(this.particleCount);
        
        // 回転の配列
        const rotations = new Float32Array(this.particleCount);
        
        // 速度の配列（アニメーション用）
        const velocities = new Float32Array(this.particleCount * 3);
        
        // 生存時間の配列（アニメーション用）
        const lifetimes = new Float32Array(this.particleCount);
        
        // 各パーティクルの初期化
        for (let i = 0; i < this.particleCount; i++) {
            // 位置の初期化
            this._initParticlePosition(positions, i);
            
            // 色の初期化
            colors[i * 3] = this.currentColor.r;
            colors[i * 3 + 1] = this.currentColor.g;
            colors[i * 3 + 2] = this.currentColor.b;
            
            // サイズの初期化
            sizes[i] = Math.random() * this.particleSize + this.particleSize * 0.5;
            
            // 回転の初期化
            rotations[i] = Math.random() * Math.PI * 2;
            
            // 速度の初期化
            velocities[i * 3] = (Math.random() - 0.5) * this.particleSpeed;
            velocities[i * 3 + 1] = (Math.random() - 0.5) * this.particleSpeed;
            velocities[i * 3 + 2] = (Math.random() - 0.5) * this.particleSpeed;
            
            // 生存時間の初期化
            lifetimes[i] = Math.random();
        }
        
        // ジオメトリに属性を設定
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
        geometry.setAttribute('rotation', new THREE.BufferAttribute(rotations, 1));
        
        // ユーザーデータとして速度と生存時間を保存
        geometry.userData = {
            velocities,
            lifetimes
        };
        
        // パーティクルのテクスチャ
        const texture = this._createParticleTexture();
        
        // パーティクルのマテリアル
        const material = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                pointTexture: { value: texture },
                waveIntensity: { value: this.waveIntensity },
                turbulence: { value: this.turbulence }
            },
            vertexShader: `
                attribute float size;
                attribute float rotation;
                attribute vec3 color;
                
                uniform float time;
                uniform float waveIntensity;
                uniform float turbulence;
                
                varying vec3 vColor;
                varying float vRotation;
                
                // 乱数生成関数
                float random(vec2 st) {
                    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
                }
                
                void main() {
                    vColor = color;
                    vRotation = rotation + time * 0.5;
                    
                    // 位置のアニメーション計算
                    vec3 pos = position;
                    
                    // 波動効果
                    float wave = sin(time * 0.5 + position.x * 0.1 + position.y * 0.1 + position.z * 0.1);
                    pos += normal * wave * waveIntensity;
                    
                    // 乱流効果
                    float noise = random(position.xy + time * 0.1);
                    pos += vec3(
                        sin(time * 0.7 + position.y * 0.2) * turbulence * noise,
                        cos(time * 0.6 + position.z * 0.2) * turbulence * noise,
                        sin(time * 0.8 + position.x * 0.2) * turbulence * noise
                    );
                    
                    // カメラに対する位置の計算
                    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
                    
                    // 画面上のサイズ計算
                    gl_PointSize = size * (300.0 / length(mvPosition.xyz));
                    gl_Position = projectionMatrix * mvPosition;
                }
            `,
            fragmentShader: `
                uniform sampler2D pointTexture;
                uniform float time;
                
                varying vec3 vColor;
                varying float vRotation;
                
                void main() {
                    // 回転の適用
                    float c = cos(vRotation);
                    float s = sin(vRotation);
                    vec2 rotatedUV = vec2(
                        c * (gl_PointCoord.x - 0.5) + s * (gl_PointCoord.y - 0.5) + 0.5,
                        c * (gl_PointCoord.y - 0.5) - s * (gl_PointCoord.x - 0.5) + 0.5
                    );
                    
                    // テクスチャのサンプリング
                    vec4 texColor = texture2D(pointTexture, rotatedUV);
                    
                    // 最終的な色の計算
                    gl_FragColor = vec4(vColor, 1.0) * texColor;
                    
                    // アルファ値が小さすぎる場合は破棄
                    if (gl_FragColor.a < 0.1) discard;
                }
            `,
            blending: THREE.AdditiveBlending,
            depthTest: false,
            transparent: true,
            vertexColors: true
        });
        
        // パーティクルシステムの作成
        this.particleSystem = new THREE.Points(geometry, material);
        this.scene.add(this.particleSystem);
    }
    
    // パーティクル位置の初期化
    _initParticlePosition(positions, index) {
        const i3 = index * 3;
        const radius = 10 * Math.pow(Math.random(), 1/3) * this.expansionRate;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        
        // 調和度に応じたパターン生成
        if (Math.random() < this.harmonyFactor) {
            // 規則的なパターン
            const harmonicPattern = Math.floor(Math.random() * 5);
            
            switch (harmonicPattern) {
                case 0: // 螺旋パターン
                    positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
                    positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
                    positions[i3 + 2] = radius * Math.cos(phi) + radius * 0.1 * theta;
                    break;
                    
                case 1: // 球状層
                    const layerRadius = Math.floor(Math.random() * 5) * 2 + 4;
                    positions[i3] = layerRadius * Math.sin(phi) * Math.cos(theta);
                    positions[i3 + 1] = layerRadius * Math.sin(phi) * Math.sin(theta);
                    positions[i3 + 2] = layerRadius * Math.cos(phi);
                    break;
                    
                case 2: // トーラス（ドーナツ形）
                    const R = 8; // 大円の半径
                    const r = 2; // 小円の半径
                    const u = Math.random() * Math.PI * 2;
                    const v = Math.random() * Math.PI * 2;
                    positions[i3] = (R + r * Math.cos(v)) * Math.cos(u);
                    positions[i3 + 1] = (R + r * Math.cos(v)) * Math.sin(u);
                    positions[i3 + 2] = r * Math.sin(v);
                    break;
                    
                case 3: // 放射状
                    const angle = Math.random() * Math.PI * 2;
                    const distance = Math.random() * 10 * this.expansionRate;
                    positions[i3] = Math.cos(angle) * distance;
                    positions[i3 + 1] = Math.sin(angle) * distance;
                    positions[i3 + 2] = (Math.random() - 0.5) * 2;
                    break;
                    
                case 4: // 立方体格子
                    const gridSize = 4;
                    const cellSize = 20 / gridSize;
                    positions[i3] = (Math.floor(Math.random() * gridSize) - gridSize/2) * cellSize;
                    positions[i3 + 1] = (Math.floor(Math.random() * gridSize) - gridSize/2) * cellSize;
                    positions[i3 + 2] = (Math.floor(Math.random() * gridSize) - gridSize/2) * cellSize;
                    // ランダムなずれを追加
                    positions[i3] += (Math.random() - 0.5) * cellSize * 0.5;
                    positions[i3 + 1] += (Math.random() - 0.5) * cellSize * 0.5;
                    positions[i3 + 2] += (Math.random() - 0.5) * cellSize * 0.5;
                    break;
            }
        } else {
            // ランダムな球体状の配置
            positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i3 + 2] = radius * Math.cos(phi);
        }
    }
    
    // パーティクルのテクスチャを作成
    _createParticleTexture() {
        const canvas = document.createElement('canvas');
        canvas.width = 128;
        canvas.height = 128;
        const context = canvas.getContext('2d');
        
        context.clearRect(0, 0, canvas.width, canvas.height);
        
        // パーティクル形状の描画
        switch (this.particleShape) {
            case 'circle':
                this._drawCircle(context, canvas.width, canvas.height);
                break;
                
            case 'star':
                this._drawStar(context, canvas.width, canvas.height);
                break;
                
            case 'tear':
                this._drawTear(context, canvas.width, canvas.height);
                break;
                
            case 'spark':
                this._drawSpark(context, canvas.width, canvas.height);
                break;
                
            case 'dust':
                this._drawDust(context, canvas.width, canvas.height);
                break;
                
            case 'burst':
                this._drawBurst(context, canvas.width, canvas.height);
                break;
                
            case 'pulse':
                this._drawPulse(context, canvas.width, canvas.height);
                break;
                
            default:
                this._drawCircle(context, canvas.width, canvas.height);
        }
        
        // テクスチャの作成
        const texture = new THREE.Texture(canvas);
        texture.needsUpdate = true;
        return texture;
    }
    
    // 円形のパーティクル描画
    _drawCircle(context, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = width / 2 * 0.8;
        
        // グラデーション作成
        const gradient = context.createRadialGradient(
            centerX, centerY, 0,
            centerX, centerY, radius
        );
        gradient.addColorStop(0, 'rgba(255, 255, 255, 1.0)');
        gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.5)');
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0.0)');
        
        // 円の描画
        context.beginPath();
        context.arc(centerX, centerY, radius, 0, Math.PI * 2);
        context.fillStyle = gradient;
        context.fill();
    }
    
    // 星型のパーティクル描画
    _drawStar(context, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const outerRadius = width / 2 * 0.8;
        const innerRadius = outerRadius * 0.4;
        const spikes = 5;
        
        context.beginPath();
        let rot = Math.PI / 2 * 3;
        const step = Math.PI / spikes;
        
        context.moveTo(centerX, centerY - outerRadius);
        
        for (let i = 0; i < spikes; i++) {
            context.lineTo(
                centerX + Math.cos(rot) * outerRadius,
                centerY + Math.sin(rot) * outerRadius
            );
            rot += step;
            
            context.lineTo(
                centerX + Math.cos(rot) * innerRadius,
                centerY + Math.sin(rot) * innerRadius
            );
            rot += step;
        }
        
        context.lineTo(centerX, centerY - outerRadius);
        context.closePath();
        
        // グラデーション作成
        const gradient = context.createRadialGradient(
            centerX, centerY, innerRadius,
            centerX, centerY, outerRadius
        );
        gradient.addColorStop(0, 'rgba(255, 255, 255, 1.0)');
        gradient.addColorStop(0.7, 'rgba(255, 255, 255, 0.5)');
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0.0)');
        
        context.fillStyle = gradient;
        context.fill();
    }
    
    // 涙型のパーティクル描画
    _drawTear(context, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = width / 2 * 0.7;
        
        context.beginPath();
        context.moveTo(centerX, centerY - radius);
        
        // 涙の形を描画
        context.bezierCurveTo(
            centerX + radius, centerY - radius / 2,
            centerX + radius, centerY + radius / 2,
            centerX, centerY + radius
        );
        
        context.bezierCurveTo(
            centerX - radius, centerY + radius / 2,
            centerX - radius, centerY - radius / 2,
            centerX, centerY - radius
        );
        
        // グラデーション作成
        const gradient = context.createRadialGradient(
            centerX, centerY - radius / 4, radius / 4,
            centerX, centerY, radius
        );
        gradient.addColorStop(0, 'rgba(255, 255, 255, 1.0)');
        gradient.addColorStop(0.6, 'rgba(255, 255, 255, 0.5)');
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0.0)');
        
        context.fillStyle = gradient;
        context.fill();
    }
    
    // 火花型のパーティクル描画
    _drawSpark(context, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = width / 2 * 0.8;
        const spikes = 8;
        
        context.beginPath();
        
        // 不規則な形状を作成
        for (let i = 0; i < spikes * 2; i++) {
            const angle = (i * Math.PI * 2) / (spikes * 2);
            const spikeLength = i % 2 === 0 ? radius : radius * 0.4;
            
            const x = centerX + Math.cos(angle) * spikeLength;
            const y = centerY + Math.sin(angle) * spikeLength;
            
            if (i === 0) {
                context.moveTo(x, y);
            } else {
                context.lineTo(x, y);
            }
        }
        
        context.closePath();
        
        // グラデーション作成
        const gradient = context.createRadialGradient(
            centerX, centerY, 0,
            centerX, centerY, radius
        );
        gradient.addColorStop(0, 'rgba(255, 255, 255, 1.0)');
        gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.7)');
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0.0)');
        
        context.fillStyle = gradient;
        context.fill();
    }
    
    // 粒子型のパーティクル描画
    _drawDust(context, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = width / 2 * 0.8;
        
        // 背景の透明な円
        context.beginPath();
        context.arc(centerX, centerY, radius, 0, Math.PI * 2);
        context.fillStyle = 'rgba(255, 255, 255, 0.2)';
        context.fill();
        
        // ランダムな小さな点を描画
        const dots = 30;
        for (let i = 0; i < dots; i++) {
            const angle = Math.random() * Math.PI * 2;
            const distance = Math.random() * radius;
            
            const x = centerX + Math.cos(angle) * distance;
            const y = centerY + Math.sin(angle) * distance;
            const dotSize = Math.random() * 4 + 1;
            
            context.beginPath();
            context.arc(x, y, dotSize, 0, Math.PI * 2);
            context.fillStyle = `rgba(255, 255, 255, ${Math.random() * 0.5 + 0.5})`;
            context.fill();
        }
    }
    
    // 爆発型のパーティクル描画
    _drawBurst(context, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const outerRadius = width / 2 * 0.8;
        const innerRadius = outerRadius * 0.3;
        
        // 中心の円
        context.beginPath();
        context.arc(centerX, centerY, innerRadius, 0, Math.PI * 2);
        context.fillStyle = 'rgba(255, 255, 255, 1.0)';
        context.fill();
        
        // 放射状の線
        const rays = 16;
        for (let i = 0; i < rays; i++) {
            const angle = (i * Math.PI * 2) / rays;
            const rayLength = outerRadius * (0.7 + Math.random() * 0.3);
            
            context.beginPath();
            context.moveTo(centerX, centerY);
            context.lineTo(
                centerX + Math.cos(angle) * rayLength,
                centerY + Math.sin(angle) * rayLength
            );
            
            context.lineWidth = 2 + Math.random() * 3;
            context.strokeStyle = 'rgba(255, 255, 255, 0.7)';
            context.stroke();
        }
        
        // 外側のグロー
        const gradient = context.createRadialGradient(
            centerX, centerY, innerRadius,
            centerX, centerY, outerRadius
        );
        gradient.addColorStop(0, 'rgba(255, 255, 255, 0.5)');
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0.0)');
        
        context.beginPath();
        context.arc(centerX, centerY, outerRadius, 0, Math.PI * 2);
        context.fillStyle = gradient;
        context.fill();
    }
    
    // 脈動型のパーティクル描画
    _drawPulse(context, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = width / 2 * 0.8;
        
        // 中心の円
        context.beginPath();
        context.arc(centerX, centerY, radius * 0.3, 0, Math.PI * 2);
        context.fillStyle = 'rgba(255, 255, 255, 1.0)';
        context.fill();
        
        // 複数の同心円
        const rings = 3;
        for (let i = 1; i <= rings; i++) {
            const ringRadius = radius * (0.4 + i * 0.2);
            
            context.beginPath();
            context.arc(centerX, centerY, ringRadius, 0, Math.PI * 2);
            context.strokeStyle = `rgba(255, 255, 255, ${1 - i * 0.2})`;
            context.lineWidth = 2;
            context.stroke();
        }
        
        // 外側のグロー
        const gradient = context.createRadialGradient(
            centerX, centerY, radius * 0.3,
            centerX, centerY, radius
        );
        gradient.addColorStop(0, 'rgba(255, 255, 255, 0.5)');
        gradient.addColorStop(0.7, 'rgba(255, 255, 255, 0.2)');
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0.0)');
        
        context.beginPath();
        context.arc(centerX, centerY, radius, 0, Math.PI * 2);
        context.fillStyle = gradient;
        context.fill();
    }
    
    // パーティクルの色を設定
    setColor(color) {
        this.targetColor.copy(color);
    }
    
    // パーティクルシステムのパラメータを更新
    updateParameters(params) {
        if (!params) return;
        
        // パラメータの更新
        this.particleSize = params.particleSize || this.particleSize;
        this.particleSpeed = params.particleSpeed || this.particleSpeed;
        this.waveIntensity = params.waveIntensity || this.waveIntensity;
        this.turbulence = params.turbulence || this.turbulence;
        
        // シェーダーのユニフォームを更新
        if (this.particleSystem && this.particleSystem.material) {
            this.particleSystem.material.uniforms.waveIntensity.value = this.waveIntensity;
            this.particleSystem.material.uniforms.turbulence.value = this.turbulence;
        }
        
        // パーティクルの形状が変更された場合、テクスチャを更新
        if (params.particleShape && params.particleShape !== this.particleShape) {
            this.particleShape = params.particleShape;
            
            if (this.particleSystem && this.particleSystem.material) {
                const texture = this._createParticleTexture();
                this.particleSystem.material.uniforms.pointTexture.value = texture;
            }
        }
    }
    
    // アニメーションの更新
    update(time) {
        if (!this.particleSystem) return;
        
        // 時間の更新
        this.particleSystem.material.uniforms.time.value = time;
        
        // 色の遷移
        const colors = this.particleSystem.geometry.attributes.color;
        let needsUpdate = false;
        
        for (let i = 0; i < this.particleCount; i++) {
            const i3 = i * 3;
            
            // 現在の色
            const currentR = colors.array[i3];
            const currentG = colors.array[i3 + 1];
            const currentB = colors.array[i3 + 2];
            
            // 目標色への補間
            colors.array[i3] = currentR + (this.targetColor.r - currentR) * this.colorTransitionSpeed;
            colors.array[i3 + 1] = currentG + (this.targetColor.g - currentG) * this.colorTransitionSpeed;
            colors.array[i3 + 2] = currentB + (this.targetColor.b - currentB) * this.colorTransitionSpeed;
            
            needsUpdate = true;
        }
        
        if (needsUpdate) {
            colors.needsUpdate = true;
        }
        
        // パーティクルの位置と回転の更新
        const positions = this.particleSystem.geometry.attributes.position;
        const rotations = this.particleSystem.geometry.attributes.rotation;
        const velocities = this.particleSystem.geometry.userData.velocities;
        const lifetimes = this.particleSystem.geometry.userData.lifetimes;
        
        for (let i = 0; i < this.particleCount; i++) {
            const i3 = i * 3;
            
            // 生存時間の更新
            lifetimes[i] += 0.005;
            if (lifetimes[i] > 1.0) {
                // パーティクルのリセット
                lifetimes[i] = 0.0;
                this._initParticlePosition(positions.array, i);
                
                // 速度のリセット
                velocities[i3] = (Math.random() - 0.5) * this.particleSpeed;
                velocities[i3 + 1] = (Math.random() - 0.5) * this.particleSpeed;
                velocities[i3 + 2] = (Math.random() - 0.5) * this.particleSpeed;
            } else {
                // 位置の更新
                positions.array[i3] += velocities[i3];
                positions.array[i3 + 1] += velocities[i3 + 1];
                positions.array[i3 + 2] += velocities[i3 + 2];
                
                // 速度の減衰
                velocities[i3] *= 0.99;
                velocities[i3 + 1] *= 0.99;
                velocities[i3 + 2] *= 0.99;
            }
            
            // 回転の更新
            rotations.array[i] += 0.01;
        }
        
        positions.needsUpdate = true;
        rotations.needsUpdate = true;
    }
}
