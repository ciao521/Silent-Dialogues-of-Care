"""
音声感情分析モジュール
Hume AI EVI 2 APIを使用
"""
import os
import numpy as np
import tempfile
import soundfile as sf
from loguru import logger
from hume import HumeBatchClient
from hume.models.config import ProsodyConfig

class HumeEviAnalyzer:
    def __init__(self, config, api_key=None):
        """
        Hume AI EVI 2音声感情分析モジュールの初期化
        
        Args:
            config (dict): 設定ファイルから読み込んだ音声感情分析設定
            api_key (str, optional): Hume AI APIキー。Noneの場合は環境変数から読み込む
        """
        # APIキーの設定
        self.api_key = api_key or os.environ.get("HUME_API_KEY")
        if not self.api_key:
            logger.error("Hume AI APIキーが設定されていません")
            raise ValueError("Hume AI APIキーが必要です。環境変数HUME_API_KEYを設定するか、初期化時にapi_keyを指定してください")
        
        # Hume API クライアント初期化
        self.client = HumeBatchClient(self.api_key)
        
        # 設定
        self.sample_rate = config.get('sample_rate', 44100)
        
        # 音声感情カテゴリ（Hume AIの感情モデルに基づく）
        self.emotion_categories = [
            "Amusement", "Awe", "Concentration", "Contentment", "Desire",
            "Disappointment", "Doubt", "Elation", "Interest", "Pain",
            "Sadness", "Surprise", "Tiredness", "Triumph"
        ]
        
        logger.info("HumeEviAnalyzerを初期化しました")
    
    async def analyze_emotion(self, audio_data):
        """
        音声データから感情を分析
        
        Args:
            audio_data (numpy.ndarray): 分析する音声データ
            
        Returns:
            dict: 感情分析結果
        """
        if len(audio_data) == 0:
            logger.warning("分析する音声データがありません")
            return self._empty_result()
        
        try:
            # 音声データを一時ファイルに保存
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # WAVファイルとして保存
            sf.write(temp_filename, audio_data, self.sample_rate)
            
            # Hume API設定
            config = ProsodyConfig()
            
            # Hume APIで感情分析
            with open(temp_filename, 'rb') as file:
                file_data = file.read()
            
            job_id = await self.client.submit_job(
                files=[("file", ("audio.wav", file_data, "audio/wav"))],
                configs=[config]
            )
            
            # ジョブの完了を待機
            job_result = await self.client.get_job_predictions(job_id)
            predictions = job_result
            
            # 一時ファイルを削除
            try:
                os.unlink(temp_filename)
            except Exception as e:
                logger.warning(f"一時ファイルの削除に失敗: {e}")
            
            # 結果を解析
            prosody_predictions = predictions.get('prosody')
            if not prosody_predictions:
                logger.warning("Hume APIから音声感情予測が返されませんでした")
                return self._empty_result()
            
            # 最初の（または唯一の）予測結果を取得
            prediction = prosody_predictions[0]
            emotions = prediction.get('emotions', {})
            
            # 感情スコアを抽出
            emotion_scores = {}
            for emotion in self.emotion_categories:
                emotion_scores[emotion.lower()] = emotions.get(emotion, {}).get('score', 0.0)
            
            # 感情の主要次元（ポジティブ/ネガティブ、活性度）を計算
            positivity = (
                emotion_scores.get('amusement', 0) +
                emotion_scores.get('awe', 0) +
                emotion_scores.get('contentment', 0) +
                emotion_scores.get('elation', 0) +
                emotion_scores.get('interest', 0) +
                emotion_scores.get('triumph', 0)
            ) / 6
            
            negativity = (
                emotion_scores.get('disappointment', 0) +
                emotion_scores.get('doubt', 0) +
                emotion_scores.get('pain', 0) +
                emotion_scores.get('sadness', 0)
            ) / 4
            
            activation = (
                emotion_scores.get('amusement', 0) +
                emotion_scores.get('elation', 0) +
                emotion_scores.get('surprise', 0) +
                emotion_scores.get('triumph', 0)
            ) / 4
            
            # 最も強い感情を特定
            max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            
            result = {
                'emotion_scores': emotion_scores,
                'primary_emotion': max_emotion[0],
                'primary_score': max_emotion[1],
                'positivity': positivity,
                'negativity': negativity,
                'activation': activation,
                'valence': positivity - negativity,  # 感情価（ポジティブ-ネガティブ）
                'raw_prediction': prediction  # デバッグ用の生データ
            }
            
            logger.info(f"音声感情分析完了: 主要感情={result['primary_emotion']}({result['primary_score']:.2f}), 感情価={result['valence']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"音声感情分析中にエラーが発生: {e}")
            result = self._empty_result()
            result["error"] = f"音声感情分析中にエラーが発生しました: {e}"
            return result
    
    def _empty_result(self):
        """空の結果を返す（エラー時用）"""
        emotion_scores = {emotion.lower(): 0.0 for emotion in self.emotion_categories}
        return {
            'emotion_scores': emotion_scores,
            'primary_emotion': 'neutral',
            'primary_score': 0.0,
            'positivity': 0.0,
            'negativity': 0.0,
            'activation': 0.0,
            'valence': 0.0,
            'raw_prediction': None
        }
        
    def normalize_emotion_scores(self, emotion_scores):
        """
        感情スコアを正規化する（合計が1になるように）
        
        Args:
            emotion_scores (list): 感情スコアのリスト [{"name": str, "score": float}, ...]
            
        Returns:
            list: 正規化された感情スコアのリスト
        """
        if not emotion_scores:
            return []
            
        # 合計を計算
        total = sum(item["score"] for item in emotion_scores)
        
        # 正規化
        if total > 0:
            return [{"name": item["name"], "score": item["score"] / total} for item in emotion_scores]
        else:
            return emotion_scores
            
    def format_result(self, emotion_scores):
        """
        感情スコアを結果形式にフォーマットする
        
        Args:
            emotion_scores (list): 感情スコアのリスト [{"name": str, "score": float}, ...]
            
        Returns:
            dict: フォーマットされた結果
        """
        # 結果辞書を初期化
        result = {
            "emotions": [],
            "dominant_emotion": "neutral",
            "emotion_vector": [0.0] * len(self.emotion_categories)
        }
        
        # 感情スコアがない場合は空の結果を返す
        if not emotion_scores:
            return result
            
        # 感情スコアをリストにコピー
        result["emotions"] = emotion_scores.copy()
        
        # 最も強い感情を特定
        max_emotion = max(emotion_scores, key=lambda x: x["score"], default={"name": "neutral", "score": 0.0})
        result["dominant_emotion"] = max_emotion["name"]
        
        # 感情ベクトルを作成
        emotion_dict = {item["name"]: item["score"] for item in emotion_scores}
        for i, category in enumerate(self.emotion_categories):
            result["emotion_vector"][i] = emotion_dict.get(category, 0.0)
            
        return result


# テスト用コード
if __name__ == "__main__":
    import asyncio
    import sounddevice as sd
    
    # テスト設定
    test_config = {
        'sample_rate': 44100
    }
    
    # APIキーが環境変数に設定されていることを確認
    if not os.environ.get("HUME_API_KEY"):
        print("テストにはHUME_API_KEY環境変数が必要です")
        exit(1)
    
    # 感情分析モジュールの初期化
    analyzer = HumeEviAnalyzer(test_config)
    
    # 5秒間の音声録音
    duration = 5  # 秒
    print(f"{duration}秒間の音声を録音します。感情的な表現で何か話してください...")
    
    recording = sd.rec(
        int(duration * test_config['sample_rate']),
        samplerate=test_config['sample_rate'],
        channels=1
    )
    sd.wait()  # 録音完了まで待機
    
    print("録音完了。感情分析を実行します...")
    
    # 感情分析実行
    async def run_analysis():
        result = await analyzer.analyze_emotion(recording)
        print(f"感情分析結果:")
        print(f"主要感情: {result['primary_emotion']} (スコア: {result['primary_score']:.2f})")
        print(f"感情価 (Valence): {result['valence']:.2f}")
        print(f"活性度 (Activation): {result['activation']:.2f}")
        print("\n詳細感情スコア:")
        for emotion, score in result['emotion_scores'].items():
            print(f"  {emotion}: {score:.2f}")
    
    # 非同期関数を実行
    asyncio.run(run_analysis())
