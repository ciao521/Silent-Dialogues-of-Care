"""
共感的応答生成モジュールのテスト
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import os
import json

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_interaction.empathetic_response_generator import EmpatheticResponseGenerator


class TestEmpatheticResponseGenerator(unittest.TestCase):
    """共感的応答生成モジュールのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # APIキーを環境変数に設定
        os.environ["OPENAI_API_KEY"] = "test_api_key"
        
        # 設定を準備
        self.config = {
            'model': 'gpt-4o',
            'temperature': 0.7,
            'max_tokens': 300,
            'system_message': "あなたは来場者の感情に寄り添い、共感的な応答を提供するAIアシスタントです。"
                            "短く、詩的で、深い洞察を含む応答を心がけてください。"
        }
        
        # openaiモジュールをパッチ
        self.patcher = patch('llm_interaction.empathetic_response_generator.openai')
        self.mock_openai = self.patcher.start()
        
        # 応答生成器の初期化
        self.response_generator = EmpatheticResponseGenerator(self.config)
        
        # テスト用の感情データ
        self.emotion_data = {
            'dominant_emotion': 'happy',
            'emotion_intensity': 0.8,
            'emotion_vector': {
                'happy': 0.8,
                'sad': 0.1,
                'surprise': 0.05,
                'anger': 0.02,
                'fear': 0.03
            },
            'valence': 0.7,
            'arousal': 0.6
        }
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.patcher.stop()
    
    def test_init(self):
        """初期化テスト"""
        self.assertEqual(self.response_generator.api_key, "test_api_key")
        self.assertEqual(self.response_generator.model, "gpt-4o")
        self.assertEqual(self.response_generator.temperature, 0.7)
        self.assertEqual(self.response_generator.max_tokens, 300)
        self.assertIn("共感的な応答を提供する", self.response_generator.system_message)
        self.assertEqual(len(self.response_generator.conversation_history), 0)
    
    @patch('llm_interaction.empathetic_response_generator.openai')
    def test_init_custom_api_key(self, mock_openai):
        """カスタムAPIキーでの初期化テスト"""
        generator = EmpatheticResponseGenerator(self.config, api_key="custom_api_key")
        self.assertEqual(generator.api_key, "custom_api_key")
        self.assertEqual(mock_openai.api_key, "custom_api_key")
    
    @patch('llm_interaction.empathetic_response_generator.openai')
    def test_init_no_api_key(self, mock_openai):
        """APIキーなしの初期化テスト"""
        # 環境変数をクリア
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                EmpatheticResponseGenerator(self.config)
    
    def test_generate_response(self):
        """応答生成テスト"""
        # OpenAI APIのモックレスポンス
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = {"content": "あなたの喜びが伝わってきます。素敵な瞬間ですね。"}
        self.mock_openai.ChatCompletion.create.return_value = mock_response
        
        # 応答を生成
        user_text = "今日はとても楽しい一日でした！"
        result = self.response_generator.generate_response(user_text, self.emotion_data)
        
        # 検証
        self.mock_openai.ChatCompletion.create.assert_called_once()
        self.assertIn("response", result)
        self.assertEqual(result["response"], "あなたの喜びが伝わってきます。素敵な瞬間ですね。")
        
        # 会話履歴が更新されたことを確認
        self.assertEqual(len(self.response_generator.conversation_history), 2)  # ユーザー発話とシステム応答
    
    def test_generate_response_with_history(self):
        """会話履歴を含む応答生成テスト"""
        # 既存の会話履歴を設定
        self.response_generator.conversation_history = [
            {"role": "user", "content": "こんにちは"},
            {"role": "assistant", "content": "こんにちは、お元気ですか？"}
        ]
        
        # OpenAI APIのモックレスポンス
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = {"content": "素晴らしいですね。その喜びを大切にしてください。"}
        self.mock_openai.ChatCompletion.create.return_value = mock_response
        
        # 応答を生成
        user_text = "今日はとても楽しい一日でした！"
        result = self.response_generator.generate_response(user_text, self.emotion_data)
        
        # 検証
        self.mock_openai.ChatCompletion.create.assert_called_once()
        
        # 会話履歴が正しく更新されたことを確認（システムメッセージ + 2つの古い会話 + 新しい会話2つ）
        self.assertEqual(len(self.response_generator.conversation_history), 4)
        self.assertEqual(self.response_generator.conversation_history[2]["content"], user_text)
        self.assertEqual(self.response_generator.conversation_history[3]["content"], "素晴らしいですね。その喜びを大切にしてください。")
    
    def test_generate_response_reset_history(self):
        """会話履歴リセットテスト"""
        # 既存の会話履歴を設定
        self.response_generator.conversation_history = [
            {"role": "user", "content": "こんにちは"},
            {"role": "assistant", "content": "こんにちは、お元気ですか？"}
        ]
        
        # OpenAI APIのモックレスポンス
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = {"content": "新しい会話の始まりですね。"}
        self.mock_openai.ChatCompletion.create.return_value = mock_response
        
        # 会話履歴をリセットして応答を生成
        user_text = "新しい話題について話しましょう"
        result = self.response_generator.generate_response(user_text, self.emotion_data, reset_history=True)
        
        # 検証
        self.mock_openai.ChatCompletion.create.assert_called_once()
        
        # 会話履歴がリセットされて新しい会話だけになったことを確認
        self.assertEqual(len(self.response_generator.conversation_history), 2)
        self.assertEqual(self.response_generator.conversation_history[0]["content"], user_text)
        self.assertEqual(self.response_generator.conversation_history[1]["content"], "新しい会話の始まりですね。")
    
    def test_generate_response_api_error(self):
        """API エラーテスト"""
        # APIエラーをシミュレート
        self.mock_openai.ChatCompletion.create.side_effect = Exception("API エラー")
        
        # 応答生成を試みる
        user_text = "今日はとても楽しい一日でした！"
        result = self.response_generator.generate_response(user_text, self.emotion_data)
        
        # 検証
        self.assertIn("error", result)
        self.assertIn("API エラー", result["error"])
    
    def test_get_prompt_with_emotion(self):
        """感情を含むプロンプト生成テスト"""
        user_text = "今日はとても楽しい一日でした！"
        prompt = self.response_generator._get_prompt_with_emotion(user_text, self.emotion_data)
        
        # 検証
        self.assertIn("感情分析結果", prompt)
        self.assertIn("happy", prompt)
        self.assertIn("0.8", prompt)
        self.assertIn(user_text, prompt)
    
    def test_history_limit(self):
        """会話履歴の長さ制限テスト"""
        # 会話履歴の最大長さをテスト用に設定
        self.response_generator.max_history_length = 3
        
        # 会話履歴を最大長さを超えて設定
        self.response_generator.conversation_history = [
            {"role": "user", "content": "こんにちは1"},
            {"role": "assistant", "content": "こんにちは1、お元気ですか？"},
            {"role": "user", "content": "こんにちは2"},
            {"role": "assistant", "content": "こんにちは2、お元気ですか？"},
            {"role": "user", "content": "こんにちは3"},
            {"role": "assistant", "content": "こんにちは3、お元気ですか？"}
        ]
        
        # OpenAI APIのモックレスポンス
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = {"content": "新しい応答です。"}
        self.mock_openai.ChatCompletion.create.return_value = mock_response
        
        # 応答を生成
        user_text = "新しいメッセージです"
        self.response_generator.generate_response(user_text, self.emotion_data)
        
        # 検証
        # 会話履歴が最大長さの3に制限されていることを確認（6つの古い会話から最新の4つだけが保持されるはず）
        self.assertEqual(len(self.response_generator.conversation_history), 3)
        
        # 最新の会話が保持されていることを確認
        self.assertEqual(self.response_generator.conversation_history[1]["content"], user_text)
        self.assertEqual(self.response_generator.conversation_history[2]["content"], "新しい応答です。")


if __name__ == '__main__':
    unittest.main()
