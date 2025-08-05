import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from fastmcp import FastMCP
from src.models.memo import Memo, MemoCreate, MemoUpdate
from src.utils.ai_processor import AIProcessor
from src.utils.database_manager import DatabaseManager
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートの .env を指定して読み込む
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)

# データベースマネージャーの初期化
db_manager = DatabaseManager()

# AIプロセッサーの初期化
ai_processor = AIProcessor()

mcp = FastMCP("AI Memo App")

# プレビュー用ツール（要約 + タグ）
# preview_memo ツールにデバッグログを追加
@mcp.tool()
def preview_memo(content: str) -> Dict[str, Any]:
    """メモ内容を AI で要約し、タグ候補を返す (DB 変更なし)"""
    if not ai_processor:
        return {"error": "AIProcessor 未初期化"}
    try:
        result = ai_processor.process_memo(content)
        return result
    except Exception as e:
        return {"error": f"AI 処理に失敗しました: {str(e)}"}

@mcp.tool()
def create_memo(title: str, content: str, tags: List[str] = None) -> Dict[str, Any]:
    """新しいメモを作成し、AIで要約とタグを生成する"""
    
    if tags is None:
        tags = []
    
    # AI処理
    ai_result = {"summary": None, "tags": []}
    if ai_processor:
        try:
            ai_result = ai_processor.process_memo(content)
            # AIが生成したタグとユーザーが指定したタグを結合
            all_tags = list(set(tags + ai_result["tags"]))
        except Exception as e:
            all_tags = tags
    else:
        all_tags = tags
    
    try:
        # データベースに保存
        memo = db_manager.create_memo(
            title=title,
            content=content,
            tags=all_tags,
            summary=ai_result["summary"]
        )
        
        return {
            "id": memo["id"],
            "title": memo["title"],
            "content": memo["content"],
            "summary": memo["summary"],
            "tags": memo["tags"],
            "status": memo["status"],
            "created_at": memo["created_at"],
            "message": "メモが正常に作成されました"
        }
    except Exception as e:
        return {"error": f"メモの作成に失敗しました: {str(e)}"}

@mcp.tool()
def get_memo(memo_id: str) -> Dict[str, Any]:
    """指定されたIDのメモを取得する"""
    
    try:
        memo = db_manager.get_memo(memo_id)
        if not memo:
            return {"error": "メモが見つかりません"}
        
        return {
            "id": memo["id"],
            "title": memo["title"],
            "content": memo["content"],
            "summary": memo["summary"],
            "tags": memo["tags"],
            "status": memo["status"],
            "created_at": memo["created_at"],
            "updated_at": memo["updated_at"]
        }
    except Exception as e:
        return {"error": f"メモの取得に失敗しました: {str(e)}"}

# 以下の READ 系ユーティリティは FastAPI 側が直接 DB を参照するよう
# 移行したため、FastMCP への登録 (@mcp.tool) を外しました。
# 将来的にバッチ処理や CLI から再利用する可能性があるため、
# 関数本体は残しつつ decorator だけコメントアウトしています。

# def list_memos(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
#     """すべてのメモをリストで取得する (DISABLED: handled by API server)"""
#     try:
#         return db_manager.list_memos(limit=limit, offset=offset)
#     except Exception as e:
#         return [{"error": f"メモ一覧の取得に失敗しました: {str(e)}"}]

# def search_memos(query: str, limit: int = 50) -> List[Dict[str, Any]]:
#     """メモを検索 (DISABLED)"""
#     try:
#         return db_manager.search_memos(query=query, limit=limit)
#     except Exception as e:
#         return [{"error": f"メモの検索に失敗しました: {str(e)}"}]

# def get_memos_by_tag(tag_name: str, limit: int = 50) -> List[Dict[str, Any]]:
#     """タグでメモ検索 (DISABLED)"""
#     try:
#         return db_manager.get_memos_by_tag(tag_name=tag_name, limit=limit)
#     except Exception as e:
#         return [{"error": f"タグ検索に失敗しました: {str(e)}"}]

# def get_all_tags() -> List[str]:
#     """タグ一覧取得 (DISABLED)"""
#     try:
#         return db_manager.get_all_tags()
#     except Exception as e:
#         return [f"タグの取得に失敗しました: {str(e)}"]

# def get_memo_count() -> Dict[str, Any]:
#     """メモ総数取得 (DISABLED)"""
#     try:
#         count = db_manager.get_memo_count()
#         return {"count": count}
#     except Exception as e:
#         return {"error": f"メモ数の取得に失敗しました: {str(e)}"}

@mcp.tool()
def update_memo(memo_id: str, title: str = None, content: str = None, tags: List[str] = None) -> Dict[str, Any]:
    """メモを更新する"""
    
    try:
        # 内容が変更された場合、AIで再処理
        ai_result = {"summary": None, "tags": []}
        if content and ai_processor:
            try:
                ai_result = ai_processor.process_memo(content)
                if tags is None:
                    tags = []
                all_tags = list(set(tags + ai_result["tags"]))
            except Exception as e:
                all_tags = tags if tags else []
        else:
            all_tags = tags
        
        # データベースを更新
        memo = db_manager.update_memo(
            memo_id=memo_id,
            title=title,
            content=content,
            tags=all_tags,
            summary=ai_result["summary"] if content else None
        )
        
        if not memo:
            return {"error": "メモが見つかりません"}
        
        return {
            "id": memo["id"],
            "title": memo["title"],
            "content": memo["content"],
            "summary": memo["summary"],
            "tags": memo["tags"],
            "status": memo["status"],
            "updated_at": memo["updated_at"],
            "message": "メモが正常に更新されました"
        }
    except Exception as e:
        return {"error": f"メモの更新に失敗しました: {str(e)}"}

# @mcp.tool()  # WRITE 系だが現状 FastAPI 直呼び出しに移行したため無効化（再利用時に戻す）
def delete_memo(memo_id: str) -> Dict[str, Any]:
    """メモを削除する"""
    
    try:
        success = db_manager.delete_memo(memo_id)
        if success:
            return {"message": "メモが正常に削除されました"}
        else:
            return {"error": "メモが見つかりません"}
    except Exception as e:
        return {"error": f"メモの削除に失敗しました: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport="stdio")
