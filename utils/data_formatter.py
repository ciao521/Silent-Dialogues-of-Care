"""
ユーティリティモジュール - 共通関数とヘルパークラス
"""
import os
import json
import time
import numpy as np
from loguru import logger

class DataFormatter:
    """
    データ形式変換ユーティリティクラス
    異なるモジュール間でのデータ形式の変換をサポート
    """
    
    @staticmethod
    def audio_to_bytes(audio_data, sample_rate=44100, channels=1, sample_width=2):
        """
        NumPy配列のオーディオデータをバイト列に変換
        
        Args:
            audio_data (numpy.ndarray): 変換するオーディオデータ
            sample_rate (int): サンプルレート（Hz）
            channels (int): チャンネル数
            sample_width (int): サンプル幅（バイト単位）
            
        Returns:
            bytes: バイト列に変換されたオーディオデータ
        """
        try:
            # float32からint16に変換（APIによってはint16が必要）
            if audio_data.dtype == np.float32:
                # [-1.0, 1.0]の範囲を[-32768, 32767]に変換
                audio_data = (audio_data * 32767).astype(np.int16)
            
            return audio_data.tobytes()
        except Exception as e:
            logger.error(f"オーディオデータのバイト変換中にエラー: {e}")
            return b''
    
    @staticmethod
    def emotion_to_json(emotion_data):
        """
        感情データをJSON形式に変換
        
        Args:
            emotion_data (dict): 感情データ
            
        Returns:
            str: JSON形式の感情データ
        """
        try:
            # NumPy配列をリストに変換（JSONシリアライズ可能にするため）
            cleaned_data = {}
            
            for key, value in emotion_data.items():
                if isinstance(value, np.ndarray):
                    cleaned_data[key] = value.tolist()
                elif isinstance(value, np.float32) or isinstance(value, np.float64):
                    cleaned_data[key] = float(value)
                elif isinstance(value, np.int32) or isinstance(value, np.int64):
                    cleaned_data[key] = int(value)
                elif isinstance(value, dict):
                    cleaned_data[key] = DataFormatter.emotion_to_json(value)
                else:
                    cleaned_data[key] = value
            
            return json.dumps(cleaned_data, ensure_ascii=False)
        except Exception as e:
            logger.error(f"感情データのJSON変換中にエラー: {e}")
            return '{}'
    
    @staticmethod
    def flatten_emotion_data(emotion_data):
        """
        階層的な感情データを平坦化（データベース保存用）
        
        Args:
            emotion_data (dict): 感情データ
            
        Returns:
            dict: 平坦化された感情データ
        """
        flattened = {}
        
        # 主要感情情報
        flattened['primary_emotion'] = emotion_data.get('primary_emotion', 'neutral')
        flattened['confidence'] = emotion_data.get('confidence', 0.0)
        flattened['valence'] = emotion_data.get('valence', 0.0)
        flattened['activation'] = emotion_data.get('activation', 0.0)
        
        # モダリティ別の寄与（存在する場合）
        if 'vocal_contribution' in emotion_data:
            vocal = emotion_data['vocal_contribution']
            flattened['vocal_emotion'] = vocal.get('emotion', 'unknown')
            flattened['vocal_score'] = vocal.get('score', 0.0)
            flattened['vocal_weight'] = vocal.get('weight', 0.0)
        
        if 'facial_contribution' in emotion_data:
            facial = emotion_data['facial_contribution']
            flattened['facial_emotion'] = facial.get('emotion', 'unknown')
            flattened['facial_score'] = facial.get('score', 0.0)
            flattened['facial_weight'] = facial.get('weight', 0.0)
        
        # タイムスタンプ
        flattened['timestamp'] = time.time()
        
        return flattened


