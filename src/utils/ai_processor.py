import os
import openai
from typing import List, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# プロジェクトルートの .env を指定して読み込む
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)

class AIProcessor:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = openai.OpenAI(api_key=api_key)
    
    def summarize_memo(self, content: str) -> str:
        """メモの内容を要約する"""
        prompt = f"""
###
You are a professional summarizer.
Summarize the following user note into 2–3 bullet points, each ≤ 15 words.
Text:
\"\"\"{content}\"\"\"
###
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error summarizing memo: {e}")
            return "要約を生成できませんでした"
    
    def extract_tags(self, content: str) -> List[str]:
        """メモの内容からタグを抽出する"""
        prompt = f"""
###
You are a metadata extractor.
From the note below, list up to 5 relevant tags.
Note:
\"\"\"{content}\"\"\"
###
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            # レスポンスからタグを抽出
            tags_text = response.choices[0].message.content.strip()
            # カンマや改行で区切られたタグをリストに変換
            tags = [tag.strip().strip('*').strip('-').strip() for tag in tags_text.split('\n') if tag.strip()]
            tags = [tag for tag in tags if tag and len(tag) > 0]
            
            return tags[:5]  # 最大5個まで
        except Exception as e:
            print(f"Error extracting tags: {e}")
            return []
    
    def process_memo(self, content: str) -> Dict[str, Any]:
        """メモの内容を処理して要約とタグを生成する"""
        summary = self.summarize_memo(content)
        tags = self.extract_tags(content)
        
        return {
            "summary": summary,
            "tags": tags
        } 
