"""
Silent Dialogues of Care - 境界なき対話
テスト実行スクリプト - テキスト読み上げ機能のテスト

このスクリプトは、テキスト読み上げモジュールを直接テストするためのものです。
"""
import os
import time
import argparse
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv

# モジュールのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# テキスト読み上げモジュールをインポート
from output_modules.audio_output.openai_tts import TextToSpeechManager


def main():
    """
    メイン関数
    """
    # コマンドライン引数の処理
    parser = argparse.ArgumentParser(description="テキスト読み上げ機能のテスト")
    parser.add_argument('--text', default='こんにちは、境界なき対話へようこそ。このテストは読み上げ機能が正しく動作しているかを確認するためのものです。',
                        help='読み上げるテキスト')
    parser.add_argument('--voice', default='nova', help='使用する音声（nova, alloy, echo, fable, onyx, shimmer）')
    parser.add_argument('--speed', type=float, default=1.0, help='読み上げ速度（0.5〜2.0）')
    parser.add_argument('--config', default='config/settings.yaml', help='設定ファイルのパス')
    args = parser.parse_args()
    
    # 環境変数の読み込み
    load_dotenv()
    
    # APIキーの確認
    if not os.environ.get('OPENAI_API_KEY'):
        print("エラー: OPENAI_API_KEYが設定されていません。")
        print("'.env'ファイルにOPENAI_API_KEY=your_key_hereを追加してください。")
        return
    
    # 設定ファイルの読み込み
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"設定ファイルの読み込みに失敗しました: {e}")
        config = {}
    
    # 音声出力設定の取得または設定
    if 'output' not in config:
        config['output'] = {}
    if 'audio' not in config['output']:
        config['output']['audio'] = {}
    
    # コマンドライン引数で上書き
    config['output']['audio']['voice'] = args.voice
    config['output']['audio']['speed'] = args.speed
    config['output']['audio']['enabled'] = True
    
    print(f"テキスト読み上げテストを開始します:")
    print(f"テキスト: {args.text}")
    print(f"音声: {args.voice}")
    print(f"速度: {args.speed}")
    
    try:
        # テキスト読み上げマネージャーの初期化
        tts_manager = TextToSpeechManager(config['output']['audio'])
        
        # テキスト読み上げの実行
        print("音声を生成して再生します...")
        success = tts_manager.speak(args.text, block=True)
        
        if success:
            print("読み上げが完了しました。")
        else:
            print("読み上げに失敗しました。")
        
        # クリーンアップ
        tts_manager.cleanup()
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
