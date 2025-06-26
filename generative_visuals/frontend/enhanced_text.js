/**
 * Silent Dialogues of Care - 境界なき対話
 * 拡張3Dテキストシステム
 */

import * as THREE from 'three';
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';

// 3Dテキストシステムのクラス
export class EnhancedTextSystem {
    constructor(scene, params = {}) {
        this.scene = scene;
        this.textMeshes = [];
        this.textParams = {
            textComplexity: params.textComplexity || 0.5,
            textRhythm: params.textRhythm || 0.5,
            textEmphasis: params.textEmphasis || 0.5,
            textGeometry: params.textGeometry || 'float',
            textAnimation: params.textAnimation || 'fade',
            textDensity: params.textDensity || 1.0
        };
        
        // フォントのキャッシュ
        this.fontCache = null;
        
        // フォントの事前ロード
        this.loadFont();
    }
    
    // フォントのロード
    async loadFont() {
        if (this.fontCache) return this.fontCache;
        
        const loader = new FontLoader();
        
        return new Promise((resolve, reject) => {
            // デフォルトのヘルベチカフォントを使用
            loader.load('https://threejs.org/examples/fonts/helvetiker_regular.typeface.json', font => {
                this.fontCache = font;
                resolve(font);
            }, undefined, reject);
        });
    }
    
    // テキストの作成
    async createText(text, position = { x: 0, y: 0, z: -5 }, color = 0xffffff) {
        if (!text) return;
        
        // 古いテキストメッシュを削除
        this.clearText();
        
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
        
        // フォントが読み込まれるまで待機
        const font = await this.loadFont();
        
        // テキストの幾何学的スタイルを決定
        const textStyle = this._getTextStyle(this.textParams.textGeometry);
        
        // テキスト生成
        lines.forEach((line, index) => {
            const geometry = new TextGeometry(line, {
                font: font,
                size: 0.2 * (1 + this.textParams.textEmphasis * 0.5),
                height: 0.05 * (1 + this.textParams.textEmphasis),
                curveSegments: 12,
                bevelEnabled: textStyle.bevelEnabled,
                bevelThickness: textStyle.bevelThickness,
                bevelSize: textStyle.bevelSize,
                bevelOffset: textStyle.bevelOffset,
                bevelSegments: textStyle.bevelSegments
            });
            
            // テキストを中央揃え
            geometry.computeBoundingBox();
            const centerOffset = -0.5 * (geometry.boundingBox.max.x - geometry.boundingBox.min.x);
            
            // マテリアル作成
            const material = this._createTextMaterial(color, this.textParams.textGeometry);
            
            // メッシュ作成
            const mesh = new THREE.Mesh(geometry, material);
            
            // 位置設定
            mesh.position.x = position.x + centerOffset;
            mesh.position.y = position.y - index * 0.3 * this.textParams.textDensity;
            mesh.position.z = position.z;
            
            // スタイルに基づく回転
            this._applyTextRotation(mesh, index);
            
            // アニメーション設定
            mesh.userData = {
                animation: this.textParams.textAnimation,
                creationTime: Date.now() / 1000,
                originalPosition: mesh.position.clone(),
                originalRotation: mesh.rotation.clone(),
                animationParams: this._getAnimationParams(index)
            };
            
            this.scene.add(mesh);
            this.textMeshes.push(mesh);
        });
    }
    
    // テキストスタイルの取得
    _getTextStyle(styleType) {
        switch (styleType) {
            case 'float':
                return {
                    bevelEnabled: true,
                    bevelThickness: 0.01,
                    bevelSize: 0.01,
                    bevelOffset: 0,
                    bevelSegments: 3
                };
                
            case 'bold':
                return {
                    bevelEnabled: true,
                    bevelThickness: 0.03,
                    bevelSize: 0.02,
                    bevelOffset: 0,
                    bevelSegments: 4
                };
                
            case 'serif':
                return {
                    bevelEnabled: true,
                    bevelThickness: 0.01,
                    bevelSize: 0.005,
                    bevelOffset: 0.001,
                    bevelSegments: 2
                };
                
            case 'curve':
                return {
                    bevelEnabled: true,
                    bevelThickness: 0.02,
                    bevelSize: 0.02,
                    bevelOffset: 0.001,
                    bevelSegments: 5
                };
                
            case 'flowing':
                return {
                    bevelEnabled: true,
                    bevelThickness: 0.01,
                    bevelSize: 0.02,
                    bevelOffset: 0.002,
                    bevelSegments: 8
                };
                
            default:
                return {
                    bevelEnabled: false,
                    bevelThickness: 0,
                    bevelSize: 0,
                    bevelOffset: 0,
                    bevelSegments: 0
                };
        }
    }
    
