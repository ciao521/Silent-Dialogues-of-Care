// ビジュアルシステムの更新
function updateVisualSystems(visualParams) {
    if (!visualParams) return;
    
    // 色情報の取得
    const colorInfo = emotionColors[currentEmotionData.primary_emotion] || emotionColors.neutral;
    const targetColor = colorInfo.color;
    
    // 感情の次元（感情価と活性度）に基づく色の調整
    const valence = currentEmotionData.valence; // -1.0〜1.0
    const activation = currentEmotionData.activation; // -1.0〜1.0
    
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
    
    // パーティクルシステムの更新
    if (enhancedParticles) {
        enhancedParticles.setColor(adjustedColor);
        enhancedParticles.updateParameters({
            particleSize: visualParams.particleSize,
            particleSpeed: visualParams.particleSpeed,
            waveIntensity: visualParams.waveIntensity,
            turbulence: visualParams.turbulence,
            particleShape: visualParams.particleShape,
            harmonyFactor: visualParams.harmonyFactor,
            expansionRate: visualParams.expansionRate
        });
    }
    
    // テキストシステムの更新
    if (enhancedText) {
        enhancedText.updateParameters({
            textComplexity: visualParams.textComplexity,
            textRhythm: visualParams.textRhythm,
            textEmphasis: visualParams.textEmphasis,
            textGeometry: visualParams.textGeometry,
            textAnimation: visualParams.textAnimation,
            textDensity: visualParams.textDensity
        });
    }
    
    // ポストプロセッシングの調整
    const bloomPass = composer.passes[1];
    bloomPass.strength = 0.8 + Math.abs(activation) * 0.7;
    bloomPass.radius = 0.3 + Math.abs(valence) * 0.4;
    
    if (composer.passes[2] && composer.passes[2].uniforms && composer.passes[2].uniforms.aberration) {
        const chromaticAberrationPass = composer.passes[2];
        chromaticAberrationPass.uniforms.aberration.value = 0.01 + Math.abs(activation) * 0.02;
    }
}
