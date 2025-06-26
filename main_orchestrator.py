"""
Silent Dialogues of Care - 境界なき対話
メインオーケストレータ - 各モジュールを統合して全体の処理フローを制御
"""
import os
import time
import asyncio
import yaml
import dotenv
import threading
from loguru import logger

# モジュールのインポート
from input_modules.audio_capture.microphone_handler import MicrophoneHandler
from input_modules.face_capture.opencv_mediapipe_capture import FaceCaptureHandler
from analysis_modules.speech_to_text.whisper_transcriber import WhisperTranscriber
from analysis_modules.vocal_emotion_recognition.hume_evi_analyzer import HumeEviAnalyzer
from analysis_modules.facial_emotion_recognition.emotion_classifier_onnx import FacialEmotionRecognizer
from analysis_modules.multimodal_fusion.fusion_engine import EmotionFusionEngine
from llm_interaction.empathetic_response_generator import EmpatheticResponseGenerator
from output_modules.audio_output.openai_tts import TextToSpeechManager
from generative_visuals.backend_websocket_server.app import WebSocketServer

class MainOrchestrator:
    def __init__(self, config_path="config/settings.yaml"):
        """
        メインオーケストレータの初期化
        
        Args:
            config_path (str): 設定ファイルのパス
        """
        # 設定ファイルの読み込み
        self.config = self._load_config(config_path)
        
        # ロギングの設定
        self._setup_logging()
        
        # コンポーネントの初期化
        self.mic_handler = None
        self.face_handler = None
        self.transcriber = None
        self.vocal_analyzer = None
        self.facial_recognizer = None
        self.fusion_engine = None
        self.response_generator = None
        self.tts_manager = None
        self.websocket_server = None
        
        # 処理フラグ
        self.is_running = False
        self.is_processing = False
        
        # 処理間隔（秒）
        self.processing_interval = 1.0  # 1秒ごとに感情分析
        
        logger.info("メインオーケストレータを初期化しました")
    
    def _load_config(self, config_path):
        """設定ファイルを読み込む"""
        try:
            # 環境変数ファイルの読み込み
            dotenv_path = os.path.join(os.path.dirname(config_path), ".env")
            if os.path.exists(dotenv_path):
                dotenv.load_dotenv(dotenv_path)
            
            # YAML設定ファイルの読み込み
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # 環境変数の展開
            self._expand_env_vars(config)
            
            return config
        except Exception as e:
            print(f"設定ファイルの読み込みに失敗しました: {e}")
            return {}
    
    def _expand_env_vars(self, config):
        """設定内の環境変数を展開"""
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    config[key] = os.environ.get(env_var, value)
                elif isinstance(value, (dict, list)):
                    self._expand_env_vars(value)
        elif isinstance(config, list):
            for i, item in enumerate(config):
                if isinstance(item, str) and item.startswith('${') and item.endswith('}'):
                    env_var = item[2:-1]
                    config[i] = os.environ.get(env_var, item)
                elif isinstance(item, (dict, list)):
                    self._expand_env_vars(item)
    
    def _setup_logging(self):
        """ロギングの設定"""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        logger.remove()  # デフォルトハンドラを削除
        logger.add(
            "logs/silent_dialogues_{time}.log",
            rotation="1 day",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
        logger.add(lambda msg: print(msg), level=log_level)
    
    async def initialize_components(self):
        """各コンポーネントを初期化"""
        try:
            # 入力モジュールの初期化
            self.mic_handler = MicrophoneHandler(self.config.get('input', {}).get('audio', {}))
            self.face_handler = FaceCaptureHandler(self.config.get('input', {}).get('video', {}))
            
            # 分析モジュールの初期化
            self.transcriber = WhisperTranscriber(self.config.get('analysis', {}).get('speech_to_text', {}))
            self.vocal_analyzer = HumeEviAnalyzer(self.config.get('analysis', {}).get('vocal_emotion', {}))
            self.facial_recognizer = FacialEmotionRecognizer(self.config.get('analysis', {}).get('facial_emotion', {}))
            self.fusion_engine = EmotionFusionEngine(self.config.get('analysis', {}).get('multimodal_fusion', {}))
            
            # LLM対話モジュールの初期化
            self.response_generator = EmpatheticResponseGenerator(self.config.get('llm', {}))
            
            # テキスト読み上げモジュールの初期化
            self.tts_manager = TextToSpeechManager(self.config.get('output', {}).get('audio', {}))
            
            # WebSocketサーバーの初期化
            self.websocket_server = WebSocketServer(self.config.get('visuals', {}).get('websocket', {}))
            
            logger.info("すべてのコンポーネントを初期化しました")
            return True
        except Exception as e:
            logger.error(f"コンポーネントの初期化中にエラーが発生: {e}")
            return False
    
    def start(self):
        """処理を開始"""
        if self.is_running:
            logger.warning("既に実行中です")
            return
        
        self.is_running = True
        
        # 非同期初期化
        loop = asyncio.get_event_loop()
        init_success = loop.run_until_complete(self.initialize_components())
        
        if not init_success:
            logger.error("初期化に失敗したため、処理を中断します")
            self.is_running = False
            return
        
        # 入力キャプチャの開始
        self.mic_handler.start_recording()
        self.face_handler.start_capture()
        
        # WebSocketサーバーを別スレッドで起動
        websocket_thread = threading.Thread(target=self._run_websocket_server)
        websocket_thread.daemon = True
        websocket_thread.start()
        
        # メイン処理ループ
        logger.info("処理ループを開始します")
        
        try:
            loop.run_until_complete(self._main_loop())
        except KeyboardInterrupt:
            logger.info("ユーザーにより中断されました")
        finally:
            self.stop()
    
    def _run_websocket_server(self):
        """WebSocketサーバーを実行（別スレッド）"""
        try:
            self.websocket_server.run()
        except Exception as e:
            logger.error(f"WebSocketサーバーの実行中にエラーが発生: {e}")
    
    async def _main_loop(self):
        """メイン処理ループ（非同期）"""
        last_process_time = 0
        
        while self.is_running:
            current_time = time.time()
            
            # 一定間隔で処理を実行
            if current_time - last_process_time >= self.processing_interval and not self.is_processing:
                self.is_processing = True
                last_process_time = current_time
                
                try:
                    await self._process_interaction()
                except Exception as e:
                    logger.error(f"インタラクション処理中にエラーが発生: {e}")
                
                self.is_processing = False
            
            # CPUの負荷を下げるために少し待機
            await asyncio.sleep(0.01)
    
    async def _process_interaction(self):
        """インタラクション処理（音声入力、表情入力、感情分析、応答生成）"""
        # 1. 音声データの取得と処理
        audio_chunks = []
        for _ in range(10):  # 複数のチャンクを収集
            chunk = self.mic_handler.get_audio_chunk(timeout=0.01)
            if chunk is not None:
                audio_chunks.append(chunk)
                self.transcriber.add_audio_chunk(chunk)
        
        # 2. 顔データの取得
        face_data = self.face_handler.get_face_data(timeout=0.1)
        
        # 音声がない場合や顔が検出されない場合はスキップ
        if not audio_chunks and face_data is None:
            return
        
        # 3. 音声からテキストへの変換
        transcription = self.transcriber.get_transcription(reset_buffer=False)
        text = transcription.get('text', '')
        
        # テキストが空でない場合のみバッファをリセット
        if text:
            self.transcriber.reset_buffer()
            logger.info(f"認識されたテキスト: {text}")
        
        # 4. 音声感情分析
        vocal_emotion = None
        if audio_chunks:
            import numpy as np
            combined_audio = np.concatenate(audio_chunks)
            vocal_emotion = await self.vocal_analyzer.analyze_emotion(combined_audio)
        
        # 5. 表情感情分析
        facial_emotion = None
        if face_data:
            facial_emotion = self.facial_recognizer.predict_emotion(face_data)
        
        # 6. マルチモーダル感情統合
        fused_emotion = self.fusion_engine.fuse_emotions(vocal_emotion, facial_emotion, text)
        
        # テキストと感情の両方がある場合のみLLM応答を生成
        ai_response = None
        if text:
            # 7. 共感的応答の生成
            response_result = self.response_generator.generate_response(text, fused_emotion)
            ai_response = response_result.get('response', '')
            
            if ai_response:
                logger.info(f"AI応答: {ai_response[:50]}...")
                
                # 設定で有効な場合、テキスト読み上げを実行
                if self.config.get('output', {}).get('audio', {}).get('enabled', True):
                    self.tts_manager.speak(ai_response, block=False)
        
        # 8. WebSocketを通じてクライアントに結果を送信
        if fused_emotion:
            text_data = {'text': text, 'timestamp': time.time()} if text else None
            response_data = {'response': ai_response, 'timestamp': time.time()} if ai_response else None
            
            # 非同期送信
            asyncio.create_task(
                self.websocket_server.send_emotion_data(fused_emotion, text_data, response_data)
            )
        
        # 9. インタラクションのログ保存（オプション）
        if self.config.get('logging', {}).get('save_interactions', False):
            self._log_interaction(text, fused_emotion, ai_response)
    
    def _log_interaction(self, text, emotion_data, response):
        """インタラクションをログに保存"""
        try:
            if not os.path.exists('logs'):
                os.makedirs('logs')
            
            log_file = 'logs/interaction_log.jsonl'
            
            # 匿名化オプション
            anonymize = self.config.get('logging', {}).get('anonymize', True)
            
            # ログデータの作成
            log_data = {
                'timestamp': time.time(),
                'text': text if not anonymize else '[ユーザー発話]',
                'emotion': emotion_data,
                'response': response if not anonymize else '[AI応答]'
            }
            
            # JSON Lines形式で追記
            import json
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                
        except Exception as e:
            logger.error(f"インタラクションログの保存中にエラー: {e}")
    
    def stop(self):
        """処理を停止"""
        logger.info("処理を停止します")
        self.is_running = False
        
        # 各モジュールの停止処理
        if self.mic_handler:
            self.mic_handler.stop_recording()
        
        if self.face_handler:
            self.face_handler.stop_capture()
        
        if self.tts_manager:
            self.tts_manager.stop()
            self.tts_manager.cleanup()
        
        logger.info("すべての処理を停止しました")


# メイン実行
if __name__ == "__main__":
    try:
        # コマンドライン引数の処理
        import argparse
        parser = argparse.ArgumentParser(description="Silent Dialogues of Care - メインオーケストレータ")
        parser.add_argument("--config", default="config/settings.yaml", help="設定ファイルのパス")
        args = parser.parse_args()
        
        # オーケストレータの作成と実行
        orchestrator = MainOrchestrator(config_path=args.config)
        orchestrator.start()
        
    except KeyboardInterrupt:
        print("\nプログラムが中断されました")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