class EmotionColorMapper:
    """
    感情から色へのマッピングユーティリティクラス
    """
    
    # 感情カテゴリと色のマッピング（RGB値、0-255）
    EMOTION_COLORS = {
        'neutral': (128, 128, 128),
        'happy': (255, 223, 0),
        'sad': (0, 102, 204),
        'surprise': (255, 0, 255),
        'fear': (102, 0, 102),
        'anger': (255, 0, 0),
        'disgust': (0, 102, 0),
        'contempt': (85, 85, 0),
        'interest': (0, 204, 255),
        'amusement': (255, 170, 0),
        'awe': (170, 0, 255),
        'contentment': (0, 170, 136),
        'desire': (255, 102, 0),
        'disappointment': (102, 68, 0),
        'doubt': (119, 119, 119),
        'elation': (255, 255, 0),
        'pain': (153, 0, 0),
        'tiredness': (68, 85, 102),
        'triumph': (255, 221, 0)
    }
    
    @staticmethod
    def get_color(emotion, format='rgb'):
        """
        感情に対応する色を取得
        
        Args:
            emotion (str): 感情カテゴリ
            format (str): 出力形式（'rgb', 'hex', 'normalized'）
            
        Returns:
            tuple/str: 指定された形式の色
        """
        # デフォルトの色（ニュートラル）
        default_color = EmotionColorMapper.EMOTION_COLORS.get('neutral')
        
        # 指定された感情の色を取得
        color_rgb = EmotionColorMapper.EMOTION_COLORS.get(emotion.lower(), default_color)
        
        # 要求された形式に変換
        if format == 'rgb':
            return color_rgb
        elif format == 'hex':
            return '#{:02x}{:02x}{:02x}'.format(*color_rgb)
        elif format == 'normalized':
            return tuple(c / 255.0 for c in color_rgb)
        else:
            return color_rgb
    
    @staticmethod
    def interpolate_color(valence, activation):
        """
        感情価（valence）と活性度（activation）に基づいて色を補間
        
        Args:
            valence (float): 感情価（-1.0〜1.0）
            activation (float): 活性度（-1.0〜1.0）
            
        Returns:
            tuple: RGB色（0-255）
        """
        # 感情次元から色への変換マトリックス
        # 第1象限（ポジティブ・高活性）: 黄色系
        # 第2象限（ネガティブ・高活性）: 赤色系
        # 第3象限（ネガティブ・低活性）: 青色系
        # 第4象限（ポジティブ・低活性）: 緑色系
        
        # 値の範囲を確認
        valence = max(-1.0, min(1.0, valence))
        activation = max(-1.0, min(1.0, activation))
        
        if valence >= 0 and activation >= 0:
            # 第1象限（ポジティブ・高活性）: 黄色系
            r = 255
            g = int(128 + 127 * valence)
            b = int(128 - 128 * activation)
        elif valence < 0 and activation >= 0:
            # 第2象限（ネガティブ・高活性）: 赤色系
            r = 255
            g = int(128 - 128 * abs(valence))
            b = int(128 - 128 * activation)
        elif valence < 0 and activation < 0:
            # 第3象限（ネガティブ・低活性）: 青色系
            r = int(128 - 128 * abs(valence))
            g = int(128 - 128 * abs(activation))
            b = 255
        else:
            # 第4象限（ポジティブ・低活性）: 緑色系
            r = int(128 - 128 * abs(activation))
            g = 255
            b = int(128 - 128 * valence)
        
        return (r, g, b)


# テスト用コード
if __name__ == "__main__":
    # データフォーマッタのテスト
    print("データフォーマッタのテスト:")
    
    # オーディオ変換テスト
    audio_data = np.random.uniform(-1, 1, 44100).astype(np.float32)  # 1秒のランダムオーディオ
    audio_bytes = DataFormatter.audio_to_bytes(audio_data)
    print(f"オーディオバイト長: {len(audio_bytes)} バイト")
    
    # 感情データJSON変換テスト
    test_emotion = {
        'primary_emotion': 'happy',
        'confidence': np.float32(0.85),
        'valence': np.float32(0.7),
        'activation': np.float32(0.6),
        'scores': np.array([0.1, 0.85, 0.05]),
        'vocal_contribution': {
            'emotion': 'happy',
            'score': np.float32(0.9)
        }
    }
    
    json_emotion = DataFormatter.emotion_to_json(test_emotion)
    print(f"JSON感情データ: {json_emotion}")
    
    # 感情色マッパーのテスト
    print("\n感情色マッパーのテスト:")
    
    emotions = ['happy', 'sad', 'anger', 'fear', 'neutral']
    for emotion in emotions:
        rgb = EmotionColorMapper.get_color(emotion, 'rgb')
        hex_color = EmotionColorMapper.get_color(emotion, 'hex')
        norm = EmotionColorMapper.get_color(emotion, 'normalized')
        print(f"{emotion}: RGB={rgb}, HEX={hex_color}, 正規化={norm}")
    
    # 感情次元から色への補間テスト
    test_points = [
        (0.8, 0.7, "高ポジティブ・高活性"),
        (-0.7, 0.8, "高ネガティブ・高活性"),
        (-0.6, -0.5, "中ネガティブ・中低活性"),
        (0.5, -0.6, "中ポジティブ・中低活性"),
        (0.0, 0.0, "ニュートラル")
    ]
    
    print("\n感情次元からの色補間テスト:")
    for valence, activation, label in test_points:
        color = EmotionColorMapper.interpolate_color(valence, activation)
        hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
        print(f"{label} (valence={valence}, activation={activation}): RGB={color}, HEX={hex_color}")
