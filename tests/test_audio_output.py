"""
テキスト読み上げモジュールのテスト
"""
import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from pathlib import Path

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from output_modules.audio_output.openai_tts import OpenAITTSEngine, TextToSpeechManager


class TestOpenAITTSEngine(unittest.TestCase):
    """OpenAI TTS エンジンのテスト"""
    
    @patch('output_modules.audio_output.openai_tts.OpenAI')
    @patch('output_modules.audio_output.openai_tts.pygame')
    def setUp(self, mock_pygame, mock_openai):
        """テスト前の準備"""
        self.mock_openai = mock_openai
        self.mock_mixer = mock_pygame.mixer
        self.api_key = "test_api_key"
        self.tts_engine = OpenAITTSEngine(api_key=self.api_key)
    
    def test_init(self):
        """初期化のテスト"""
        self.assertEqual(self.tts_engine.voice, "alloy")
        self.assertEqual(self.tts_engine.model, "tts-1")
        self.assertEqual(self.tts_engine.output_format, "mp3")
        self.mock_openai.assert_called_once_with(api_key=self.api_key)
    
    @patch('output_modules.audio_output.openai_tts.OpenAI')
    def test_init_no_api_key(self, mock_openai):
        """API キーなしの初期化テスト"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env_api_key"}):
            tts_engine = OpenAITTSEngine()
            mock_openai.assert_called_once_with(api_key="env_api_key")
    
    @patch('output_modules.audio_output.openai_tts.OpenAI')
    @patch('output_modules.audio_output.openai_tts.load_dotenv', return_value=False)
    def test_init_error(self, mock_load_dotenv, mock_openai):
        """API キーがない場合のエラーテスト"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                OpenAITTSEngine()
    
    def test_generate_speech(self):
        """音声生成テスト"""
        # モックのセットアップ
        mock_response = MagicMock()
        self.tts_engine.client.audio.speech.create.return_value = mock_response
        
        # Path.exists()をモック化
        with patch('pathlib.Path.exists', return_value=True):
            # テスト
            text = "テスト音声です"
            result = self.tts_engine.generate_speech(text)
            
            # 検証
            self.tts_engine.client.audio.speech.create.assert_called_once_with(
                model="tts-1",
                voice="alloy",
                input=text,
                speed=1.0
            )
            mock_response.stream_to_file.assert_called_once()
            self.assertTrue(result.exists())
    
    def test_play_speech_with_text(self):
        """テキストからの音声再生テスト"""
        # generate_speech をモック化
        mock_path = MagicMock(spec=Path)
        mock_path.__str__.return_value = "/tmp/test.mp3"
        self.tts_engine.generate_speech = MagicMock(return_value=mock_path)
        
        # 実際のplay_speechメソッドではなく、モックバージョンを使用
        with patch('output_modules.audio_output.openai_tts.pygame.mixer') as mock_mixer:
            with patch('pathlib.Path.exists', return_value=True):
                # テスト
                result = self.tts_engine.play_speech(text="テスト音声です")
                
                # 検証
                self.tts_engine.generate_speech.assert_called_once_with("テスト音声です", None, 1.0)
                mock_mixer.music.load.assert_called_once_with("/tmp/test.mp3")
                mock_mixer.music.play.assert_called_once()
                self.assertTrue(result)
    
    def test_play_speech_with_file(self):
        """ファイルからの音声再生テスト"""
        # 実際のplay_speechメソッドではなく、モックバージョンを使用
        with patch('output_modules.audio_output.openai_tts.pygame.mixer') as mock_mixer:
            with patch('pathlib.Path.exists', return_value=True):
                # テスト
                file_path = "/tmp/existing.mp3"
                result = self.tts_engine.play_speech(file_path=file_path)
                
                # 検証
                mock_mixer.music.load.assert_called_once_with(file_path)
                mock_mixer.music.play.assert_called_once()
                self.assertTrue(result)
    
    def test_play_speech_error(self):
        """音声再生エラーテスト"""
        # エラーをシミュレート
        self.mock_mixer.music.load.side_effect = Exception("テスト例外")
        
        # テスト
        result = self.tts_engine.play_speech(file_path="/tmp/test.mp3")
        
        # 検証
        self.assertFalse(result)
    
    def test_stop_playback(self):
        """再生停止テスト"""
        # 実際のstop_playbackメソッドではなく、モックバージョンを使用
        with patch('output_modules.audio_output.openai_tts.pygame.mixer') as mock_mixer:
            # テスト
            mock_mixer.music.get_busy.return_value = True
            result = self.tts_engine.stop_playback()
            
            # 検証
            mock_mixer.music.stop.assert_called_once()
            self.assertTrue(result)


