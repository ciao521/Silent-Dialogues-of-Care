# Silent Dialogues of Care - 境界なき対話

インタラクティブなAI×ヘルスケア×アート展示プロジェクト

## プロジェクト概要

「Silent Dialogues of Care - 境界なき対話」は、来場者の声と表情をAIがリアルタイムで解析し、その感情や言葉を美しいビジュアルと言葉に変換するインタラクティブアート展示です。コの字型の空間全体を包み込むインタラクティブな映像と音響を通じて、来場者に「AIによる寄り添い」という新たなケアの形を体験していただきます。声にならない思いが可視化され、空間と対話し、自己と向き合う静かで深い対話の場を創出します。

## 主な機能

- **マルチモーダル感情認識**: 音声と表情から感情を分析
- **リアルタイム感情視覚化**: 感情に応じたインタラクティブな3Dビジュアル生成
- **共感的AI応答**: 感情と言葉に基づくLLM（GPT-4o）による応答生成
- **空間全体での体験**: 壁面全体に映し出される没入型視覚表現

## 技術構成

### 入力モジュール
- 音声入力: USBマイク/アレイマイク SDK
- 表情入力: Webカメラ (OpenCV/MediaPipe JS)

### バックエンド（データ処理・AI）
- 音声認識 (STT): OpenAI Whisper API
- 音声感情分析: Hume EVI 2 API
- 表情感情分析: MediaPipe Face Landmarker + カスタムMLモデル (ONNX)
- マルチモーダル感情統合: カスタムロジック
- 共感的応答生成: OpenAI GPT-4o API

### ビジュアル生成・出力
- 3Dビジュアルエンジン: Three.js (WebGPU対応)
- データ連携（AI→ビジュアル）: WebSocket
- 演出出力: プロジェクター(群)

### （任意）音声出力
- テキスト音声合成 (TTS): OpenAI TTS API

## システム要件

### ハードウェア
- CPU: Intel Core i7/AMD Ryzen 7以上
- RAM: 16GB以上
- GPU: NVIDIA GeForce RTX 2060以上（ビジュアル処理用）
- 入力機器: USBカメラ、USBマイク/アレイマイク
- 出力機器: プロジェクター、スピーカー

### ソフトウェア
- OS: Windows 10/11、macOS 12+、Linux Ubuntu 20.04+
- Python 3.9+
- Node.js 16+（フロントエンド開発用）
- WebブラウザはChrome/Edge/Firefox最新版を推奨

## インストール手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/silent-dialogues-of-care.git
cd silent-dialogues-of-care
```

### 2. Pythonパッケージのインストール
```bash
# Python仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Linuxの場合
# Windowsの場合: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 3. 環境設定
```bash
# 環境変数ファイルの作成
cp config/.env.template config/.env

# APIキーの設定（.envファイルを編集）
# OPENAI_API_KEY, HUME_API_KEYなどを設定
```

### 4. フロントエンドの設定
```bash
# WebSocketサーバーとフロントエンドの設定は
# 自動的に行われます（別途のビルド手順は不要）
```

## 使用方法

### 1. アプリケーションの実行
```bash
# メインオーケストレータの実行
python main_orchestrator.py
```

### 2. ブラウザでのアクセス
- WebブラウザでURLにアクセス: `http://localhost:8765`
- ブラウザの全画面モードを有効にしてください（F11キー）

### 3. プロジェクター設定
- プロジェクターを接続し、ディスプレイ設定で拡張または複製モードに設定
- ブラウザの表示をプロジェクターに映し出す

## モジュール構成

プロジェクトは以下のモジュールで構成されています：

```
project-root/
├── data_collection/             # (オプション) 表情感情モデル学習用データ
│   └── custom_emotion_dataset/
├── input_modules/
│   ├── audio_capture/
│   │   └── microphone_handler.py  # マイク入力処理
│   └── face_capture/
│       └── opencv_mediapipe_capture.py # 表情キャプチャ
├── analysis_modules/
│   ├── speech_to_text/
│   │   └── whisper_transcriber.py # 音声テキスト変換
│   ├── vocal_emotion_recognition/
│   │   └── hume_evi_analyzer.py   # 音声感情分析
│   ├── facial_emotion_recognition/
│   │   └── emotion_classifier_onnx.py # 表情感情分析
│   └── multimodal_fusion/
│       └── fusion_engine.py       # 感情統合処理
├── llm_interaction/
│   └── empathetic_response_generator.py # GPT-4oによる応答生成
├── generative_visuals/
│   ├── frontend/                  # Three.jsアプリケーション
│   │   ├── index.html
│   │   ├── main.js
│   │   └── style.css
│   └── backend_websocket_server/
│       └── app.py                 # WebSocketサーバー
├── audio_output/                  # (オプション、AIが発話する場合)
│   └── tts_module.py              # 音声合成
├── logs/
│   └── interaction_log.json       # インタラクションログ
├── models/                          # 学習済みモデル
│   └── facial_emotion_classifier.onnx
├── config/
│   └── settings.yaml              # 設定ファイル
├── tests/                           # テスト
├── utils/                           # ユーティリティ
│   └── data_formatter.py          # データ形式変換
└── main_orchestrator.py             # メイン処理制御
```

## デバッグモード

ビジュアルディスプレイの右上にある「デバッグパネル表示/非表示」ボタンをクリックすると、デバッグパネルが表示されます。ここでは手動で感情状態やメッセージを設定してテストできます。

## 展示設置ガイド

1. **空間設計**:
   - コの字型の空間を準備し、内側に向けてプロジェクターを設置
   - 中央にマイクとカメラを配置

2. **機材設置**:
   - PCをプロジェクターとUSBカメラ/マイクに接続
   - 電源と安定したネットワーク環境を確保

3. **キャリブレーション**:
   - アプリケーション実行後、デバッグモードで各感情状態をテスト
   - 音声入力と表情認識の調整

## ライセンス

本プロジェクトは[MITライセンス](LICENSE)の下で公開されています。

## 謝辞

- OpenAI - GPT-4o、Whisper、TTS APIの提供
- Hume AI - EVI 2音声感情分析APIの提供
- Google - MediaPipe顔認識技術
- Three.js コミュニティ - 3Dビジュアライゼーションライブラリ

## お問い合わせ

プロジェクトに関するお問い合わせは以下までお願いします：
- Email: yasuhiro.iwai@aicurion.com

## テスト

プロジェクトには包括的なテストスイートが含まれています。以下のコマンドでテストを実行できます：

```bash
# すべてのテストを実行
./run_tests.sh

# 個別のテスト実行（例）
python -m unittest tests/test_audio_output.py
```

テキスト読み上げ機能のみをテストするには：
```bash
python tests/test_tts_demo.py --text "こんにちは、テストです" --voice "nova" --speed 1.0
```