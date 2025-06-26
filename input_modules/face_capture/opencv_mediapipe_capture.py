"""
カメラからの表情キャプチャを処理するモジュール
OpenCVとMediaPipeを使用して顔のランドマークを抽出
"""
import cv2
import mediapipe as mp
import numpy as np
import threading
import queue
import time
from loguru import logger

class FaceCaptureHandler:
    def __init__(self, config):
        """
        顔キャプチャハンドラの初期化
        
        Args:
            config (dict): 設定ファイルから読み込んだビデオ入力設定
        """
        self.device_id = config.get('device_id', 0)
        self.width = config.get('width', 640)
        self.height = config.get('height', 480)
        self.fps = config.get('fps', 30)
        
        # MediaPipe Faceモジュール設定
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
        
        # 顔メッシュ検出器（シンプルな設定に変更）
        try:
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        except Exception as e:
            logger.error(f"MediaPipe FaceMeshの初期化に失敗: {e}")
            # フォールバックオプション: より単純な設定で試す
            try:
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    max_num_faces=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            except Exception as e:
                logger.error(f"フォールバックMediaPipe FaceMeshの初期化にも失敗: {e}")
                self.face_mesh = None
        
        # 顔データを保存するキュー
        self.face_queue = queue.Queue()
        self.frame_queue = queue.Queue()
        
        # キャプチャ状態の管理
        self.is_capturing = False
        self.capture_thread = None
        self.cap = None
        
        logger.info(f"顔キャプチャハンドラを初期化: デバイスID={self.device_id}, 解像度={self.width}x{self.height}")
    
    def start_capture(self):
        """顔キャプチャを開始"""
        if self.is_capturing:
            logger.warning("顔キャプチャはすでに開始されています")
            return
            
        # カメラキャプチャの初期化
        self.cap = cv2.VideoCapture(self.device_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        if not self.cap.isOpened():
            logger.error(f"カメラ（デバイスID: {self.device_id}）を開けませんでした")
            return
        
        self.is_capturing = True
        self.capture_thread = threading.Thread(target=self._capture_face)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        logger.info("顔キャプチャを開始しました")
    
    def stop_capture(self):
        """顔キャプチャを停止"""
        self.is_capturing = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
            self.capture_thread = None
        
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
        
        logger.info("顔キャプチャを停止しました")
    
    def _capture_face(self):
        """バックグラウンドで顔をキャプチャし、キューに追加するスレッド関数"""
        while self.is_capturing and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("カメラからのフレーム取得に失敗しました")
                    time.sleep(0.1)
                    continue
                
                # 画像をRGBに変換（MediaPipeはRGBを使用）
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 顔データの初期設定
                face_data = {
                    'image': frame.copy(),
                    'landmarks': None,
                    'timestamp': time.time()
                }
                
                # 顔のランドマークを検出（MediaPipeが初期化されている場合のみ）
                if self.face_mesh:
                    try:
                        results = self.face_mesh.process(rgb_frame)
                        
                        if results.multi_face_landmarks:
                            # 最初に検出された顔のランドマークを使用
                            face_landmarks = results.multi_face_landmarks[0]
                            # ランドマークを辞書のリストに変換
                            landmarks_list = [
                                {'x': lm.x, 'y': lm.y, 'z': lm.z}
                                for lm in face_landmarks.landmark
                            ]
                            face_data['landmarks'] = landmarks_list
                            
                            # デバッグ用の描画（顔のランドマークを表示）
                            debug_frame = frame.copy()
                            self.mp_drawing.draw_landmarks(
                                debug_frame,
                                face_landmarks,
                                self.mp_face_mesh.FACEMESH_CONTOURS,
                                self.drawing_spec,
                                self.drawing_spec
                            )
                            self.frame_queue.put(debug_frame)
                        else:
                            self.frame_queue.put(frame)
                    except Exception as e:
                        logger.error(f"顔ランドマーク処理中にエラー発生: {e}")
                        self.frame_queue.put(frame)
                else:
                    # MediaPipeが初期化されていない場合は、生のフレームを使用
                    self.frame_queue.put(frame)
                
                # 顔データをキューに追加
                self.face_queue.put(face_data)
                
                # フレームレート調整
                time.sleep(1/self.fps)
                
            except Exception as e:
                logger.error(f"顔キャプチャ中にエラーが発生: {e}")
                time.sleep(0.1)
    
    def get_face_data(self, timeout=0.1):
        """
        キューから顔データを取得
        
        Args:
            timeout (float): キューからの取得タイムアウト時間（秒）
            
        Returns:
            dict or None: 顔データ（タイムアウト時はNone）
        """
        try:
            return self.face_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_debug_frame(self, timeout=0.1):
        """
        デバッグ用のフレームを取得
        
        Args:
            timeout (float): キューからの取得タイムアウト時間（秒）
            
        Returns:
            numpy.ndarray or None: デバッグフレーム（タイムアウト時はNone）
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def __del__(self):
        """クリーンアップ処理"""
        try:
            self.stop_capture()
            if hasattr(self, 'face_mesh') and self.face_mesh:
                self.face_mesh.close()
        except Exception as e:
            logger.error(f"顔キャプチャハンドラのクリーンアップ中にエラー: {e}")


# テスト用コード
if __name__ == "__main__":
    # テスト設定
    test_config = {
        'device_id': 0,
        'width': 640,
        'height': 480,
        'fps': 30
    }
    
    # 顔キャプチャハンドラの初期化
    face_capture = FaceCaptureHandler(test_config)
    
    # キャプチャ開始
    face_capture.start_capture()
    
    # ウィンドウ作成
    cv2.namedWindow("Face Landmarks", cv2.WINDOW_NORMAL)
    
    try:
        # キャプチャしたフレームを表示（30秒間）
        start_time = time.time()
        while time.time() - start_time < 30:
            frame = face_capture.get_debug_frame()
            if frame is not None:
                cv2.imshow("Face Landmarks", frame)
            
            face_data = face_capture.get_face_data(timeout=0.01)
            if face_data and face_data['landmarks'] is not None:
                print(f"顔ランドマーク検出: 点数={len(face_data['landmarks'])}")
            
            # 'q'キーで終了
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        # クリーンアップ
        face_capture.stop_capture()
        cv2.destroyAllWindows()
        print("キャプチャを停止しました")
