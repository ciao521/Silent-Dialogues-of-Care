"""
Silent Dialogues of Care - 境界なき対話
総合テスト - 全コンポーネントの連携を検証

このスクリプトは、すべてのモジュールが連携して正しく動作することを検証します。
各コンポーネントをモック化し、エンドツーエンドの動作を確認します。
"""
import asyncio
import unittest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import yaml
from main_orchestrator import MainOrchestrator


class TestFullIntegration(unittest.TestCase):
    """全コンポーネントの統合テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # テスト用の設定
        self.test_config = {
            'input': {
                'audio': {
                    'device_id': 0,
                    'sample_rate': 44100,
                    'channels': 1,
                    'chunk_size': 1024
                },
                'video': {
                    'device_id': 0,
                    'width': 640,
                    'height': 480,
                    'fps': 30
                }
            },
            'analysis': {
                'speech_to_text': {
                    'model': 'whisper-1',
                    'language': 'ja'
                },
                'vocal_emotion': {
                    'provider': 'hume'
                },
                'facial_emotion': {
                    'use_mediapipe': True,
                    'model_path': 'models/facial_emotion_classifier.onnx'
                },
                'multimodal_fusion': {
                    'vocal_weight': 0.6,
                    'facial_weight': 0.4
                }
            },
            'llm': {
                'model': 'gpt-4o',
                'temperature': 0.7,
                'max_tokens': 300,
                'system_message': 'あなたは来場者の感情に寄り添い、共感的な応答を提供するAIアシスタントです。'
            },
            'output': {
                'audio': {
                    'enabled': True,
                    'voice': 'nova',
                    'speed': 1.0,
                    'language': 'ja'
                }
            },
            'visuals': {
                'websocket': {
                    'host': '127.0.0.1',
                    'port': 8765
                }
            },
            'logging': {
                'level': 'INFO',
                'save_interactions': False
            }
        }
        
        # モックの準備
        self.setup_mocks()
        
        # テスト用オーケストレータの作成
        with patch('main_orchestrator.MainOrchestrator._load_config', return_value=self.test_config):
            self.orchestrator = MainOrchestrator()
    
    def setup_mocks(self):
        """各モジュールのモックを設定"""
        # 各クラスのパッチを適用
        self.patches = [
            patch('input_modules.audio_capture.microphone_handler.MicrophoneHandler'),
            patch('input_modules.face_capture.opencv_mediapipe_capture.FaceCaptureHandler'),
            patch('analysis_modules.speech_to_text.whisper_transcriber.WhisperTranscriber'),
            patch('analysis_modules.vocal_emotion_recognition.hume_evi_analyzer.HumeEviAnalyzer'),
            patch('analysis_modules.facial_emotion_recognition.emotion_classifier_onnx.FacialEmotionRecognizer'),
            patch('analysis_modules.multimodal_fusion.fusion_engine.EmotionFusionEngine'),
            patch('llm_interaction.empathetic_response_generator.EmpatheticResponseGenerator'),
            patch('output_modules.audio_output.openai_tts.TextToSpeechManager'),
            patch('generative_visuals.backend_websocket_server.app.WebSocketServer')
        ]
        
        # パッチを開始
        self.mocks = [p.start() for p in self.patches]
        
        # モックのインスタンスを作成
        self.mock_instances = [MagicMock() for _ in self.mocks]
        
        # 各モックのreturn_valueを設定
        for mock_class, mock_instance in zip(self.mocks, self.mock_instances):
            mock_class.return_value = mock_instance
        
        # 特定のモックの振る舞いを設定
        # 音声キャプチャ
        self.mock_instances[0].get_audio_chunk.return_value = np.zeros(1024, dtype=np.float32)
        
        # 顔キャプチャ
        self.mock_instances[1].get_face_data.return_value = {
            'image': np.zeros((480, 640, 3), dtype=np.uint8),
            'landmarks': [{'x': 0.5, 'y': 0.5, 'z': 0.0} for _ in range(468)]
        }
        
        # 音声認識
        self.mock_instances[2].get_transcription.return_value = {
            'text': 'こんにちは、私の気持ちを聞いてください。',
            'confidence': 0.95
        }
        
        # 音声感情分析
        self.mock_instances[3].analyze_emotion.return_value = {
            'joy': 0.7,
            'sadness': 0.1,
            'anger': 0.05,
            'fear': 0.05,
            'surprise': 0.1
        }
        
        # 表情感情分析
        self.mock_instances[4].predict_emotion.return_value = {
            'joy': 0.6,
            'sadness': 0.2,
            'anger': 0.05,
            'fear': 0.05,
            'surprise': 0.1
        }
        
        # 感情統合
        self.mock_instances[5].fuse_emotions.return_value = {
            'joy': 0.65,
            'sadness': 0.15,
            'anger': 0.05,
            'fear': 0.05,
            'surprise': 0.1,
            'combined_score': 0.85
        }
        
        # 応答生成
        self.mock_instances[6].generate_response.return_value = {
            'response': 'こんにちは。あなたの喜びが伝わってきます。どんなことがあなたを嬉しくさせたのですか？',
            'model': 'gpt-4o'
        }
        
        # WebSocketサーバー
        self.mock_instances[8].send_emotion_data.return_value = asyncio.Future()
        self.mock_instances[8].send_emotion_data.return_value.set_result(True)
    
    def tearDown(self):
        """テスト後の後処理"""
        # パッチを停止
        for p in self.patches:
            p.stop()
    
    async def async_test_initialize_components(self):
        """コンポーネント初期化のテスト"""
        result = await self.orchestrator.initialize_components()
        self.assertTrue(result)
        
        # 各コンポーネントが正しく初期化されたか確認
        for i, mock_class in enumerate(self.mocks):
            mock_class.assert_called_once()
    
    def test_initialize_components(self):
        """非同期初期化テストのラッパー"""
        asyncio.run(self.async_test_initialize_components())
    
    async def async_test_process_interaction(self):
        """インタラクション処理のテスト"""
        # コンポーネントを初期化
        await self.orchestrator.initialize_components()
        
        # 処理を実行
        await self.orchestrator._process_interaction()
        
        # 各コンポーネントのメソッドが呼び出されたか確認
        self.mock_instances[0].get_audio_chunk.assert_called()  # 音声取得
        self.mock_instances[1].get_face_data.assert_called_once()  # 顔取得
        self.mock_instances[2].get_transcription.assert_called_once()  # 音声認識
        self.mock_instances[3].analyze_emotion.assert_called_once()  # 音声感情分析
        self.mock_instances[4].predict_emotion.assert_called_once()  # 表情感情分析
        self.mock_instances[5].fuse_emotions.assert_called_once()  # 感情統合
        self.mock_instances[6].generate_response.assert_called_once()  # 応答生成
        self.mock_instances[7].speak.assert_called_once()  # テキスト読み上げ
    
    def test_process_interaction(self):
        """非同期インタラクション処理テストのラッパー"""
        asyncio.run(self.async_test_process_interaction())
    
    def test_stop(self):
        """停止処理のテスト"""
        # コンポーネントを初期化（同期的に実行）
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.orchestrator.initialize_components())
        
        # 停止処理を実行
        self.orchestrator.stop()
        
        # 各コンポーネントの停止メソッドが呼び出されたか確認
        self.mock_instances[0].stop_recording.assert_called_once()  # マイク停止
        self.mock_instances[1].stop_capture.assert_called_once()  # カメラ停止
        self.mock_instances[7].stop.assert_called_once()  # 読み上げ停止
        self.mock_instances[7].cleanup.assert_called_once()  # 読み上げクリーンアップ


class TestRealInitialization(unittest.TestCase):
    """実際の初期化テスト（モックなし）"""
    
    def setUp(self):
        """テスト前の準備"""
        # 設定ファイルのパス
        self.config_path = "config/settings.yaml"
        
        # 必要なディレクトリを作成
        os.makedirs('logs', exist_ok=True)
    
    def test_load_config(self):
        """設定読み込みのテスト"""
        # 設定ファイルが存在するか確認
        self.assertTrue(os.path.exists(self.config_path))
        
        # 設定ファイルを読み込めるか確認
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # 必要な設定が含まれているか確認
        self.assertIn('input', config)
        self.assertIn('analysis', config)
        self.assertIn('llm', config)
        self.assertIn('output', config)
        self.assertIn('audio', config['output'])
        
        # 音声出力の設定が正しいか確認
        self.assertTrue(config['output']['audio']['enabled'])
        self.assertEqual(config['output']['audio']['voice'], 'nova')
        self.assertEqual(config['output']['audio']['language'], 'ja')


if __name__ == '__main__':
    unittest.main()
