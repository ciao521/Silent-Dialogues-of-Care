/**
 * Silent Dialogues of Care - 境界なき対話
 * WebGPUレンダラーモジュール
 */

import * as THREE from 'three';
import { WebGPURenderer } from 'three/addons/renderers/webgpu/WebGPURenderer.js';
import { WebGPUTextureUtils } from 'three/addons/renderers/webgpu/WebGPUTextureUtils.js';

// WebGPUのサポート状況を確認する関数
export async function isWebGPUSupported() {
    if (!navigator.gpu) {
        console.log('WebGPUはこのブラウザでサポートされていません');
        return false;
    }
    
    try {
        const adapter = await navigator.gpu.requestAdapter();
        if (!adapter) {
            console.log('WebGPUアダプターを取得できません');
            return false;
        }
        
        const device = await adapter.requestDevice();
        if (!device) {
            console.log('WebGPUデバイスを取得できません');
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('WebGPU初期化エラー:', error);
        return false;
    }
}

// WebGPUレンダラーを作成する関数
export async function createRenderer(container) {
    let renderer;
    
    // WebGPUサポートの確認
    const isWebGPUAvailable = await isWebGPUSupported();
    
    if (isWebGPUAvailable) {
        try {
            // WebGPUレンダラーの作成
            renderer = new WebGPURenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            
            console.log('WebGPUレンダラーを初期化しました');
        } catch (error) {
            console.error('WebGPUレンダラー初期化エラー:', error);
            // フォールバック: WebGLレンダラーを使用
            renderer = createWebGLRenderer();
        }
    } else {
        // WebGPUがサポートされていない場合はWebGLを使用
        renderer = createWebGLRenderer();
    }
    
    // コンテナに追加
    container.appendChild(renderer.domElement);
    
    return renderer;
}

// フォールバック用のWebGLレンダラーを作成
function createWebGLRenderer() {
    console.log('WebGLレンダラーにフォールバックします');
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    return renderer;
}

// WebGPUに最適化されたエフェクトコンポーザーの作成
export function createOptimizedComposer(renderer, scene, camera) {
    // WebGPUレンダラーかどうか確認
    const isWebGPU = renderer.constructor.name === 'WebGPURenderer';
    
    // 以下のコードはThree.jsの標準的なエフェクトコンポーザーを使用
    // WebGPUに最適化された特殊なエフェクトを追加する場合は、ここを拡張
    
    // 標準のエフェクトコンポーザーの作成（WebGLと同じ）
    const composer = new EffectComposer(renderer);
    
    // レンダーパスの追加
    const renderPass = new RenderPass(scene, camera);
    composer.addPass(renderPass);
    
    // WebGPU用の最適化（将来的な拡張用）
    if (isWebGPU) {
        // WebGPU固有の最適化をここに追加
    }
    
    return composer;
}

// カスタムシェーダーパスの最適化
export function createOptimizedShaderPass(shader) {
    // WebGPU用にシェーダーを最適化（将来的な拡張用）
    return new ShaderPass(shader);
}

// WebGPUに対応したテクスチャローダー
export async function loadTextureWebGPU(url, renderer) {
    return new Promise((resolve, reject) => {
        const textureLoader = new THREE.TextureLoader();
        textureLoader.load(url, (texture) => {
            // WebGPUレンダラーの場合、テクスチャの特別な処理が必要かもしれない
            if (renderer.constructor.name === 'WebGPURenderer') {
                // 将来的なWebGPU固有の処理を追加
            }
            resolve(texture);
        }, undefined, reject);
    });
}
