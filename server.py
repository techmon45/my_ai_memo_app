import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from fastmcp import FastMCP
from src.models.memo import Memo, MemoCreate, MemoUpdate
from src.utils.ai_processor import AIProcessor

# メモデータを保存する簡易ストレージ（後でSQLiteに移行予定）
memo_storage: Dict[str, Memo] = {}

# AIプロセッサーの初期化
try:
    ai_processor = AIProcessor()
except ValueError as e:
    print(f"Warning: {e}")
    ai_processor = None

mcp = FastMCP("AI Memo App")

@mcp.tool()
def create_memo(title: str, content: str, tags: List[str] = None) -> Dict[str, Any]:
    """新しいメモを作成し、AIで要約とタグを生成する"""
    if tags is None:
        tags = []
    
    memo_id = str(uuid.uuid4())
    
    # AI処理
    ai_result = {"summary": None, "tags": []}
    if ai_processor:
        try:
            ai_result = ai_processor.process_memo(content)
            # AIが生成したタグとユーザーが指定したタグを結合
            all_tags = list(set(tags + ai_result["tags"]))
        except Exception as e:
            print(f"AI processing error: {e}")
            all_tags = tags
    else:
        all_tags = tags
    
    # メモオブジェクトの作成
    memo = Memo(
        id=memo_id,
        title=title,
        content=content,
        summary=ai_result["summary"],
        tags=all_tags,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # ストレージに保存
    memo_storage[memo_id] = memo
    
    return {
        "id": memo_id,
        "title": memo.title,
        "content": memo.content,
        "summary": memo.summary,
        "tags": memo.tags,
        "status": memo.status.value,
        "created_at": memo.created_at.isoformat(),
        "message": "メモが正常に作成されました"
    }

@mcp.tool()
def get_memo(memo_id: str) -> Dict[str, Any]:
    """指定されたIDのメモを取得する"""
    if memo_id not in memo_storage:
        return {"error": "メモが見つかりません"}
    
    memo = memo_storage[memo_id]
    return {
        "id": memo.id,
        "title": memo.title,
        "content": memo.content,
        "summary": memo.summary,
        "tags": memo.tags,
        "status": memo.status.value,
        "created_at": memo.created_at.isoformat(),
        "updated_at": memo.updated_at.isoformat()
    }

@mcp.tool()
def list_memos() -> List[Dict[str, Any]]:
    """すべてのメモをリストで取得する"""
    return [
        {
            "id": memo.id,
            "title": memo.title,
            "summary": memo.summary,
            "tags": memo.tags,
            "status": memo.status.value,
            "created_at": memo.created_at.isoformat()
        }
        for memo in memo_storage.values()
    ]

@mcp.tool()
def update_memo(memo_id: str, title: str = None, content: str = None, tags: List[str] = None) -> Dict[str, Any]:
    """メモを更新する"""
    if memo_id not in memo_storage:
        return {"error": "メモが見つかりません"}
    
    memo = memo_storage[memo_id]
    
    # 更新するフィールドを設定
    if title:
        memo.title = title
    if content:
        memo.content = content
        # 内容が変更された場合、AIで再処理
        if ai_processor:
            try:
                ai_result = ai_processor.process_memo(content)
                memo.summary = ai_result["summary"]
                if tags is None:
                    tags = []
                memo.tags = list(set(tags + ai_result["tags"]))
            except Exception as e:
                print(f"AI processing error: {e}")
                if tags:
                    memo.tags = tags
        else:
            if tags:
                memo.tags = tags
    elif tags:
        memo.tags = tags
    
    memo.updated_at = datetime.now()
    
    return {
        "id": memo.id,
        "title": memo.title,
        "content": memo.content,
        "summary": memo.summary,
        "tags": memo.tags,
        "status": memo.status.value,
        "updated_at": memo.updated_at.isoformat(),
        "message": "メモが正常に更新されました"
    }

@mcp.tool()
def delete_memo(memo_id: str) -> Dict[str, Any]:
    """メモを削除する"""
    if memo_id not in memo_storage:
        return {"error": "メモが見つかりません"}
    
    del memo_storage[memo_id]
    return {"message": "メモが正常に削除されました"}

@mcp.tool()
def search_memos(query: str) -> List[Dict[str, Any]]:
    """メモを検索する（タイトル、内容、タグで検索）"""
    results = []
    query_lower = query.lower()
    
    for memo in memo_storage.values():
        if (query_lower in memo.title.lower() or 
            query_lower in memo.content.lower() or 
            any(query_lower in tag.lower() for tag in memo.tags)):
            results.append({
                "id": memo.id,
                "title": memo.title,
                "summary": memo.summary,
                "tags": memo.tags,
                "status": memo.status.value,
                "created_at": memo.created_at.isoformat()
            })
    
    return results

if __name__ == "__main__":
    mcp.run(transport="stdio")