    // テキストマテリアルの作成
    _createTextMaterial(color, styleType) {
        let material;
        
        switch (styleType) {
            case 'float':
                material = new THREE.MeshBasicMaterial({
                    color: color,
                    transparent: true,
                    opacity: 0.8
                });
                break;
                
            case 'bold':
                material = new THREE.MeshStandardMaterial({
                    color: color,
                    metalness: 0.5,
                    roughness: 0.2,
                    transparent: true,
                    opacity: 0.9
                });
                break;
                
            case 'serif':
                material = new THREE.MeshPhongMaterial({
                    color: color,
                    specular: 0x111111,
                    shininess: 30,
                    transparent: true,
                    opacity: 0.85
                });
                break;
                
            case 'curve':
                material = new THREE.MeshLambertMaterial({
                    color: color,
                    emissive: new THREE.Color(color).multiplyScalar(0.2),
                    transparent: true,
                    opacity: 0.9
                });
                break;
                
            case 'flowing':
                material = new THREE.MeshPhysicalMaterial({
                    color: color,
                    clearcoat: 1.0,
                    clearcoatRoughness: 0.1,
                    metalness: 0.2,
                    roughness: 0.3,
                    transparent: true,
                    opacity: 0.8
                });
                break;
                
            default:
                material = new THREE.MeshBasicMaterial({
                    color: color,
                    transparent: true,
                    opacity: 0.8
                });
        }
        
        return material;
    }
    
    // テキスト回転の適用
    _applyTextRotation(mesh, index) {
        switch (this.textParams.textGeometry) {
            case 'float':
                mesh.rotation.x = Math.random() * 0.2 - 0.1;
                mesh.rotation.y = Math.random() * 0.2 - 0.1;
                break;
                
            case 'bold':
                // 安定感のある最小限の回転
                mesh.rotation.x = (Math.random() * 0.1 - 0.05) * this.textParams.textEmphasis;
                mesh.rotation.y = (Math.random() * 0.1 - 0.05) * this.textParams.textEmphasis;
                break;
                
            case 'curve':
                // 曲線に沿ったような回転
                mesh.rotation.z = (Math.random() * 0.2 - 0.1) * index * 0.1;
                mesh.rotation.y = (Math.random() * 0.2 - 0.1);
                break;
                
            case 'flowing':
                // 流れるような回転
                mesh.rotation.x = Math.sin(index * 0.5) * 0.2;
                mesh.rotation.y = Math.cos(index * 0.5) * 0.2;
                mesh.rotation.z = Math.sin(index * 0.3) * 0.1;
                break;
                
            default:
                mesh.rotation.x = Math.random() * 0.1 - 0.05;
                mesh.rotation.y = Math.random() * 0.1 - 0.05;
        }
    }
    
    // アニメーションパラメータの取得
    _getAnimationParams(index) {
        const params = {
            speed: 0.5 + Math.random() * 0.5,
            amplitude: 0.2 + Math.random() * 0.3,
            frequency: 0.5 + Math.random() * 1.0,
            delay: index * 0.2,
            duration: 10.0 + Math.random() * 5.0
        };
        
        switch (this.textParams.textAnimation) {
            case 'pulse':
                params.speed = 1.0 + Math.random() * 1.0;
                params.amplitude = 0.1 + Math.random() * 0.2;
                params.frequency = 1.0 + Math.random() * 2.0;
                break;
                
            case 'explode':
                params.speed = 2.0 + Math.random() * 1.0;
                params.amplitude = 0.5 + Math.random() * 0.5;
                params.frequency = 0.2 + Math.random() * 0.5;
                break;
                
            case 'echo':
                params.speed = 0.3 + Math.random() * 0.3;
                params.amplitude = 0.3 + Math.random() * 0.2;
                params.frequency = 0.3 + Math.random() * 0.3;
                params.delay = index * 0.5;
                break;
                
            case 'float':
                params.speed = 0.2 + Math.random() * 0.2;
                params.amplitude = 0.4 + Math.random() * 0.3;
                params.frequency = 0.2 + Math.random() * 0.2;
                break;
        }
        
        return params;
    }
    
    // テキストの削除
    clearText() {
        this.textMeshes.forEach(mesh => {
            if (mesh.geometry) mesh.geometry.dispose();
            if (mesh.material) {
                if (Array.isArray(mesh.material)) {
                    mesh.material.forEach(material => material.dispose());
                } else {
                    mesh.material.dispose();
                }
            }
            this.scene.remove(mesh);
        });
        
        this.textMeshes = [];
    }
    
    // パラメータの更新
    updateParameters(params) {
        if (!params) return;
        
        this.textParams.textComplexity = params.textComplexity || this.textParams.textComplexity;
        this.textParams.textRhythm = params.textRhythm || this.textParams.textRhythm;
        this.textParams.textEmphasis = params.textEmphasis || this.textParams.textEmphasis;
        this.textParams.textDensity = params.textDensity || this.textParams.textDensity;
        
        if (params.textGeometry) this.textParams.textGeometry = params.textGeometry;
        if (params.textAnimation) this.textParams.textAnimation = params.textAnimation;
    }
    
