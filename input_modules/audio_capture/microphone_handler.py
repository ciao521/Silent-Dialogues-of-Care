"""
マイクからの音声入力を処理するモジュール
"""
import sounddevice as sd
import numpy as np
import queue
import threading
import time
from loguru import logger

class MicrophoneHandler:
    def __init__(self, config):
        """
        マイク入力ハンドラの初期化
        
        Args:
            config (dict): 設定ファイルから読み込んだ音声入力設定
        """
        self.device_id = config.get('device_id', 0)
        self.sample_rate = config.get('sample_rate', 44100)
        self.channels = config.get('channels', 1)
        self.chunk_size = config.get('chunk_size', 1024)
        
        # 音声データを保存するキュー
        self.audio_queue = queue.Queue()
        
        # 録音状態の管理
        self.is_recording = False
        self.recording_thread = None
        
        logger.info(f"マイクハンドラを初期化: デバイスID={self.device_id}, サンプルレート={self.sample_rate}Hz")
    
    def start_recording(self):
        """録音を開始"""
        if self.is_recording:
            logger.warning("録音はすでに開始されています")
            return
            
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        logger.info("録音を開始しました")
    
    def stop_recording(self):
        """録音を停止"""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=1.0)
            self.recording_thread = None
        logger.info("録音を停止しました")
    
    def _record_audio(self):
        """バックグラウンドで音声を録音し、キューに追加するスレッド関数"""
        def audio_callback(indata, frames, time, status):
            """sounddeviceのコールバック関数"""
            if status:
                logger.warning(f"音声キャプチャ中にエラーが発生: {status}")
            # 音声データをキューに追加
            self.audio_queue.put(indata.copy())
        
        try:
            with sd.InputStream(
                device=self.device_id,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=audio_callback
            ):
                logger.debug("音声ストリームを開始しました")
                # 録音フラグがFalseになるまで待機
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"音声録音中にエラーが発生: {e}")
            self.is_recording = False
    
    def get_audio_chunk(self, timeout=0.1):
        """
        キューから音声チャンクを取得
        
        Args:
            timeout (float): キューからの取得タイムアウト時間（秒）
            
        Returns:
            numpy.ndarray or None: 音声データ（タイムアウト時はNone）
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_available_devices(self):
        """
        利用可能なオーディオデバイスのリストを返す
        
        Returns:
            list: オーディオデバイス情報のリスト
        """
        devices = sd.query_devices()
        return devices
    
    def __del__(self):
        """クリーンアップ処理"""
        self.stop_recording()


# テスト用コード
if __name__ == "__main__":
    # テスト設定
    test_config = {
        'device_id': 0,
        'sample_rate': 44100,
        'channels': 1,
        'chunk_size': 1024
    }
    
    # マイクハンドラの初期化
    mic = MicrophoneHandler(test_config)
    
    # 利用可能なデバイス一覧を表示
    print("利用可能なオーディオデバイス:")
    devices = mic.get_available_devices()
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']}")
    
    # 録音テスト（5秒間）
    print("録音を開始します（5秒間）...")
    mic.start_recording()
    
    # 5秒間音声を処理
    start_time = time.time()
    while time.time() - start_time < 5:
        audio_chunk = mic.get_audio_chunk()
        if audio_chunk is not None:
            # 音声データの処理（ここではデータの形状を表示）
            print(f"音声チャンク取得: 形状={audio_chunk.shape}, 最大値={np.max(audio_chunk):.2f}")
        time.sleep(0.1)
    
    # 録音停止
    mic.stop_recording()
    print("録音を停止しました")
