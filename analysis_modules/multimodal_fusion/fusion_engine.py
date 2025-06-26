"""
マルチモーダル感情統合モジュール
音声感情と表情感情を統合して総合的な感情状態を推定
"""
import numpy as np
from loguru import logger

class EmotionFusionEngine:
    def __init__(self, config):
        """
        感情統合エンジンの初期化
        
        Args:
            config (dict): 設定ファイルから読み込んだマルチモーダル感情統合設定
        """
        # 各モダリティの重み
        self.vocal_weight = config.get('vocal_weight', 0.6)
        self.facial_weight = config.get('facial_weight', 0.4)
        
        # 感情の基本次元
        self.dimension_keys = ['valence', 'activation']
        
        # 感情カテゴリとその次元空間での位置
        self.emotion_map = {
            # 基本感情の次元空間マッピング（valence, activation）
            'neutral': (0.0, 0.0),
            'happy': (0.8, 0.6),
            'sad': (-0.7, -0.4),
            'surprise': (0.2, 0.8),
            'fear': (-0.7, 0.7),
            'anger': (-0.8, 0.8),
            'disgust': (-0.6, 0.2),
            'contempt': (-0.5, -0.2),
            'interest': (0.5, 0.3),
            'amusement': (0.8, 0.7),
            'awe': (0.5, 0.5),
            'contentment': (0.7, -0.2),
            'desire': (0.6, 0.5),
            'disappointment': (-0.6, -0.3),
            'doubt': (-0.3, 0.1),
            'elation': (0.9, 0.8),
            'pain': (-0.8, 0.4),
            'tiredness': (-0.2, -0.7),
            'triumph': (0.9, 0.9)
        }
        
        # 逆マッピング: 次元空間座標から最も近い感情カテゴリを得るための辞書
        self.dimension_to_emotion = self.emotion_map
        
        logger.info("EmotionFusionEngineを初期化しました")
    
    def fuse_emotions(self, vocal_emotion, facial_emotion, text=None):
        """
        音声感情と表情感情を統合
        
        Args:
            vocal_emotion (dict): 音声感情分析結果
            facial_emotion (dict): 表情感情分析結果
            text (str, optional): 発話テキスト（感情的キーワード分析用）
            
        Returns:
            dict: 統合された感情状態
        """
        try:
            # 入力チェック
            if vocal_emotion is None:
                logger.warning("音声感情データがありません。表情感情のみを使用します")
                return self._process_single_modality(facial_emotion)
            
            if facial_emotion is None:
                logger.warning("表情感情データがありません。音声感情のみを使用します")
                return self._process_single_modality(vocal_emotion)
            
            # 感情次元の統合
            fused_dimensions = {}
            for dim in self.dimension_keys:
                vocal_val = vocal_emotion.get(dim, 0.0)
                facial_val = facial_emotion.get(dim, 0.0)
                
                # 加重平均による統合
                fused_dimensions[dim] = (
                    vocal_val * self.vocal_weight + 
                    facial_val * self.facial_weight
                )
            
            # 次元から最も近い感情カテゴリを特定
            primary_emotion = self._get_closest_emotion(
                fused_dimensions['valence'],
                fused_dimensions['activation']
            )
            
            # 信頼度の計算（両モダリティの一致度から）
            vocal_primary = vocal_emotion.get('primary_emotion', 'neutral')
            facial_primary = facial_emotion.get('primary_emotion', 'neutral')
            
            # 両モダリティの主要感情が一致するか
            modality_agreement = 1.0 if vocal_primary == facial_primary else 0.5
            
            # 両モダリティのスコアを考慮した信頼度
            vocal_score = vocal_emotion.get('primary_score', 0.5)
            facial_score = facial_emotion.get('primary_score', 0.5)
            score_factor = (vocal_score * self.vocal_weight + facial_score * self.facial_weight)
            
            confidence = modality_agreement * score_factor
            
            # テキストからの感情的キーワード抽出（オプション）
            emotional_keywords = []
            if text:
                emotional_keywords = self._extract_emotional_keywords(text)
            
            # 統合結果
            result = {
                'primary_emotion': primary_emotion,
                'confidence': confidence,
                'valence': fused_dimensions['valence'],
                'activation': fused_dimensions['activation'],
                'vocal_contribution': {
                    'emotion': vocal_primary,
                    'score': vocal_score,
                    'weight': self.vocal_weight
                },
                'facial_contribution': {
                    'emotion': facial_primary,
                    'score': facial_score,
                    'weight': self.facial_weight
                },
                'emotional_keywords': emotional_keywords
            }
            
            logger.info(f"感情統合完了: 主要感情={result['primary_emotion']}(信頼度:{result['confidence']:.2f}), " + 
                        f"感情価={result['valence']:.2f}, 活性度={result['activation']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"感情統合中にエラーが発生: {e}")
            return self._empty_result()
    
    def _process_single_modality(self, emotion_data):
        """単一モダリティのみの場合の処理"""
        if emotion_data is None:
            return self._empty_result()
        
        primary_emotion = emotion_data.get('primary_emotion', 'neutral')
        primary_score = emotion_data.get('primary_score', 0.5)
        valence = emotion_data.get('valence', 0.0)
        activation = emotion_data.get('activation', 0.0)
        
        return {
            'primary_emotion': primary_emotion,
            'confidence': primary_score,
            'valence': valence,
            'activation': activation,
            'vocal_contribution': {
                'emotion': primary_emotion,
                'score': primary_score,
                'weight': 1.0
            } if 'vocal' in str(emotion_data) else {
                'emotion': 'unknown',
                'score': 0.0,
                'weight': 0.0
            },
            'facial_contribution': {
                'emotion': primary_emotion,
                'score': primary_score,
                'weight': 1.0
            } if 'facial' in str(emotion_data) else {
                'emotion': 'unknown',
                'score': 0.0,
                'weight': 0.0
            },
            'emotional_keywords': []
        }
    
    def _get_closest_emotion(self, valence, activation):
        """
        感情次元（感情価と活性度）から最も近い感情カテゴリを取得
        
        Args:
            valence (float): 感情価（-1.0〜1.0）
            activation (float): 活性度（-1.0〜1.0）
            
        Returns:
            str: 最も近い感情カテゴリ
        """
        min_distance = float('inf')
        closest_emotion = 'neutral'
        
        for emotion, (e_valence, e_activation) in self.emotion_map.items():
            # ユークリッド距離を計算
            distance = np.sqrt((valence - e_valence)**2 + (activation - e_activation)**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_emotion = emotion
        
        return closest_emotion
    
    def _extract_emotional_keywords(self, text):
        """
        テキストから感情的なキーワードを抽出（簡易版）
        
        Args:
            text (str): 分析するテキスト
            
        Returns:
            list: 抽出された感情的キーワードのリスト
        """
        if not text:
            return []
        
        # 簡易的な感情キーワード辞書（実際のアプリケーションではより高度な感情分析が必要）
        emotional_keywords = {
            'positive': [
                '幸せ', '嬉しい', '楽しい', '喜び', '愛', '希望', '安心', '満足', '感謝',
                '笑顔', '元気', '幸福', '最高', '素晴らしい', '良い', '好き', '安らぎ'
            ],
            'negative': [
                '悲しい', '辛い', '苦しい', '怒り', '恐怖', '不安', '心配', '恐れ', '絶望',
                '憎しみ', '嫌い', '失望', '後悔', '痛み', '孤独', '虚しい', '嫌悪'
            ],
            'arousal': [
                '興奮', 'ドキドキ', 'わくわく', '驚き', '衝撃', '緊張', '焦り', '急ぎ',
                '激しい', '熱い', '燃える', 'すごい', '動揺', '震える'
            ],
            'calm': [
                '穏やか', '静か', '平和', 'リラックス', '落ち着く', '安定', '和む',
                'ゆったり', 'のんびり', '眠い', '疲れた', '癒し', '休息'
            ]
        }
        
        found_keywords = []
        
        # 単純なキーワードマッチング
        text_lower = text.lower()
        for category, keywords in emotional_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_keywords.append({
                        'keyword': keyword,
                        'category': category
                    })
        
        return found_keywords
    
    def _empty_result(self):
        """空の結果を返す（エラー時用）"""
        return {
            'primary_emotion': 'neutral',
            'confidence': 0.0,
            'valence': 0.0,
            'activation': 0.0,
            'vocal_contribution': {
                'emotion': 'unknown',
                'score': 0.0,
                'weight': self.vocal_weight
            },
            'facial_contribution': {
                'emotion': 'unknown',
                'score': 0.0,
                'weight': self.facial_weight
            },
            'emotional_keywords': []
        }


# テスト用コード
if __name__ == "__main__":
    # テスト設定
    test_config = {
        'vocal_weight': 0.6,
        'facial_weight': 0.4
    }
    
    # 感情統合エンジンの初期化
    fusion_engine = EmotionFusionEngine(test_config)
    
    # テスト用の感情データ
    test_vocal_emotion = {
        'primary_emotion': 'happy',
        'primary_score': 0.75,
        'valence': 0.7,
        'activation': 0.6
    }
    
    test_facial_emotion = {
        'primary_emotion': 'surprise',
        'primary_score': 0.8,
        'valence': 0.2,
        'activation': 0.9
    }
    
    test_text = "わくわくして、とても嬉しいです！驚きました！"
    
    # 感情統合の実行
    result = fusion_engine.fuse_emotions(test_vocal_emotion, test_facial_emotion, test_text)
    
    # 結果表示
    print("感情統合結果:")
    print(f"主要感情: {result['primary_emotion']} (信頼度: {result['confidence']:.2f})")
    print(f"感情価 (Valence): {result['valence']:.2f}")
    print(f"活性度 (Activation): {result['activation']:.2f}")
    
    print("\n音声感情の寄与:")
    contribution = result['vocal_contribution']
    print(f"  感情: {contribution['emotion']} (スコア: {contribution['score']:.2f}, 重み: {contribution['weight']:.2f})")
    
    print("\n表情感情の寄与:")
    contribution = result['facial_contribution']
    print(f"  感情: {contribution['emotion']} (スコア: {contribution['score']:.2f}, 重み: {contribution['weight']:.2f})")
    
    print("\n感情的キーワード:")
    for keyword in result['emotional_keywords']:
        print(f"  {keyword['keyword']} ({keyword['category']})")
