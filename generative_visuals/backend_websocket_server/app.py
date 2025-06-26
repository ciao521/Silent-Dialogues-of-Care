"""
WebSocketサーバー
AI処理結果をThree.jsフロントエンドへリアルタイム送信
FastAPIとwebsocketsを使用
"""
import asyncio
import json
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

class WebSocketServer:
    def __init__(self, config):
        """
        WebSocketサーバーの初期化
        
        Args:
            config (dict): 設定ファイルから読み込んだWebSocket設定
        """
        self.host = config.get('host', '127.0.0.1')
        self.port = config.get('port', 8765)
        
        # FastAPIアプリケーション
        self.app = FastAPI(title="Silent Dialogues of Care - WebSocket Server")
        
        # CORSミドルウェア
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 本番環境では適切なオリジンを指定
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 静的ファイル（フロントエンド）のホスティング
        try:
            self.app.mount("/", StaticFiles(directory="generative_visuals/frontend", html=True), name="static")
            logger.info("フロントエンドファイルをマウントしました")
        except Exception as e:
            logger.warning(f"フロントエンドファイルのマウント中にエラー: {e}")
        
        # WebSocketクライアント接続の管理
        self.active_connections = []
        
        # WebSocketエンドポイントの設定
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.connect(websocket)
            try:
                while True:
                    # クライアントからのメッセージを受信（オプション）
                    data = await websocket.receive_text()
                    # 単純なエコーレスポンス
                    await websocket.send_text(f"Echo: {data}")
            except WebSocketDisconnect:
                self.disconnect(websocket)
        
        logger.info(f"WebSocketサーバーを初期化: {self.host}:{self.port}")
    
    async def connect(self, websocket: WebSocket):
        """
        WebSocket接続を確立
        
        Args:
            websocket (WebSocket): 接続するWebSocketインスタンス
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"新しいWebSocket接続: 現在の接続数={len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """
        WebSocket接続を切断
        
        Args:
            websocket (WebSocket): 切断するWebSocketインスタンス
        """
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket接続が切断されました: 残り接続数={len(self.active_connections)}")
    
    async def broadcast(self, data):
        """
        すべての接続済みWebSocketクライアントにデータをブロードキャスト
        
        Args:
            data (dict): 送信するデータ（JSON形式に変換される）
        """
        if not self.active_connections:
            logger.debug("アクティブなWebSocket接続がありません")
            return
        
        # データをJSON文字列に変換
        json_data = json.dumps(data)
        
        # 接続済みの各クライアントにデータを送信
        for connection in self.active_connections:
            try:
                await connection.send_text(json_data)
            except Exception as e:
                logger.error(f"データ送信中にエラーが発生: {e}")
    
    async def send_emotion_data(self, emotion_data, text_data=None, response=None):
        """
        感情データをWebSocketクライアントに送信
        
        Args:
            emotion_data (dict): 送信する感情データ
            text_data (dict, optional): 送信するテキストデータ（発話内容など）
            response (dict, optional): LLMの応答データ
        """
        # 送信データの構築
        data = {
            'type': 'emotion_update',
            'timestamp': asyncio.get_event_loop().time(),
            'emotion': emotion_data
        }
        
        if text_data:
            data['text'] = text_data
        
        if response:
            data['response'] = response
        
        # データをブロードキャスト
        await self.broadcast(data)
        logger.debug(f"感情データをブロードキャスト: {emotion_data.get('primary_emotion', 'unknown')}")
    
    async def send_message(self, message_type, content):
        """
        任意のメッセージをWebSocketクライアントに送信
        
        Args:
            message_type (str): メッセージタイプ
            content (dict): メッセージの内容
        """
        data = {
            'type': message_type,
            'timestamp': asyncio.get_event_loop().time(),
            'content': content
        }
        
        await self.broadcast(data)
        logger.debug(f"メッセージをブロードキャスト: タイプ={message_type}")
    
    def run(self):
        """WebSocketサーバーを起動"""
        uvicorn.run(self.app, host=self.host, port=self.port)
    
    async def run_async(self):
        """WebSocketサーバーを非同期で起動（別のイベントループで実行する場合）"""
        config = uvicorn.Config(self.app, host=self.host, port=self.port)
        server = uvicorn.Server(config)
        await server.serve()


# テスト用コード
if __name__ == "__main__":
    import time
    
    # テスト設定
    test_config = {
        'host': '127.0.0.1',
        'port': 8765
    }
    
    # WebSocketサーバーの初期化
    server = WebSocketServer(test_config)
    
    # テスト用のデータ送信関数
    async def send_test_data():
        # サーバー起動から5秒待機（クライアント接続のため）
        await asyncio.sleep(5)
        
        # テスト用の感情データ
        test_emotions = [
            {'primary_emotion': 'happy', 'valence': 0.8, 'activation': 0.6},
            {'primary_emotion': 'sad', 'valence': -0.7, 'activation': -0.4},
            {'primary_emotion': 'surprise', 'valence': 0.2, 'activation': 0.8},
            {'primary_emotion': 'anger', 'valence': -0.8, 'activation': 0.8},
            {'primary_emotion': 'neutral', 'valence': 0.0, 'activation': 0.0}
        ]
        
        # テストメッセージ
        test_messages = [
            "これは幸せな状態のテストメッセージです。",
            "これは悲しい状態のテストメッセージです。",
            "これは驚いた状態のテストメッセージです！",
            "これは怒りの状態のテストメッセージです！",
            "これは平常状態のテストメッセージです。"
        ]
        
        # 各感情データを3秒ごとに送信
        for i, (emotion, message) in enumerate(zip(test_emotions, test_messages)):
            print(f"テストデータ送信 {i+1}/{len(test_emotions)}: {emotion['primary_emotion']}")
            
            text_data = {
                'text': message,
                'timestamp': time.time()
            }
            
            response = {
                'response': f"これは{emotion['primary_emotion']}に対する応答テストです。",
                'timestamp': time.time()
            }
            
            await server.send_emotion_data(emotion, text_data, response)
            await asyncio.sleep(3)
        
        print("テストデータの送信が完了しました")
    
    # サーバー起動と同時にテストデータ送信を開始
    async def main():
        # テストデータ送信タスク
        send_task = asyncio.create_task(send_test_data())
        
        # サーバー起動
        await server.run_async()
        
        # テストタスクの完了を待機
        await send_task
    
    # 非同期メインループを実行
    asyncio.run(main())
