"""
音声からテキストへの変換モジュールのテスト
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import os
import numpy as np
import tempfile

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis_modules.speech_to_text.whisper_transcriber import WhisperTranscriber


class TestWhisperTranscriber(unittest.TestCase):
    """Whisper 音声文字起こしモジュールのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # APIキーを環境変数に設定
        os.environ["OPENAI_API_KEY"] = "test_api_key"
        
        # 設定を準備
        self.config = {
            'model': 'whisper-1',
            'language': 'ja',
            'sample_rate': 16000,
            'sensitivity': 0.5
        }
        
        # openaiモジュールをパッチ
        self.patcher = patch('analysis_modules.speech_to_text.whisper_transcriber.openai')
        self.mock_openai = self.patcher.start()
        
        # 文字起こしモジュールの初期化
        self.transcriber = WhisperTranscriber(self.config)
        
        # テスト用の音声データ（1秒の無音）
        self.test_audio = np.zeros((16000, 1), dtype=np.float32)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.patcher.stop()
    
    def test_init(self):
        """初期化テスト"""
        self.assertEqual(self.transcriber.api_key, "test_api_key")
        self.assertEqual(self.transcriber.model, "whisper-1")
        self.assertEqual(self.transcriber.language, "ja")
        self.assertEqual(self.transcriber.sample_rate, 16000)
        self.assertEqual(len(self.transcriber.audio_buffer), 0)
        self.assertEqual(self.transcriber.min_buffer_duration, 1.0)
        self.assertEqual(self.transcriber.max_buffer_duration, 5.0)
    
    @patch('analysis_modules.speech_to_text.whisper_transcriber.openai')
    def test_init_custom_api_key(self, mock_openai):
        """カスタムAPIキーでの初期化テスト"""
        transcriber = WhisperTranscriber(self.config, api_key="custom_api_key")
        self.assertEqual(transcriber.api_key, "custom_api_key")
        self.assertEqual(mock_openai.api_key, "custom_api_key")
    
    @patch('analysis_modules.speech_to_text.whisper_transcriber.openai')
    def test_init_no_api_key(self, mock_openai):
        """APIキーなしの初期化テスト"""
        # 環境変数をクリア
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                WhisperTranscriber(self.config)
    
    def test_add_audio_chunk(self):
        """音声チャンク追加テスト"""
        # 初期状態を確認
        self.assertEqual(len(self.transcriber.audio_buffer), 0)
        
        # 音声チャンクを追加
        self.transcriber.add_audio_chunk(self.test_audio)
        
        # バッファに追加されたことを確認
        self.assertEqual(len(self.transcriber.audio_buffer), 16000)
    
    def test_add_audio_chunk_multiple(self):
        """複数の音声チャンク追加テスト"""
        # 音声チャンクを2回追加
        self.transcriber.add_audio_chunk(self.test_audio)
        self.transcriber.add_audio_chunk(self.test_audio)
        
        # バッファに両方のチャンクが追加されたことを確認
        self.assertEqual(len(self.transcriber.audio_buffer), 32000)
    
    def test_clear_buffer(self):
        """バッファクリアテスト"""
        # 音声チャンクを追加
        self.transcriber.add_audio_chunk(self.test_audio)
        self.assertEqual(len(self.transcriber.audio_buffer), 16000)
        
        # バッファをクリア
        self.transcriber.clear_buffer()
        
        # バッファが空になったことを確認
        self.assertEqual(len(self.transcriber.audio_buffer), 0)
    
    def test_is_buffer_ready(self):
        """バッファ準備状態テスト"""
        # 初期状態（空のバッファ）
        self.assertFalse(self.transcriber.is_buffer_ready())
        
        # 最小サイズ未満のバッファ
        short_audio = np.zeros((int(self.transcriber.sample_rate * 0.5), 1), dtype=np.float32)  # 0.5秒
        self.transcriber.add_audio_chunk(short_audio)
        self.assertFalse(self.transcriber.is_buffer_ready())
        
        # 最小サイズ以上のバッファ
        self.transcriber.clear_buffer()
        long_audio = np.zeros((int(self.transcriber.sample_rate * 1.5), 1), dtype=np.float32)  # 1.5秒
        self.transcriber.add_audio_chunk(long_audio)
        self.assertTrue(self.transcriber.is_buffer_ready())
    
    def test_buffer_duration(self):
        """バッファ長さテスト"""
        # 2秒の音声データ
        audio_2sec = np.zeros((self.transcriber.sample_rate * 2, 1), dtype=np.float32)
        self.transcriber.add_audio_chunk(audio_2sec)
        
        # バッファの長さが2秒であることを確認
        self.assertAlmostEqual(self.transcriber.get_buffer_duration(), 2.0, places=2)
    
    @patch('analysis_modules.speech_to_text.whisper_transcriber.tempfile')
    def test_transcribe_audio(self, mock_tempfile):
        """音声文字起こしテスト"""
        # 一時ファイルのモック
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test_audio.wav"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp
        
        # OpenAI APIのモックレスポンス
        mock_response = {"text": "これはテストです"}
        self.mock_openai.Audio.transcribe.return_value = mock_response
        
        # 音声チャンクを追加
        self.transcriber.add_audio_chunk(self.test_audio)
        
        # 文字起こしを実行
        result = self.transcriber.transcribe_audio()
        
        # 検証
        self.mock_openai.Audio.transcribe.assert_called_once()
        self.assertEqual(result["text"], "これはテストです")
        
        # バッファがクリアされたことを確認
        self.assertEqual(len(self.transcriber.audio_buffer), 0)
    
    @patch('analysis_modules.speech_to_text.whisper_transcriber.tempfile')
    def test_transcribe_audio_empty_buffer(self, mock_tempfile):
        """空バッファでの文字起こしテスト"""
        # バッファを空にする
        self.transcriber.clear_buffer()
        
        # 文字起こしを実行
        result = self.transcriber.transcribe_audio()
        
        # 検証
        self.mock_openai.Audio.transcribe.assert_not_called()
        self.assertIn("error", result)
        self.assertIn("音声バッファが空です", result["error"])
    
    @patch('analysis_modules.speech_to_text.whisper_transcriber.tempfile')
    def test_transcribe_audio_api_error(self, mock_tempfile):
        """API エラーテスト"""
        # 一時ファイルのモック
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test_audio.wav"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp
        
        # APIエラーをシミュレート
        self.mock_openai.Audio.transcribe.side_effect = Exception("API エラー")
        
        # 音声チャンクを追加
        self.transcriber.add_audio_chunk(self.test_audio)
        
        # 文字起こしを実行
        result = self.transcriber.transcribe_audio()
        
        # 検証
        self.assertIn("error", result)
        self.assertIn("API エラー", result["error"])
    
    def test_trim_buffer_to_max_duration(self):
        """バッファトリミングテスト"""
        # 最大バッファサイズの2倍の音声データ
        max_samples = int(self.transcriber.sample_rate * self.transcriber.max_buffer_duration)
        long_audio = np.zeros((max_samples * 2, 1), dtype=np.float32)
        self.transcriber.add_audio_chunk(long_audio)
        
        # トリミング前のバッファサイズを確認
        self.assertEqual(len(self.transcriber.audio_buffer), max_samples * 2)
        
        # バッファをトリミング
        self.transcriber._trim_buffer_to_max_duration()
        
        # トリミング後のバッファサイズを確認
        self.assertEqual(len(self.transcriber.audio_buffer), max_samples)
        
        # 最新の部分が保持されていることを確認（この場合は全て0なので特に検証方法はないが、コンセプト上のテスト）
        expected_duration = self.transcriber.max_buffer_duration
        actual_duration = len(self.transcriber.audio_buffer) / self.transcriber.sample_rate
        self.assertAlmostEqual(actual_duration, expected_duration, places=2)


if __name__ == '__main__':
    unittest.main()
