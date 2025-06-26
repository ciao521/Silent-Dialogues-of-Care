"""
マルチモーダル感情統合モジュールのテスト
"""
import os
import sys
import unittest

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_modules.multimodal_fusion.fusion_engine import EmotionFusionEngine

class TestEmotionFusionEngine(unittest.TestCase):
    """感情統合エンジンのテストケース"""
    
    def setUp(self):
        """テスト前の準備"""
        # テスト用の設定
        self.test_config = {
            'vocal_weight': 0.6,
            'facial_weight': 0.4
        }
        
        # 感情統合エンジンの初期化
        self.fusion_engine = EmotionFusionEngine(self.test_config)
        
        # テスト用の感情データ
        self.test_vocal_emotion = {
            'primary_emotion': 'happy',
            'primary_score': 0.75,
            'valence': 0.7,
            'activation': 0.6
        }
        
        self.test_facial_emotion = {
            'primary_emotion': 'surprise',
            'primary_score': 0.8,
            'valence': 0.2,
            'activation': 0.9
        }
        
        # 異なる感情のテストデータ
        self.test_vocal_emotion_sad = {
            'primary_emotion': 'sad',
            'primary_score': 0.8,
            'valence': -0.7,
            'activation': -0.4
        }
        
        self.test_text = "わくわくして、とても嬉しいです！驚きました！"
    
    def test_initialization(self):
        """初期化が正しく行われることをテスト"""
        self.assertIsNotNone(self.fusion_engine)
        self.assertEqual(self.fusion_engine.vocal_weight, 0.6)
        self.assertEqual(self.fusion_engine.facial_weight, 0.4)
        self.assertIsNotNone(self.fusion_engine.emotion_map)
        self.assertTrue(len(self.fusion_engine.emotion_map) > 0)
    
    def test_fuse_emotions_both_modalities(self):
        """両方のモダリティ（音声と表情）がある場合の感情統合をテスト"""
        result = self.fusion_engine.fuse_emotions(
            self.test_vocal_emotion,
            self.test_facial_emotion,
            self.test_text
        )
        
        # 基本的な結果の検証
        self.assertIsNotNone(result)
        self.assertIn('primary_emotion', result)
        self.assertIn('confidence', result)
        self.assertIn('valence', result)
        self.assertIn('activation', result)
        
        # 感情価と活性度が重み付き平均になっていることを確認
        expected_valence = (0.7 * 0.6) + (0.2 * 0.4)
        expected_activation = (0.6 * 0.6) + (0.9 * 0.4)
        
        self.assertAlmostEqual(result['valence'], expected_valence, places=5)
        self.assertAlmostEqual(result['activation'], expected_activation, places=5)
        
        # 各モダリティの寄与が記録されていることを確認
        self.assertIn('vocal_contribution', result)
        self.assertIn('facial_contribution', result)
        
        self.assertEqual(result['vocal_contribution']['emotion'], 'happy')
        self.assertEqual(result['facial_contribution']['emotion'], 'surprise')
    
    def test_fuse_emotions_vocal_only(self):
        """音声モダリティのみの場合の感情統合をテスト"""
        result = self.fusion_engine.fuse_emotions(
            self.test_vocal_emotion,
            None,
            self.test_text
        )
        
        # 結果が音声感情と一致することを確認
        self.assertEqual(result['primary_emotion'], self.test_vocal_emotion['primary_emotion'])
        self.assertEqual(result['valence'], self.test_vocal_emotion['valence'])
        self.assertEqual(result['activation'], self.test_vocal_emotion['activation'])
    
    def test_fuse_emotions_facial_only(self):
        """表情モダリティのみの場合の感情統合をテスト"""
        result = self.fusion_engine.fuse_emotions(
            None,
            self.test_facial_emotion,
            self.test_text
        )
        
        # 結果が表情感情と一致することを確認
        self.assertEqual(result['primary_emotion'], self.test_facial_emotion['primary_emotion'])
        self.assertEqual(result['valence'], self.test_facial_emotion['valence'])
        self.assertEqual(result['activation'], self.test_facial_emotion['activation'])
    
    def test_fuse_emotions_no_modalities(self):
        """どちらのモダリティもない場合の感情統合をテスト"""
        result = self.fusion_engine.fuse_emotions(None, None, self.test_text)
        
        # デフォルト値が設定されることを確認
        self.assertEqual(result['primary_emotion'], 'neutral')
        self.assertEqual(result['confidence'], 0.0)
        self.assertEqual(result['valence'], 0.0)
        self.assertEqual(result['activation'], 0.0)
    
    def test_fuse_emotions_conflicting_emotions(self):
        """感情が矛盾する場合の統合をテスト"""
        result = self.fusion_engine.fuse_emotions(
            self.test_vocal_emotion_sad,  # 悲しみ
            self.test_facial_emotion,      # 驚き
            self.test_text
        )
        
        # 信頼度が減少することを確認（モダリティの不一致のため）
        self.assertLess(result['confidence'], 1.0)
        
        # 重み付き平均が正しく計算されることを確認
        expected_valence = (-0.7 * 0.6) + (0.2 * 0.4)
        expected_activation = (-0.4 * 0.6) + (0.9 * 0.4)
        
        self.assertAlmostEqual(result['valence'], expected_valence, places=5)
        self.assertAlmostEqual(result['activation'], expected_activation, places=5)
    
    def test_get_closest_emotion(self):
        """感情次元から最も近い感情カテゴリを取得する関数をテスト"""
        # 明確なポジティブ・高活性の位置
        emotion = self.fusion_engine._get_closest_emotion(0.9, 0.8)
        self.assertIn(emotion, self.fusion_engine.emotion_map.keys())
        
        # 明確なネガティブ・低活性の位置
        emotion = self.fusion_engine._get_closest_emotion(-0.7, -0.6)
        self.assertIn(emotion, self.fusion_engine.emotion_map.keys())
        
        # ニュートラルに近い位置
        emotion = self.fusion_engine._get_closest_emotion(0.0, 0.0)
        self.assertEqual(emotion, 'neutral')
    
    def test_extract_emotional_keywords(self):
        """テキストから感情キーワードを抽出する関数をテスト"""
        # 感情キーワードを含むテキスト
        text = "とても幸せで嬉しいです。心配や不安はありません。"
        keywords = self.fusion_engine._extract_emotional_keywords(text)
        
        # キーワードが抽出されることを確認
        self.assertTrue(len(keywords) > 0)
        
        # 各キーワードにカテゴリが付与されていることを確認
        for keyword in keywords:
            self.assertIn('keyword', keyword)
            self.assertIn('category', keyword)
        
        # 空のテキストでのテスト
        keywords = self.fusion_engine._extract_emotional_keywords("")
        self.assertEqual(len(keywords), 0)
        
        # Noneでのテスト
        keywords = self.fusion_engine._extract_emotional_keywords(None)
        self.assertEqual(len(keywords), 0)
    
    def test_empty_result(self):
        """空の結果が正しいフォーマットで返されることをテスト"""
        empty_result = self.fusion_engine._empty_result()
        
        self.assertIsInstance(empty_result, dict)
        self.assertEqual(empty_result['primary_emotion'], 'neutral')
        self.assertEqual(empty_result['confidence'], 0.0)
        self.assertEqual(empty_result['valence'], 0.0)
        self.assertEqual(empty_result['activation'], 0.0)
        self.assertIn('vocal_contribution', empty_result)
        self.assertIn('facial_contribution', empty_result)
        self.assertEqual(len(empty_result['emotional_keywords']), 0)


if __name__ == '__main__':
    unittest.main()
