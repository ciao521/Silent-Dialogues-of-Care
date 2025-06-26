"""
OpenAI TTS API を使用したテキスト読み上げモジュール
"""
import os
import time
import logging
import tempfile
from pathlib import Path
import pygame
from openai import OpenAI
from dotenv import load_dotenv

# ロギング設定
logger = logging.getLogger(__name__)

class OpenAITTSEngine:
    """
    OpenAI のテキスト読み上げ API を使用して、テキストを音声に変換するクラス
    """
    
    def __init__(self, api_key=None, voice="alloy", model="tts-1", output_format="mp3"):
        """
        OpenAI TTS エンジンの初期化
        
        Args:
            api_key (str, optional): OpenAI API キー。None の場合は環境変数から取得
            voice (str, optional): 使用する音声。デフォルトは "alloy"
            model (str, optional): 使用するモデル。デフォルトは "tts-1"
            output_format (str, optional): 出力フォーマット。デフォルトは "mp3"
        """
        # 環境変数から API キーを取得（もし指定されていない場合）
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError("OpenAI API キーが指定されておらず、環境変数にも設定されていません")
        
        self.client = OpenAI(api_key=api_key)
        self.voice = voice
        self.model = model
        self.output_format = output_format
        self.temp_dir = Path(tempfile.gettempdir()) / "silent_dialogues_tts"
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        
        # Pygame の初期化
        pygame.mixer.init()
    
    def generate_speech(self, text, voice=None, speed=1.0):
        """
        テキストから音声を生成し、一時ファイルとして保存
        
        Args:
            text (str): 音声に変換するテキスト
            voice (str, optional): 使用する音声。None の場合はデフォルト値を使用
            speed (float, optional): 音声の速度。デフォルトは 1.0
            
        Returns:
            Path: 生成された音声ファイルのパス
        """
        if voice is None:
            voice = self.voice
            
        try:
            timestamp = int(time.time())
            output_path = self.temp_dir / f"speech_{timestamp}.{self.output_format}"
            
            # OpenAI API を使用して音声を生成
            response = self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                speed=speed
            )
            
            # 音声ファイルを保存
            response.stream_to_file(str(output_path))
            logger.info(f"音声が生成されました: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"音声生成中にエラーが発生しました: {e}")
            raise
    
    def play_speech(self, text=None, file_path=None, voice=None, speed=1.0, block=False):
        """
        テキストから音声を生成して再生、または既存の音声ファイルを再生
        
        Args:
            text (str, optional): 音声に変換するテキスト
            file_path (str or Path, optional): 再生する音声ファイルのパス
            voice (str, optional): 使用する音声。None の場合はデフォルト値を使用
            speed (float, optional): 音声の速度。デフォルトは 1.0
            block (bool, optional): 音声の再生が完了するまでブロックするかどうか
            
        Returns:
            bool: 再生が成功したかどうか
        """
        try:
            # テキストが指定されている場合は、音声を生成
            if text is not None:
                file_path = self.generate_speech(text, voice, speed)
            elif file_path is None:
                raise ValueError("テキストまたはファイルパスのいずれかを指定する必要があります")
            
            # 音声ファイルを再生
            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()
            
            # ブロックモードの場合は、再生が完了するまで待機
            if block:
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            
            return True
            
        except Exception as e:
            logger.error(f"音声再生中にエラーが発生しました: {e}")
            return False
    
    def stop_playback(self):
        """
        現在再生中の音声を停止
        """
        try:
            pygame.mixer.music.stop()
            logger.info("音声再生を停止しました")
            return True
        except Exception as e:
            logger.error(f"音声停止中にエラーが発生しました: {e}")
            return False
    
    def cleanup(self):
        """
        一時ファイルをクリーンアップ
        """
        try:
            for file in self.temp_dir.glob(f"*.{self.output_format}"):
                file.unlink()
            logger.info("一時ファイルをクリーンアップしました")
        except Exception as e:
            logger.error(f"クリーンアップ中にエラーが発生しました: {e}")


class TextToSpeechManager:
    """
    テキスト読み上げ機能の管理クラス
    """
    
    def __init__(self, config=None):
        """
        テキスト読み上げマネージャーの初期化
        
        Args:
            config (dict, optional): 設定パラメータ
        """
        self.config = config or {}
        
        # デフォルト設定
        self.voice = self.config.get("voice", "alloy")
        self.speed = float(self.config.get("speed", 1.0))
        self.enabled = self.config.get("enabled", True)
        
        # 言語に基づいて音声を選択
        language = self.config.get("language", "ja")
        if language == "ja":
            # 日本語向けの音声
            self.voice = self.config.get("voice", "nova")
        
        # TTS エンジンの初期化
        try:
            self.tts_engine = OpenAITTSEngine(voice=self.voice)
            logger.info(f"テキスト読み上げエンジンが初期化されました (音声: {self.voice})")
        except Exception as e:
            logger.error(f"テキスト読み上げエンジンの初期化に失敗しました: {e}")
            self.enabled = False
            self.tts_engine = None
    
    def speak(self, text, block=False):
        """
        テキストを音声で読み上げ
        
        Args:
            text (str): 読み上げるテキスト
            block (bool, optional): 読み上げが完了するまでブロックするかどうか
            
        Returns:
            bool: 読み上げが開始されたかどうか
        """
        if not self.enabled or self.tts_engine is None:
            logger.warning("テキスト読み上げは無効になっています")
            return False
        
        try:
            return self.tts_engine.play_speech(
                text=text,
                voice=self.voice,
                speed=self.speed,
                block=block
            )
        except Exception as e:
            logger.error(f"テキスト読み上げ中にエラーが発生しました: {e}")
            return False
    
    def stop(self):
        """
        現在の読み上げを停止
        
        Returns:
            bool: 停止が成功したかどうか
        """
        if self.tts_engine is None:
            return False
        
        try:
            return self.tts_engine.stop_playback()
        except Exception as e:
            logger.error(f"読み上げ停止中にエラーが発生しました: {e}")
            return False
    
    def cleanup(self):
        """
        リソースをクリーンアップ
        """
        if self.tts_engine is not None:
            try:
                self.tts_engine.cleanup()
                logger.info("テキスト読み上げリソースをクリーンアップしました")
            except Exception as e:
                logger.error(f"クリーンアップ中にエラーが発生しました: {e}")
