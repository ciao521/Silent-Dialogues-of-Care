"""
音声キャプチャモジュールのテスト
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import numpy as np
import queue
import threading
import time

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from input_modules.audio_capture.microphone_handler import MicrophoneHandler


class TestMicrophoneHandler(unittest.TestCase):
    """マイクロフォンハンドラのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.config = {
            'device_id': 1,
            'sample_rate': 16000,
            'channels': 1,
            'chunk_size': 512,
            'min_volume': 0.01
        }
        
        # sounddevice モジュールをモック化
        self.patcher = patch('input_modules.audio_capture.microphone_handler.sd')
        self.mock_sd = self.patcher.start()
        
        # マイクハンドラの初期化
        self.mic_handler = MicrophoneHandler(self.config)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # モックのパッチを停止
        self.patcher.stop()
        
        # 録音中なら停止
        if self.mic_handler.is_recording:
            self.mic_handler.stop_recording()
    
    def test_init(self):
        """初期化のテスト"""
        self.assertEqual(self.mic_handler.device_id, 1)
        self.assertEqual(self.mic_handler.sample_rate, 16000)
        self.assertEqual(self.mic_handler.channels, 1)
        self.assertEqual(self.mic_handler.chunk_size, 512)
        self.assertIsInstance(self.mic_handler.audio_queue, queue.Queue)
        self.assertFalse(self.mic_handler.is_recording)
        self.assertIsNone(self.mic_handler.recording_thread)
    
    def test_init_default(self):
        """デフォルト設定の初期化テスト"""
        mic_handler = MicrophoneHandler({})
        self.assertEqual(mic_handler.device_id, 0)  # デフォルト値
        self.assertEqual(mic_handler.sample_rate, 44100)  # デフォルト値
        self.assertEqual(mic_handler.channels, 1)  # デフォルト値
        self.assertEqual(mic_handler.chunk_size, 1024)  # デフォルト値
    
    def test_start_recording(self):
        """録音開始テスト"""
        # 録音を開始
        self.mic_handler.start_recording()
        
        # 検証
        self.assertTrue(self.mic_handler.is_recording)
        self.assertIsNotNone(self.mic_handler.recording_thread)
        self.assertTrue(self.mic_handler.recording_thread.daemon)
        self.assertTrue(self.mic_handler.recording_thread.is_alive())
    
    def test_start_recording_already_recording(self):
        """既に録音中の場合のテスト"""
        # 録音状態に設定
        self.mic_handler.is_recording = True
        original_thread = threading.Thread()
        self.mic_handler.recording_thread = original_thread
        
        # 録音を開始しようとする
        self.mic_handler.start_recording()
        
        # 検証（状態が変わっていないこと）
        self.assertTrue(self.mic_handler.is_recording)
        self.assertEqual(self.mic_handler.recording_thread, original_thread)
    
    def test_stop_recording(self):
        """録音停止テスト"""
        # 録音を開始
        self.mic_handler.start_recording()
        
        # 少し待機
        time.sleep(0.1)
        
        # 録音を停止
        self.mic_handler.stop_recording()
        
        # 検証
        self.assertFalse(self.mic_handler.is_recording)
        self.assertIsNone(self.mic_handler.recording_thread)
    
    def test_stop_recording_not_recording(self):
        """録音していない場合の停止テスト"""
        # 録音していない状態で停止
        self.mic_handler.stop_recording()
        
        # 検証
        self.assertFalse(self.mic_handler.is_recording)
        self.assertIsNone(self.mic_handler.recording_thread)
    
    @patch('input_modules.audio_capture.microphone_handler.sd.InputStream')
    def test_record_audio(self, mock_input_stream):
        """音声録音処理のテスト"""
        # InputStream のモックを設定
        mock_stream = MagicMock()
        mock_input_stream.return_value.__enter__.return_value = mock_stream
        
        # テスト用の音声データ
        test_audio = np.random.rand(512, 1).astype(np.float32)
        
        # コールバック関数をシミュレート
        def simulate_callback():
            if self.mic_handler.is_recording:
                callback = mock_input_stream.call_args[1]['callback']
                callback(test_audio, 512, None, None)
        
        # モックストリームの read メソッドを上書き
        mock_stream.read.side_effect = lambda frames: (test_audio, None)
        
        # 録音を開始
        self.mic_handler.start_recording()
        
        # コールバックをシミュレート
        simulate_callback()
        
        # 少し待機
        time.sleep(0.1)
        
        # 録音を停止
        self.mic_handler.stop_recording()
        
        # 検証
        mock_input_stream.assert_called_once()
        self.assertFalse(self.mic_handler.audio_queue.empty())
        
        # キューからデータを取得
        audio_data = self.mic_handler.audio_queue.get(block=False)
        self.assertIsInstance(audio_data, np.ndarray)
    
    def test_get_audio_chunk(self):
        """音声チャンク取得テスト"""
        # テスト用の音声データをキューに入れる
        test_audio = np.random.rand(512, 1).astype(np.float32)
        self.mic_handler.audio_queue.put(test_audio)
        
        # 音声チャンクを取得
        chunk = self.mic_handler.get_audio_chunk(timeout=1.0)
        
        # 検証
        self.assertIsInstance(chunk, np.ndarray)
        np.testing.assert_array_equal(chunk, test_audio)
    
    def test_get_audio_chunk_timeout(self):
        """タイムアウト時のテスト"""
        # 空のキューで取得を試みる
        chunk = self.mic_handler.get_audio_chunk(timeout=0.1)
        
        # 検証
        self.assertIsNone(chunk)
    
    def test_get_audio_buffer(self):
        """音声バッファ取得テスト"""
        # テスト用の音声データをキューに入れる
        for _ in range(5):
            test_audio = np.random.rand(512, 1).astype(np.float32)
            self.mic_handler.audio_queue.put(test_audio)
        
        # 音声バッファを取得（最大3チャンク）
        buffer = self.mic_handler.get_audio_buffer(max_chunks=3)
        
        # 検証
        self.assertIsInstance(buffer, np.ndarray)
        self.assertEqual(buffer.shape, (512 * 3, 1))
        
        # キューにはまだ2チャンク残っているはず
        self.assertEqual(self.mic_handler.audio_queue.qsize(), 2)
    
    def test_get_audio_buffer_empty(self):
        """空のキューでのバッファ取得テスト"""
        # 空のキューで取得を試みる
        buffer = self.mic_handler.get_audio_buffer(max_chunks=3)
        
        # 検証
        self.assertIsNone(buffer)
    
    def test_clear_audio_queue(self):
        """音声キュークリアテスト"""
        # テスト用の音声データをキューに入れる
        for _ in range(5):
            test_audio = np.random.rand(512, 1).astype(np.float32)
            self.mic_handler.audio_queue.put(test_audio)
        
        # キューをクリア
        self.mic_handler.clear_audio_queue()
        
        # 検証
        self.assertTrue(self.mic_handler.audio_queue.empty())


if __name__ == '__main__':
    unittest.main()
