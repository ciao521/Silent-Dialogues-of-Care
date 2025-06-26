"""
共感的応答生成モジュール
OpenAI GPT-4o APIを使用して感情や発話内容に応じた共感的な応答を生成
"""
import os
import openai
from loguru import logger

class EmpatheticResponseGenerator:
    def __init__(self, config, api_key=None):
        """
        共感的応答生成モジュールの初期化
        
        Args:
            config (dict): 設定ファイルから読み込んだLLM設定
            api_key (str, optional): OpenAI APIキー。Noneの場合は環境変数から読み込む
        """
        # APIキーの設定
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OpenAI APIキーが設定されていません")
            raise ValueError("OpenAI APIキーが必要です。環境変数OPENAI_API_KEYを設定するか、初期化時にapi_keyを指定してください")
        
        openai.api_key = self.api_key
        
        # LLM設定
        self.model = config.get('model', 'gpt-4o')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 300)
        self.system_message = config.get('system_message', 
                                        "あなたは来場者の感情に寄り添い、共感的な応答を提供するAIアシスタントです。"
                                        "短く、詩的で、深い洞察を含む応答を心がけてください。")
        
        # 会話履歴（コンテキスト維持用）
        self.conversation_history = []
        self.max_history_length = 10  # 保持する会話の最大ターン数
        
        logger.info(f"EmpatheticResponseGeneratorを初期化: モデル={self.model}")
    
    def generate_response(self, user_text, emotion_data, reset_history=False):
        """
        ユーザーの発話と感情データに基づいて共感的な応答を生成
        
        Args:
            user_text (str): ユーザーの発話テキスト
            emotion_data (dict): マルチモーダル感情統合の結果
            reset_history (bool): 会話履歴をリセットするかどうか
            
        Returns:
            dict: 生成された応答と関連情報
        """
        if reset_history:
            self.reset_conversation_history()
        
        if not user_text:
            logger.warning("応答生成のためのユーザーテキストがありません")
            return {'response': '', 'prompt_tokens': 0, 'completion_tokens': 0}
        
        try:
            # 感情情報の整形
            emotion_str = ""
            if emotion_data:
                primary_emotion = emotion_data.get('primary_emotion', 'neutral')
                valence = emotion_data.get('valence', 0.0)
                activation = emotion_data.get('activation', 0.0)
                
                emotion_str = (
                    f"感情状態: {primary_emotion}, "
                    f"感情価(valence): {valence:.2f} (-1.0〜1.0, ポジティブ度), "
                    f"活性度(activation): {activation:.2f} (-1.0〜1.0, 興奮度)"
                )
                
                # 感情的キーワードがあれば追加
                if 'emotional_keywords' in emotion_data and emotion_data['emotional_keywords']:
                    keywords = [item['keyword'] for item in emotion_data['emotional_keywords']]
                    emotion_str += f"\n感情的キーワード: {', '.join(keywords)}"
            
            # プロンプトの構築
            messages = [
                {"role": "system", "content": self.system_message}
            ]
            
            # 会話履歴を追加
            for message in self.conversation_history:
                messages.append(message)
            
            # 現在のユーザー発話と感情情報を追加
            current_message = f"{user_text}\n\n[{emotion_str}]"
            messages.append({"role": "user", "content": current_message})
            
            # GPT-4o APIを呼び出して応答を生成
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # 応答テキストを取得
            assistant_response = response.choices[0].message.content.strip()
            
            # 会話履歴を更新
            self.conversation_history.append({"role": "user", "content": current_message})
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            
            # 会話履歴が長すぎる場合は古いものから削除
            if len(self.conversation_history) > self.max_history_length * 2:
                self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
            
            # トークン使用量を取得
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            
            logger.info(f"応答生成完了: '{assistant_response[:50]}...' (トークン: {prompt_tokens}+{completion_tokens})")
            
            return {
                'response': assistant_response,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'model': self.model
            }
            
        except Exception as e:
            logger.error(f"応答生成中にエラーが発生: {e}")
            return {'response': '申し訳ありません、応答の生成中にエラーが発生しました。', 'prompt_tokens': 0, 'completion_tokens': 0}
    
    def reset_conversation_history(self):
        """会話履歴をリセット"""
        self.conversation_history = []
        logger.debug("会話履歴をリセットしました")


# テスト用コード
if __name__ == "__main__":
    import json
    
    # テスト設定
    test_config = {
        'model': 'gpt-4o',
        'temperature': 0.7,
        'max_tokens': 300,
        'system_message': "あなたは来場者の感情に寄り添い、共感的な応答を提供するAIアシスタントです。短く、詩的で、深い洞察を含む応答を心がけてください。"
    }
    
    # APIキーが環境変数に設定されていることを確認
    if not os.environ.get("OPENAI_API_KEY"):
        print("テストにはOPENAI_API_KEY環境変数が必要です")
        exit(1)
    
    # 応答生成モジュールの初期化
    generator = EmpatheticResponseGenerator(test_config)
    
    # テスト用の感情データ
    test_emotion_data = {
        'primary_emotion': 'contentment',
        'confidence': 0.85,
        'valence': 0.7,
        'activation': -0.2,
        'emotional_keywords': [
            {'keyword': '穏やか', 'category': 'calm'},
            {'keyword': '安心', 'category': 'positive'}
        ]
    }
    
    # テスト用のユーザー発話
    test_user_text = "今日はとても穏やかな気持ちで、久しぶりに心が安らいでいます。"
    
    # 応答生成を実行
    print(f"ユーザー発話: {test_user_text}")
    print(f"感情状態: {json.dumps(test_emotion_data, indent=2, ensure_ascii=False)}")
    print("\n応答を生成中...\n")
    
    result = generator.generate_response(test_user_text, test_emotion_data)
    
    print(f"生成された応答: {result['response']}")
    print(f"使用トークン: プロンプト={result['prompt_tokens']}, 応答={result['completion_tokens']}")
