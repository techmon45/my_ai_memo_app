import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from fastmcp import FastMCP
from src.models.memo import Memo, MemoCreate, MemoUpdate
from src.utils.ai_processor import AIProcessor
from src.utils.database_manager import DatabaseManager

# データベースマネージャーの初期化
db_manager = DatabaseManager()

# AIプロセッサーの初期化
try:
    ai_processor = AIProcessor()
except ValueError as e:
    # print(f"Warning: {e}")
    ai_processor = None

mcp = FastMCP("AI Memo App")

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
            # print(f"AI processing error: {e}")
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

@mcp.tool()
def list_memos(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """すべてのメモをリストで取得する"""
    try:
        memos = db_manager.list_memos(limit=limit, offset=offset)
        return [
            {
                "id": memo["id"],
                "title": memo["title"],
                "summary": memo["summary"],
                "tags": memo["tags"],
                "status": memo["status"],
                "created_at": memo["created_at"]
            }
            for memo in memos
        ]
    except Exception as e:
        return [{"error": f"メモ一覧の取得に失敗しました: {str(e)}"}]

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
                # print(f"AI processing error: {e}")
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

@mcp.tool()
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

@mcp.tool()
def search_memos(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """メモを検索する（タイトル、内容、タグで検索）"""
    try:
        results = db_manager.search_memos(query=query, limit=limit)
        return [
            {
                "id": memo["id"],
                "title": memo["title"],
                "summary": memo["summary"],
                "tags": memo["tags"],
                "status": memo["status"],
                "created_at": memo["created_at"]
            }
            for memo in results
        ]
    except Exception as e:
        return [{"error": f"メモの検索に失敗しました: {str(e)}"}]

@mcp.tool()
def get_memos_by_tag(tag_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """指定されたタグでメモを検索する"""
    try:
        results = db_manager.get_memos_by_tag(tag_name=tag_name, limit=limit)
        return [
            {
                "id": memo["id"],
                "title": memo["title"],
                "summary": memo["summary"],
                "tags": memo["tags"],
                "status": memo["status"],
                "created_at": memo["created_at"]
            }
            for memo in results
        ]
    except Exception as e:
        return [{"error": f"タグ検索に失敗しました: {str(e)}"}]

@mcp.tool()
def get_all_tags() -> List[str]:
    """すべてのタグを取得する"""
    try:
        return db_manager.get_all_tags()
    except Exception as e:
        return [f"タグの取得に失敗しました: {str(e)}"]

@mcp.tool()
def get_memo_count() -> Dict[str, Any]:
    """メモの総数を取得する"""
    try:
        count = db_manager.get_memo_count()
        return {"count": count, "message": f"メモの総数: {count}件"}
    except Exception as e:
        return {"error": f"メモ数の取得に失敗しました: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport="stdio")
