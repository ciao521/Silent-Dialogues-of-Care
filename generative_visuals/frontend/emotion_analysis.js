/**
 * Silent Dialogues of Care - 境界なき対話
 * 感情と言語分析モジュール
 */

// 感情強度に基づくビジュアルパラメータの計算
export function calculateEmotionParameters(emotionData) {
    const { primary_emotion, valence, activation } = emotionData;
    
    // 基本パラメータ
    const params = {
        particleCount: 10000,         // パーティクル数の基本値
        particleSize: 0.08,           // パーティクルサイズの基本値
        particleSpeed: 0.5,           // パーティクル速度の基本値
        waveIntensity: 0.5,           // 波動の強度
        bloomStrength: 0.8,           // ブルームエフェクトの強度
        chromaticAberration: 0.01,    // 色収差の強度
        turbulence: 0.5,              // 乱流の強度
        harmonyFactor: 0.5,           // 調和度（パターンの規則性）
        expansionRate: 1.0,           // 拡張率（空間の広がり）
        colorVariation: 0.2,          // 色のバリエーション
        particleShape: 'circle'       // パーティクルの形状
    };
    
    // 活性度（-1.0〜1.0）に基づく調整
    const activationFactor = 1.0 + activation * 0.5;
    params.particleSpeed *= activationFactor;
    params.waveIntensity *= activationFactor;
    params.turbulence = Math.max(0.1, params.turbulence * activationFactor);
    params.bloomStrength = Math.max(0.5, params.bloomStrength * activationFactor);
    params.chromaticAberration = Math.max(0.005, params.chromaticAberration * activationFactor);
    
    // 感情価（-1.0〜1.0）に基づく調整
    const valenceFactor = 1.0 + valence * 0.3;
    params.harmonyFactor = Math.max(0.2, params.harmonyFactor * valenceFactor);
    params.colorVariation = Math.max(0.1, params.colorVariation * (valence >= 0 ? 1.5 : 0.7));
    
    // 感情タイプ別の特殊調整
    switch (primary_emotion) {
        case 'happy':
        case 'amusement':
        case 'contentment':
        case 'triumph':
            params.expansionRate = 1.2;
            params.particleShape = 'star';
            break;
            
        case 'sad':
        case 'disappointment':
        case 'tiredness':
            params.particleSpeed *= 0.7;
            params.expansionRate = 0.8;
            params.particleShape = 'tear';
            break;
            
        case 'anger':
        case 'disgust':
        case 'contempt':
            params.turbulence *= 1.5;
            params.particleShape = 'spark';
            break;
            
        case 'fear':
        case 'pain':
            params.chromaticAberration *= 1.8;
            params.turbulence *= 1.2;
            params.particleShape = 'dust';
            break;
            
        case 'surprise':
        case 'awe':
            params.bloomStrength *= 1.5;
            params.expansionRate = 1.4;
            params.particleShape = 'burst';
            break;
            
        case 'interest':
        case 'desire':
            params.particleCount = Math.floor(params.particleCount * 1.2);
            params.harmonyFactor *= 1.3;
            params.particleShape = 'pulse';
            break;
    }
    
    return params;
}

// テキストの感情的特徴を分析
export function analyzeText(text) {
    if (!text) return null;
    
    // 単語数のカウント
    const wordCount = text.split(/\s+/).filter(word => word.length > 0).length;
    
    // 文の長さ
    const sentenceCount = text.split(/[.!?。！？]+/).filter(s => s.length > 0).length;
    
    // キーワード抽出 (簡易版)
    const keywords = extractKeywords(text);
    
    // 文体の分析 (簡易版)
    const style = analyzeStyle(text);
    
    return {
        wordCount,
        sentenceCount,
        keywords,
        style,
        length: text.length
    };
}

