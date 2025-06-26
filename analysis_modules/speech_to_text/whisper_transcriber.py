"""
音声からテキストへの変換（Speech-to-Text）モジュール
OpenAI Whisper APIを使用
"""
import os
import time
import numpy as np
import openai
from loguru import logger

class WhisperTranscriber:
    def __init__(self, config, api_key=None):
        """
        Whisper音声文字起こしモジュールの初期化
        
        Args:
            config (dict): 設定ファイルから読み込んだSTT設定
            api_key (str, optional): OpenAI APIキー。Noneの場合は環境変数から読み込む
        """
        # APIキーの設定
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OpenAI APIキーが設定されていません")
            raise ValueError("OpenAI APIキーが必要です。環境変数OPENAI_API_KEYを設定するか、初期化時にapi_keyを指定してください")
        
        openai.api_key = self.api_key
        
        # Whisper設定
        self.model = config.get('model', 'whisper-1')
        self.language = config.get('language', 'ja')
        self.sample_rate = config.get('sample_rate', 44100)
        
        # 音声バッファ（複数のチャンクを結合して処理するため）
        self.audio_buffer = np.array([], dtype=np.float32)
        
        # 最小バッファサイズ（秒）- 短すぎる音声は意味をなさない
        self.min_buffer_duration = 1.0
        
        # 最大バッファサイズ（秒）- 長すぎるとレスポンスが遅くなる
        self.max_buffer_duration = 5.0
        
        logger.info(f"WhisperTranscriberを初期化: モデル={self.model}, 言語={self.language}")
    
    def add_audio_chunk(self, audio_chunk):
        """
        音声チャンクをバッファに追加
        
        Args:
            audio_chunk (numpy.ndarray): 音声データのチャンク
        """
        # チャンクをバッファに追加
        if len(audio_chunk.shape) > 1 and audio_chunk.shape[1] > 1:
            # ステレオからモノラルに変換
            audio_chunk = np.mean(audio_chunk, axis=1)
        
        # データ型をfloat32に統一
        audio_chunk = audio_chunk.astype(np.float32)
        
        # バッファに追加
        self.audio_buffer = np.concatenate([self.audio_buffer, audio_chunk.flatten()])
        
        # バッファが最大サイズを超えたら古いデータを削除
        max_samples = int(self.max_buffer_duration * self.sample_rate)
        if len(self.audio_buffer) > max_samples:
            self.audio_buffer = self.audio_buffer[-max_samples:]
    
    def get_transcription(self, reset_buffer=True):
        """
        現在のバッファ内の音声をテキストに変換
        
        Args:
            reset_buffer (bool): 変換後にバッファをクリアするかどうか
            
        Returns:
            dict: 文字起こし結果（'text'キーにテキスト、'language'キーに検出言語）
                  バッファが短すぎる場合は空テキストを返す
        """
        # バッファが最小サイズより小さい場合は処理しない
        min_samples = int(self.min_buffer_duration * self.sample_rate)
        if len(self.audio_buffer) < min_samples:
            return {'text': '', 'language': self.language}
        
        try:
            # 音声データを一時ファイルに保存
            import tempfile
            import soundfile as sf
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # WAVファイルとして保存
            sf.write(temp_filename, self.audio_buffer, self.sample_rate)
            
            # OpenAI Whisper APIで文字起こし
            with open(temp_filename, 'rb') as audio_file:
                response = openai.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=self.language
                )
            
            # 一時ファイルを削除
            try:
                os.unlink(temp_filename)
            except Exception as e:
                logger.warning(f"一時ファイルの削除に失敗: {e}")
            
            # バッファをリセット（オプション）
            if reset_buffer:
                self.reset_buffer()
            
            transcription = response.text.strip()
            logger.info(f"文字起こし完了: '{transcription}'")
            
            return {
                'text': transcription,
                'language': self.language
            }
            
        except Exception as e:
            logger.error(f"文字起こし中にエラーが発生: {e}")
            return {'text': '', 'language': self.language}
    
    def reset_buffer(self):
        """音声バッファをクリア"""
        self.audio_buffer = np.array([], dtype=np.float32)
        logger.debug("音声バッファをリセットしました")


# テスト用コード
if __name__ == "__main__":
    import sounddevice as sd
    
    # テスト設定
    test_config = {
        'model': 'whisper-1',
        'language': 'ja',
        'sample_rate': 16000  # Whisperは16kHzで最適化されている
    }
    
    # APIキーが環境変数に設定されていることを確認
    if not os.environ.get("OPENAI_API_KEY"):
        print("テストにはOPENAI_API_KEY環境変数が必要です")
        exit(1)
    
    # トランスクライバーの初期化
    transcriber = WhisperTranscriber(test_config)
    
    # 5秒間の音声録音
    duration = 5  # 秒
    print(f"{duration}秒間の音声を録音します。何か話してください...")
    
    recording = sd.rec(
        int(duration * test_config['sample_rate']),
        samplerate=test_config['sample_rate'],
        channels=1
    )
    sd.wait()  # 録音完了まで待機
    
    print("録音完了。文字起こしを実行します...")
    
    # 録音データをトランスクライバーに渡す
    transcriber.add_audio_chunk(recording)
    
    # 文字起こし実行
    result = transcriber.get_transcription()
    
    print(f"文字起こし結果: {result['text']}")