    // アニメーションの更新
    update(time) {
        if (!this.textMeshes.length) return;
        
        this.textMeshes.forEach((mesh, index) => {
            if (!mesh.userData) return;
            
            const elapsedTime = time - mesh.userData.creationTime;
            const animParams = mesh.userData.animationParams;
            const originalPos = mesh.userData.originalPosition;
            const originalRot = mesh.userData.originalRotation;
            
            // アニメーション終了チェック
            if (elapsedTime > animParams.duration) {
                // 徐々に透明化して消滅
                if (mesh.material.opacity > 0) {
                    mesh.material.opacity -= 0.01;
                }
                
                if (mesh.material.opacity <= 0) {
                    // 完全に透明になったらシーンから削除
                    this.scene.remove(mesh);
                    this.textMeshes.splice(index, 1);
                }
                
                return;
            }
            
            // 遅延時間の確認
            if (elapsedTime < animParams.delay) return;
            
            const t = elapsedTime - animParams.delay;
            
            // アニメーションタイプに基づく更新
            switch (mesh.userData.animation) {
                case 'fade':
                    // フェードイン・アウト
                    if (t < 1.0) {
                        mesh.material.opacity = Math.min(0.8, t);
                    } else if (t > animParams.duration - 2.0) {
                        mesh.material.opacity = Math.max(0, 0.8 - (t - (animParams.duration - 2.0)) / 2.0);
                    }
                    
                    // ゆっくりと回転
                    mesh.rotation.x = originalRot.x + Math.sin(t * 0.5) * 0.05;
                    mesh.rotation.y = originalRot.y + Math.cos(t * 0.4) * 0.05;
                    break;
                    
                case 'pulse':
                    // 脈動効果
                    const pulseScale = 1.0 + Math.sin(t * animParams.frequency) * 0.1 * animParams.amplitude;
                    mesh.scale.set(pulseScale, pulseScale, pulseScale);
                    
                    // 色の変化
                    if (mesh.material.color) {
                        const hue = (t * 0.1) % 1;
                        const brightness = 0.5 + Math.sin(t * 2) * 0.2;
                        mesh.material.color.setHSL(hue, 0.5, brightness);
                    }
                    break;
                    
                case 'explode':
                    // 爆発効果
                    if (t < 1.0) {
                        // 最初の動き
                        const startFactor = t * t * animParams.speed;
                        mesh.position.x = originalPos.x + (Math.random() - 0.5) * startFactor;
                        mesh.position.y = originalPos.y + (Math.random() - 0.5) * startFactor;
                        mesh.position.z = originalPos.z + (Math.random() - 0.5) * startFactor;
                        
                        // スケール
                        const scaleUp = 0.5 + t * 1.5;
                        mesh.scale.set(scaleUp, scaleUp, scaleUp);
                    } else {
                        // 徐々に元の位置に戻る
                        const returnFactor = Math.min(1.0, (t - 1.0) * 0.2);
                        mesh.position.lerp(originalPos, returnFactor);
                        
                        // スケールダウン
                        const scaleDown = Math.max(1.0, 2.0 - (t - 1.0) * 0.2);
                        mesh.scale.set(scaleDown, scaleDown, scaleDown);
                    }
                    
                    // 回転
                    mesh.rotation.x = originalRot.x + t * animParams.speed * 0.1;
                    mesh.rotation.y = originalRot.y + t * animParams.speed * 0.15;
                    break;
                    
                case 'echo':
                    // エコー効果（複数のテキストが連続して現れる感じ）
                    if (t < 2.0) {
                        // 初期フェードイン
                        mesh.material.opacity = Math.min(0.8, t / 2.0);
                    }
                    
                    // 波状の動き
                    const waveY = Math.sin(t * animParams.frequency) * animParams.amplitude;
                    const waveX = Math.cos(t * animParams.frequency * 0.7) * animParams.amplitude * 0.5;
                    
                    mesh.position.x = originalPos.x + waveX;
                    mesh.position.y = originalPos.y + waveY;
                    
                    // 回転
                    mesh.rotation.z = originalRot.z + Math.sin(t * 0.3) * 0.1;
                    break;
                    
                case 'float':
                    // 浮遊効果
                    const floatY = Math.sin(t * animParams.frequency) * animParams.amplitude;
                    const floatX = Math.cos(t * animParams.frequency * 0.6) * animParams.amplitude * 0.3;
                    const floatZ = Math.sin(t * animParams.frequency * 0.4) * animParams.amplitude * 0.2;
                    
                    mesh.position.x = originalPos.x + floatX;
                    mesh.position.y = originalPos.y + floatY;
                    mesh.position.z = originalPos.z + floatZ;
                    
                    // 緩やかな回転
                    mesh.rotation.x = originalRot.x + Math.sin(t * 0.2) * 0.1;
                    mesh.rotation.y = originalRot.y + Math.sin(t * 0.3) * 0.1;
                    break;
                    
                default:
                    // デフォルトは徐々に透明化
                    if (t > animParams.duration - 2.0) {
                        mesh.material.opacity = Math.max(0, 0.8 - (t - (animParams.duration - 2.0)) / 2.0);
                    }
            }
        });
    }
}
