"""
表情感情分析モジュール
MediaPipe Face Landmarkからの特徴抽出とONNXモデルによる感情分類
"""
import os
import numpy as np
import cv2
import onnxruntime as ort
from loguru import logger

class FacialEmotionRecognizer:
    def __init__(self, config):
        """
        表情感情認識モジュールの初期化
        
        Args:
            config (dict): 設定ファイルから読み込んだ表情感情分析設定
        """
        self.model_path = config.get('model_path', 'models/facial_emotion_classifier.onnx')
        
        # モデルの存在確認
        if not os.path.exists(self.model_path):
            logger.warning(f"感情分類モデルが見つかりません: {self.model_path}")
            logger.warning("デモモードで実行します（ランダムな感情値を返します）")
            self.demo_mode = True
        else:
            self.demo_mode = False
            # ONNXランタイムセッション初期化
            self.session = ort.InferenceSession(self.model_path)
            logger.info(f"感情分類モデルを読み込みました: {self.model_path}")
        
        # 感情クラス
        self.emotion_classes = ['neutral', 'happy', 'sad', 'surprise', 'fear', 'anger', 'disgust', 'contempt']
        
        # 感情の主要次元（ポジティブ/ネガティブ、活性度）の対応マッピング
        self.emotion_dimensions = {
            'neutral': {'valence': 0.0, 'activation': 0.0},
            'happy': {'valence': 0.8, 'activation': 0.6},
            'sad': {'valence': -0.7, 'activation': -0.4},
            'surprise': {'valence': 0.2, 'activation': 0.8},
            'fear': {'valence': -0.7, 'activation': 0.7},
            'anger': {'valence': -0.8, 'activation': 0.8},
            'disgust': {'valence': -0.6, 'activation': 0.2},
            'contempt': {'valence': -0.5, 'activation': -0.2}
        }
        
        logger.info("FacialEmotionRecognizerを初期化しました")
    
    def extract_features(self, face_landmarks):
        """
        顔のランドマークから特徴を抽出
        
        Args:
            face_landmarks (numpy.ndarray): MediaPipeで検出された顔のランドマーク
            
        Returns:
            numpy.ndarray: モデル入力用の特徴ベクトル
        """
        if face_landmarks is None:
            return None
        
        # MediaPipeの顔ランドマークから重要な特徴点を抽出
        # 以下は簡略化した例で、実際には顔の動きをより詳細に捉える特徴が必要
        features = []
        
        try:
            # 顔の重要な部位（目、眉、口、鼻など）の相対位置を特徴として抽出
            
            # 基準点（顔の中心）
            face_center = np.mean(face_landmarks, axis=0)
            
            # 正規化のための顔のサイズ（縦横の最大距離）
            face_width = np.max(face_landmarks[:, 0]) - np.min(face_landmarks[:, 0])
            face_height = np.max(face_landmarks[:, 1]) - np.min(face_landmarks[:, 1])
            face_size = max(face_width, face_height)
            
            # 重要なランドマークインデックス
            # MediaPipe Face Meshの場合の例（実際のモデルに合わせて調整が必要）
            # 目のランドマーク
            left_eye_indices = [33, 133, 160, 159, 158, 144, 153, 157]  # 左目の周囲
            right_eye_indices = [362, 263, 386, 385, 384, 381, 374, 373]  # 右目の周囲
            
            # 眉のランドマーク
            left_eyebrow_indices = [70, 63, 105, 66, 107]  # 左眉
            right_eyebrow_indices = [336, 296, 334, 293, 300]  # 右眉
            
            # 口のランドマーク
            mouth_indices = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409]  # 口の周囲
            
            # 特徴抽出（各ランドマークの相対位置）
            for idx_list in [left_eye_indices, right_eye_indices, left_eyebrow_indices, right_eyebrow_indices, mouth_indices]:
                for idx in idx_list:
                    if idx < len(face_landmarks):
                        # 顔の中心からの相対位置を正規化
                        rel_pos = (face_landmarks[idx] - face_center) / face_size
                        features.extend(rel_pos[:2])  # X, Y座標のみ使用（Zは省略可能）
            
            # 目の開き具合（上下のまぶたの距離）
            if all(idx < len(face_landmarks) for idx in [159, 145]):  # 左目
                left_eye_openness = np.linalg.norm(face_landmarks[159] - face_landmarks[145]) / face_size
                features.append(left_eye_openness)
            
            if all(idx < len(face_landmarks) for idx in [386, 374]):  # 右目
                right_eye_openness = np.linalg.norm(face_landmarks[386] - face_landmarks[374]) / face_size
                features.append(right_eye_openness)
            
            # 口の開き具合（上下の唇の距離）
            if all(idx < len(face_landmarks) for idx in [13, 14]):
                mouth_openness = np.linalg.norm(face_landmarks[13] - face_landmarks[14]) / face_size
                features.append(mouth_openness)
            
            # 必要に応じて他の特徴を追加
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"特徴抽出中にエラーが発生: {e}")
            return None
    
    def predict_emotion(self, face_data):
        """
        顔データから感情を予測
        
        Args:
            face_data (dict): 顔のデータ（'landmarks'キーに顔のランドマークが含まれる）
            
        Returns:
            dict: 感情予測結果
        """
        if face_data is None or 'landmarks' not in face_data or face_data['landmarks'] is None:
            logger.warning("顔のランドマークが見つかりません")
            return self._empty_result()
        
        try:
            if self.demo_mode:
                # デモモード：ランダムな感情値を生成
                return self._generate_demo_result()
            
            # 特徴抽出
            features = self.extract_features(face_data['landmarks'])
            if features is None:
                logger.warning("特徴抽出に失敗しました")
                return self._empty_result()
            
            # 特徴の形状をモデルの入力形式に合わせる
            features = features.reshape(1, -1)  # バッチサイズ1
            
            # ONNXモデルで予測
            input_name = self.session.get_inputs()[0].name
            output_name = self.session.get_outputs()[0].name
            prediction = self.session.run([output_name], {input_name: features})[0]
            
            # 予測結果の処理
            emotion_scores = prediction[0]
            
            # 各感情クラスのスコア
            emotion_dict = {self.emotion_classes[i]: float(score) for i, score in enumerate(emotion_scores)}
            
            # 最も確率の高い感情
            max_idx = np.argmax(emotion_scores)
            primary_emotion = self.emotion_classes[max_idx]
            primary_score = float(emotion_scores[max_idx])
            
            # 感情の主要次元（ポジティブ/ネガティブ、活性度）を計算
            valence = 0
            activation = 0
            total_weight = 0
            
            for emotion, score in emotion_dict.items():
                if score > 0:
                    valence += self.emotion_dimensions[emotion]['valence'] * score
                    activation += self.emotion_dimensions[emotion]['activation'] * score
                    total_weight += score
            
            if total_weight > 0:
                valence /= total_weight
                activation /= total_weight
            
            result = {
                'emotion_scores': emotion_dict,
                'primary_emotion': primary_emotion,
                'primary_score': primary_score,
                'valence': valence,
                'activation': activation,
                'is_demo': False
            }
            
            logger.info(f"表情感情分析完了: 主要感情={result['primary_emotion']}({result['primary_score']:.2f}), 感情価={result['valence']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"感情予測中にエラーが発生: {e}")
            return self._empty_result()
    
    def _empty_result(self):
        """空の結果を返す（エラー時用）"""
        emotion_dict = {emotion: 0.0 for emotion in self.emotion_classes}
        emotion_dict['neutral'] = 1.0  # デフォルトはニュートラル
        
        return {
            'emotion_scores': emotion_dict,
            'primary_emotion': 'neutral',
            'primary_score': 1.0,
            'valence': 0.0,
            'activation': 0.0,
            'is_demo': False
        }
    
    def _generate_demo_result(self):
        """デモモード用のランダムな結果を生成"""
        # ランダムなスコアを生成
        random_scores = np.random.rand(len(self.emotion_classes))
        random_scores = random_scores / np.sum(random_scores)  # 合計が1になるように正規化
        
        emotion_dict = {self.emotion_classes[i]: float(score) for i, score in enumerate(random_scores)}
        
        # 最も確率の高い感情
        max_idx = np.argmax(random_scores)
        primary_emotion = self.emotion_classes[max_idx]
        primary_score = float(random_scores[max_idx])
        
        # 感情の主要次元（ポジティブ/ネガティブ、活性度）を計算
        valence = 0
        activation = 0
        
        for emotion, score in emotion_dict.items():
            valence += self.emotion_dimensions[emotion]['valence'] * score
            activation += self.emotion_dimensions[emotion]['activation'] * score
        
        result = {
            'emotion_scores': emotion_dict,
            'primary_emotion': primary_emotion,
            'primary_score': primary_score,
            'valence': valence,
            'activation': activation,
            'is_demo': True
        }
        
        logger.info(f"デモモード - ランダム感情生成: 主要感情={result['primary_emotion']}({result['primary_score']:.2f})")
        
        return result


# テスト用コード
if __name__ == "__main__":
    import time
    import mediapipe as mp
    
    # テスト設定
    test_config = {
        'model_path': 'models/facial_emotion_classifier.onnx'  # モデルがなくてもデモモードで動作
    }
    
    # 表情感情認識モジュールの初期化
    recognizer = FacialEmotionRecognizer(test_config)
    
    # MediaPipe Face Meshの初期化
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    # カメラキャプチャの初期化
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("カメラを開けませんでした")
        exit(1)
    
    # ウィンドウ作成
    cv2.namedWindow("Facial Emotion", cv2.WINDOW_NORMAL)
    
    try:
        while True:
            # フレーム取得
            ret, frame = cap.read()
            if not ret:
                break
            
            # MediaPipeで顔のランドマークを検出
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            face_data = {
                'frame': frame,
                'landmarks': None,
                'timestamp': time.time()
            }
            
            if results.multi_face_landmarks:
                # 最初に検出された顔のランドマークを使用
                face_landmarks = results.multi_face_landmarks[0]
                
                # ランドマークを配列に変換
                h, w, _ = frame.shape
                landmarks_array = np.array([
                    [lm.x * w, lm.y * h, lm.z]
                    for lm in face_landmarks.landmark
                ])
                
                face_data['landmarks'] = landmarks_array
                
                # 感情予測
                emotion_result = recognizer.predict_emotion(face_data)
                
                # 予測結果をフレームに表示
                primary_emotion = emotion_result['primary_emotion']
                primary_score = emotion_result['primary_score']
                valence = emotion_result['valence']
                activation = emotion_result['activation']
                
                # 表示テキスト
                text_lines = [
                    f"感情: {primary_emotion} ({primary_score:.2f})",
                    f"感情価: {valence:.2f}",
                    f"活性度: {activation:.2f}"
                ]
                
                # テキストをフレームに描画
                y_offset = 30
                for i, line in enumerate(text_lines):
                    cv2.putText(
                        frame, line, (10, y_offset + i * 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
                    )
                
                if emotion_result['is_demo']:
                    cv2.putText(
                        frame, "デモモード", (10, y_offset + len(text_lines) * 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
                    )
            
            # フレーム表示
            cv2.imshow("Facial Emotion", frame)
            
            # 'q'キーで終了
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        # クリーンアップ
        cap.release()
        face_mesh.close()
        cv2.destroyAllWindows()
        print("終了しました")