class TestTextToSpeechManager(unittest.TestCase):
    """テキスト読み上げマネージャーのテスト"""
    
    @patch('output_modules.audio_output.openai_tts.OpenAITTSEngine')
    def setUp(self, mock_engine_class):
        """テスト前の準備"""
        self.mock_engine_class = mock_engine_class
        self.mock_engine = MagicMock()
        mock_engine_class.return_value = self.mock_engine
        
        self.config = {
            "voice": "nova",
            "speed": 1.2,
            "language": "ja",
            "enabled": True
        }
        self.tts_manager = TextToSpeechManager(self.config)
    
    def test_init(self):
        """初期化テスト"""
        self.assertEqual(self.tts_manager.voice, "nova")
        self.assertEqual(self.tts_manager.speed, 1.2)
        self.assertEqual(self.tts_manager.enabled, True)
        self.mock_engine_class.assert_called_once_with(voice="nova")
    
    def test_init_default(self):
        """デフォルト設定の初期化テスト"""
        tts_manager = TextToSpeechManager()
        self.assertEqual(tts_manager.voice, "nova")  # 日本語デフォルト
        self.assertEqual(tts_manager.speed, 1.0)
        self.assertEqual(tts_manager.enabled, True)
    
    @patch('output_modules.audio_output.openai_tts.OpenAITTSEngine')
    def test_init_engine_error(self, mock_engine_class):
        """エンジン初期化エラーテスト"""
        mock_engine_class.side_effect = Exception("テスト例外")
        tts_manager = TextToSpeechManager()
        self.assertFalse(tts_manager.enabled)
        self.assertIsNone(tts_manager.tts_engine)
    
    def test_speak(self):
        """音声読み上げテスト"""
        self.mock_engine.play_speech.return_value = True
        
        # テスト
        result = self.tts_manager.speak("こんにちは")
        
        # 検証
        self.mock_engine.play_speech.assert_called_once_with(
            text="こんにちは",
            voice="nova",
            speed=1.2,
            block=False
        )
        self.assertTrue(result)
    
    def test_speak_disabled(self):
        """無効化された状態での読み上げテスト"""
        self.tts_manager.enabled = False
        
        # テスト
        result = self.tts_manager.speak("こんにちは")
        
        # 検証
        self.mock_engine.play_speech.assert_not_called()
        self.assertFalse(result)
    
    def test_speak_error(self):
        """読み上げエラーテスト"""
        self.mock_engine.play_speech.side_effect = Exception("テスト例外")
        
        # テスト
        result = self.tts_manager.speak("こんにちは")
        
        # 検証
        self.assertFalse(result)
    
    def test_stop(self):
        """停止テスト"""
        self.mock_engine.stop_playback.return_value = True
        
        # テスト
        result = self.tts_manager.stop()
        
        # 検証
        self.mock_engine.stop_playback.assert_called_once()
        self.assertTrue(result)
    
    def test_cleanup(self):
        """クリーンアップテスト"""
        # テスト
        self.tts_manager.cleanup()
        
        # 検証
        self.mock_engine.cleanup.assert_called_once()


if __name__ == '__main__':
    unittest.main()