// キーワード抽出 (簡易版)
function extractKeywords(text) {
    // 一般的な日本語/英語のストップワード
    const stopWords = new Set([
        'は', 'が', 'の', 'に', 'を', 'と', 'で', 'た', 'し', 'て', 'ない', 'ある',
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'have', 'has', 'had',
        'this', 'that', 'these', 'those', 'and', 'or', 'but', 'if', 'then', 'else'
    ]);
    
    // 単語分割 (簡易版)
    const words = text.toLowerCase()
        .replace(/[.,!?;:()\"\']/g, ' ')
        .split(/\s+/)
        .filter(word => word.length > 1 && !stopWords.has(word));
    
    // 単語の出現回数カウント
    const wordFreq = {};
    words.forEach(word => {
        wordFreq[word] = (wordFreq[word] || 0) + 1;
    });
    
    // 出現頻度で並べ替えて上位を返す
    return Object.entries(wordFreq)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(entry => entry[0]);
}

// 文体の分析 (簡易版)
function analyzeStyle(text) {
    const style = {
        interrogative: false,   // 疑問文
        exclamatory: false,     // 感嘆文
        imperative: false,      // 命令文
        repetitive: false,      // 繰り返し
        formal: false,          // 丁寧/フォーマル
        poetic: false           // 詩的
    };
    
    // 疑問文の検出
    if (text.match(/[?？]+/) || text.match(/か[\s]*$/)) {
        style.interrogative = true;
    }
    
    // 感嘆文の検出
    if (text.match(/[!！]+/) || text.match(/わ[\s]*$/) || text.match(/よ[\s]*$/)) {
        style.exclamatory = true;
    }
    
    // 命令文の検出
    if (text.match(/[てろよ][\s]*$/) || text.match(/please|kindly|must/i)) {
        style.imperative = true;
    }
    
    // 繰り返しの検出 (同じ単語が複数回出現)
    const words = text.toLowerCase().split(/\s+/);
    const uniqueWords = new Set(words);
    if (words.length > 3 && uniqueWords.size < words.length * 0.7) {
        style.repetitive = true;
    }
    
    // フォーマル/丁寧な言葉遣いの検出
    if (text.match(/です|ます|ございます/) || 
        text.match(/would you|could you|may I|shall we/i)) {
        style.formal = true;
    }
    
    // 詩的表現の検出 (簡易版)
    if (text.match(/[、。,.]{2,}/) || text.match(/[　 ]{3,}/)) {
        style.poetic = true;
    }
    
    return style;
}

// テキスト分析に基づくビジュアルパラメータの計算
export function calculateTextParameters(textAnalysis) {
    if (!textAnalysis) return {};
    
    const params = {
        textComplexity: 0.5,    // テキストの複雑さ
        textRhythm: 0.5,        // テキストのリズム
        textEmphasis: 0.5,      // テキストの強調度
        textGeometry: 'float',  // テキストのジオメトリタイプ
        textAnimation: 'fade',  // テキストのアニメーション
        textDensity: 1.0        // テキストの密度
    };
    
    // 文の長さに基づく複雑さ
    params.textComplexity = Math.min(1.0, textAnalysis.wordCount / 30);
    
    // 文の数に基づくリズム
    params.textRhythm = Math.min(1.0, textAnalysis.sentenceCount / 5);
    
    // 文体に基づく調整
    if (textAnalysis.style.interrogative) {
        params.textGeometry = 'curve';
        params.textAnimation = 'pulse';
    }
    
    if (textAnalysis.style.exclamatory) {
        params.textEmphasis = 0.8;
        params.textAnimation = 'explode';
    }
    
    if (textAnalysis.style.imperative) {
        params.textEmphasis = 0.7;
        params.textGeometry = 'bold';
    }
    
    if (textAnalysis.style.repetitive) {
        params.textDensity = 1.5;
        params.textAnimation = 'echo';
    }
    
    if (textAnalysis.style.formal) {
        params.textGeometry = 'serif';
    }
    
    if (textAnalysis.style.poetic) {
        params.textGeometry = 'flowing';
        params.textAnimation = 'float';
    }
    
    // テキスト長に基づく密度
    params.textDensity = Math.max(0.5, Math.min(2.0, textAnalysis.length / 100));
    
    return params;
}

// 感情と言語分析を組み合わせた最終的なビジュアルパラメータの計算
export function calculateVisualParameters(emotionData, text) {
    // 感情パラメータの計算
    const emotionParams = calculateEmotionParameters(emotionData);
    
    // テキスト分析
    const textAnalysis = analyzeText(text);
    
    // テキストパラメータの計算
    const textParams = calculateTextParameters(textAnalysis);
    
    // パラメータの統合
    const visualParams = {
        ...emotionParams,
        ...textParams,
        keywords: textAnalysis ? textAnalysis.keywords : []
    };
    
    return visualParams;
}
