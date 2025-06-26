"""
表情感情認識モジュールのテスト
"""
import os
import sys
import unittest
import numpy as np

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_modules.facial_emotion_recognition.emotion_classifier_onnx import FacialEmotionRecognizer

class TestFacialEmotionRecognizer(unittest.TestCase):
    """表情感情認識モジュールのテストケース"""
    
    def setUp(self):
        """テスト前の準備"""
        # テスト用の設定
        self.test_config = {
            'model_path': 'models/facial_emotion_classifier.onnx'  # 存在しなくてもデモモードで動作する
        }
        
        # 感情認識モジュールの初期化
        self.recognizer = FacialEmotionRecognizer(self.test_config)
    
    def test_initialization(self):
        """初期化が正しく行われることをテスト"""
        self.assertIsNotNone(self.recognizer)
        self.assertEqual(len(self.recognizer.emotion_classes), 8)  # 8つの感情クラス
        
        # モデルが存在しない場合、デモモードになるはず
        self.assertTrue(self.recognizer.demo_mode)
    
    def test_extract_features(self):
        """特徴抽出関数のテスト"""
        # テスト用のランドマークデータ（468点のMediaPipeランドマーク）
        test_landmarks = np.random.rand(468, 3)  # (x, y, z)座標
        
        # 特徴抽出
        features = self.recognizer.extract_features(test_landmarks)
        
        # 特徴ベクトルが存在することを確認
        self.assertIsNotNone(features)
        self.assertIsInstance(features, np.ndarray)
        
        # 特徴ベクトルの型がfloat32であることを確認
        self.assertEqual(features.dtype, np.float32)
    
    def test_empty_landmarks(self):
        """ランドマークがない場合の特徴抽出テスト"""
        # ランドマークがNoneの場合
        features = self.recognizer.extract_features(None)
        self.assertIsNone(features)
        
        # 空のランドマーク配列の場合
        features = self.recognizer.extract_features(np.array([]))
        self.assertIsNone(features)
    
    def test_predict_emotion_with_valid_data(self):
        """有効なデータでの感情予測テスト"""
        # テスト用の顔データ
        test_landmarks = np.random.rand(468, 3)  # ランダムなランドマーク
        test_face_data = {
            'frame': np.zeros((480, 640, 3), dtype=np.uint8),  # ダミーフレーム
            'landmarks': test_landmarks,
            'timestamp': 12345.6789
        }
        
        # 感情予測
        emotion_result = self.recognizer.predict_emotion(test_face_data)
        
        # 結果の検証
        self.assertIsNotNone(emotion_result)
        self.assertIn('primary_emotion', emotion_result)
        self.assertIn('primary_score', emotion_result)
        self.assertIn('valence', emotion_result)
        self.assertIn('activation', emotion_result)
        self.assertIn('emotion_scores', emotion_result)
        
        # デモモードでの結果（is_demoフラグがTrue）
        self.assertTrue(emotion_result['is_demo'])
    
    def test_predict_emotion_with_invalid_data(self):
        """無効なデータでの感情予測テスト"""
        # ランドマークがない場合
        test_face_data = {
            'frame': np.zeros((480, 640, 3), dtype=np.uint8),
            'landmarks': None,
            'timestamp': 12345.6789
        }
        
        emotion_result = self.recognizer.predict_emotion(test_face_data)
        
        # デフォルトの'neutral'が返されるはず
        self.assertEqual(emotion_result['primary_emotion'], 'neutral')
        self.assertEqual(emotion_result['primary_score'], 1.0)
        self.assertEqual(emotion_result['valence'], 0.0)
        self.assertEqual(emotion_result['activation'], 0.0)
        self.assertFalse(emotion_result['is_demo'])
    
    def test_empty_result(self):
        """空の結果が正しいフォーマットで返されることをテスト"""
        empty_result = self.recognizer._empty_result()
        
        self.assertIsInstance(empty_result, dict)
        self.assertEqual(empty_result['primary_emotion'], 'neutral')
        self.assertEqual(empty_result['primary_score'], 1.0)
        self.assertEqual(empty_result['valence'], 0.0)
        self.assertEqual(empty_result['activation'], 0.0)
        
        # 感情スコア辞書にすべての感情クラスが含まれているか
        for emotion in self.recognizer.emotion_classes:
            self.assertIn(emotion, empty_result['emotion_scores'])
    
    def test_demo_result_generation(self):
        """デモモードの結果生成をテスト"""
        demo_result = self.recognizer._generate_demo_result()
        
        self.assertIsInstance(demo_result, dict)
        self.assertIn('primary_emotion', demo_result)
        self.assertIn('primary_score', demo_result)
        self.assertIn('valence', demo_result)
        self.assertIn('activation', demo_result)
        self.assertIn('emotion_scores', demo_result)
        self.assertTrue(demo_result['is_demo'])
        
        # 感情スコアの合計が約1.0になることを確認
        total_score = sum(demo_result['emotion_scores'].values())
        self.assertAlmostEqual(total_score, 1.0, places=5)


if __name__ == '__main__':
    unittest.main()
