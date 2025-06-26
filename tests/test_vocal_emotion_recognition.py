"""
音声感情認識モジュールのテスト
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from pathlib import Path
import numpy as np
import os
import asyncio

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis_modules.vocal_emotion_recognition.hume_evi_analyzer import HumeEviAnalyzer


class TestHumeEviAnalyzer(unittest.TestCase):
    """Hume EVI 音声感情認識モジュールのテスト"""
    
    @patch('analysis_modules.vocal_emotion_recognition.hume_evi_analyzer.HumeBatchClient')
    def setUp(self, mock_hume_client):
        """テスト前の準備"""
        # APIキーを環境変数に設定
        os.environ["HUME_API_KEY"] = "test_api_key"
        
        # モッククライアントを設定
        self.mock_client = MagicMock()
        mock_hume_client.return_value = self.mock_client
        
        # 設定を準備
        self.config = {
            'sample_rate': 16000,
            'min_duration': 1.0,
            'max_duration': 10.0
        }
        
        # アナライザーの初期化
        self.analyzer = HumeEviAnalyzer(self.config)
    
    def test_init(self):
        """初期化のテスト"""
        self.assertEqual(self.analyzer.api_key, "test_api_key")
        self.assertEqual(self.analyzer.sample_rate, 16000)
        self.assertIsNotNone(self.analyzer.emotion_categories)
        self.assertEqual(len(self.analyzer.emotion_categories), 14)  # Hume EVI 2の感情カテゴリ数
    
    @patch('analysis_modules.vocal_emotion_recognition.hume_evi_analyzer.HumeBatchClient')
    def test_init_custom_api_key(self, mock_hume_client):
        """カスタムAPIキーでの初期化テスト"""
        analyzer = HumeEviAnalyzer(self.config, api_key="custom_api_key")
        self.assertEqual(analyzer.api_key, "custom_api_key")
        mock_hume_client.assert_called_once_with("custom_api_key")
    
    @patch('analysis_modules.vocal_emotion_recognition.hume_evi_analyzer.HumeBatchClient')
    def test_init_no_api_key(self, mock_hume_client):
        """APIキーなしの初期化テスト"""
        # 環境変数をクリア
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                HumeEviAnalyzer(self.config)
    
    @patch('analysis_modules.vocal_emotion_recognition.hume_evi_analyzer.soundfile.write')
    @patch('analysis_modules.vocal_emotion_recognition.hume_evi_analyzer.tempfile.NamedTemporaryFile')
    @patch('analysis_modules.vocal_emotion_recognition.hume_evi_analyzer.os.path.exists')
    async def test_analyze_emotion(self, mock_exists, mock_temp_file, mock_sf_write):
        """感情分析テスト"""
        # テスト用の音声データ
        audio_data = np.random.rand(16000, 1).astype(np.float32)  # 1秒の音声
        
        # 一時ファイルのモック
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test_audio.wav"
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        mock_exists.return_value = True
        
        # Hume APIレスポンスのモック
        mock_predictions = {
            "prosody": {
                "predictions": [
                    {
                        "emotions": [
                            {"name": "Amusement", "score": 0.8},
                            {"name": "Contentment", "score": 0.6},
                            {"name": "Interest", "score": 0.4}
                        ]
                    }
                ]
            }
        }
        
        # Hume APIの非同期メソッドをモック
        self.mock_client.submit_job = AsyncMock()
        self.mock_client.get_job_predictions = AsyncMock()
        self.mock_client.submit_job.return_value = "test_job"
        self.mock_client.get_job_predictions.return_value = mock_predictions
        
        # 感情分析を実行
        result = await self.analyzer.analyze_emotion(audio_data)
        
        # 検証
        mock_sf_write.assert_called_once()
        self.mock_client.submit_job.assert_called_once()
        self.mock_client.get_job_predictions.assert_called_once_with("test_job")
        
        # 結果の検証
        self.assertIsInstance(result, dict)
        self.assertIn("emotion_scores", result)
        self.assertEqual(len(result["emotion_scores"]), 14)  # 全感情カテゴリ
        self.assertIn("primary_emotion", result)
        self.assertIn("primary_score", result)
        self.assertIn("valence", result)
    
    @patch('analysis_modules.vocal_emotion_recognition.hume_evi_analyzer.soundfile.write')
    @patch('analysis_modules.vocal_emotion_recognition.hume_evi_analyzer.tempfile.NamedTemporaryFile')
    async def test_analyze_emotion_no_predictions(self, mock_temp_file, mock_sf_write):
        """予測結果がない場合のテスト"""
        # テスト用の音声データ
        audio_data = np.random.rand(16000, 1).astype(np.float32)  # 1秒の音声
        
        # 一時ファイルのモック
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test_audio.wav"
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        
        # 結果がない場合のモック
        self.mock_client.submit_job = AsyncMock()
        self.mock_client.get_job_predictions = AsyncMock()
        self.mock_client.submit_job.return_value = "test_job"
        self.mock_client.get_job_predictions.return_value = {"prosody": []}
        
        # 感情分析を実行
        result = await self.analyzer.analyze_emotion(audio_data)
        
        # 検証
        self.assertIsInstance(result, dict)
        self.assertIn("emotion_scores", result)
        self.assertEqual(sum(result["emotion_scores"].values()), 0.0)  # 感情スコアがすべて0のはず
    
    @patch('analysis_modules.vocal_emotion_recognition.hume_evi_analyzer.soundfile.write')
    @patch('analysis_modules.vocal_emotion_recognition.hume_evi_analyzer.tempfile.NamedTemporaryFile')
    async def test_analyze_emotion_api_error(self, mock_temp_file, mock_sf_write):
        """API エラーのテスト"""
        # テスト用の音声データ
        audio_data = np.random.rand(16000, 1).astype(np.float32)  # 1秒の音声
        
        # 一時ファイルのモック
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test_audio.wav"
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        
        # API エラーをシミュレート
        self.mock_client.submit_job = AsyncMock()
        self.mock_client.submit_job.side_effect = Exception("API エラー")
        
        # 感情分析を実行
        result = await self.analyzer.analyze_emotion(audio_data)
        
        # 検証
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "音声感情分析中にエラーが発生しました: API エラー")
    
    def test_normalize_emotion_scores(self):
        """感情スコア正規化テスト"""
        # テスト用の感情スコア
        emotion_scores = [
            {"name": "Amusement", "score": 0.8},
            {"name": "Contentment", "score": 0.6},
            {"name": "Interest", "score": 0.4}
        ]
        
        # 正規化を実行
        normalized = self.analyzer.normalize_emotion_scores(emotion_scores)
        
        # 検証
        self.assertEqual(len(normalized), 3)
        self.assertAlmostEqual(normalized[0]["score"], 0.8 / 1.8, places=5)  # 0.444...
        self.assertAlmostEqual(normalized[1]["score"], 0.6 / 1.8, places=5)  # 0.333...
        self.assertAlmostEqual(normalized[2]["score"], 0.4 / 1.8, places=5)  # 0.222...
        self.assertAlmostEqual(sum(item["score"] for item in normalized), 1.0, places=5)
    
    def test_normalize_emotion_scores_empty(self):
        """空の感情スコア正規化テスト"""
        normalized = self.analyzer.normalize_emotion_scores([])
        self.assertEqual(normalized, [])
    
    def test_format_result(self):
        """結果フォーマットテスト"""
        # テスト用の感情スコア
        emotion_scores = [
            {"name": "Amusement", "score": 0.5},
            {"name": "Contentment", "score": 0.3},
            {"name": "Interest", "score": 0.2}
        ]
        
        # 結果をフォーマット
        formatted = self.analyzer.format_result(emotion_scores)
        
        # 検証
        self.assertIsInstance(formatted, dict)
        self.assertIn("emotions", formatted)
        self.assertEqual(len(formatted["emotions"]), 3)
        self.assertEqual(formatted["emotions"][0]["name"], "Amusement")
        self.assertEqual(formatted["emotions"][0]["score"], 0.5)
        self.assertIn("dominant_emotion", formatted)
        self.assertEqual(formatted["dominant_emotion"], "Amusement")
        self.assertIn("emotion_vector", formatted)
        self.assertEqual(len(formatted["emotion_vector"]), 14)  # 全感情カテゴリ
    
    def test_format_result_empty(self):
        """空の結果フォーマットテスト"""
        formatted = self.analyzer.format_result([])
        self.assertIsInstance(formatted, dict)
        self.assertIn("emotions", formatted)
        self.assertEqual(len(formatted["emotions"]), 0)
        self.assertIn("dominant_emotion", formatted)
        self.assertEqual(formatted["dominant_emotion"], "neutral")
        self.assertIn("emotion_vector", formatted)
        self.assertEqual(len(formatted["emotion_vector"]), 14)  # 全感情カテゴリ
        self.assertTrue(all(score == 0.0 for score in formatted["emotion_vector"]))


# asyncioのテストランナー
def run_async_test(coro):
    return asyncio.run(coro)


if __name__ == '__main__':
    unittest.main()
