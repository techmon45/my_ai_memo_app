from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import subprocess
import json
import sys
import os
from datetime import datetime
import uuid
from contextlib import asynccontextmanager
from src.utils.database_manager import DatabaseManager
import select
import time

# データベースマネージャーの初期化
db_manager = DatabaseManager()

# MCPサーバーとの通信クラス
class MCPServer:
    def __init__(self):
        self.server_process = None
    
    def start_server(self):
        """MCPサーバーを起動"""
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, "server.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # バッファ詰まり防止
                text=True
            )
            return True
        except Exception as e:
            print(f"Error starting MCP server: {e}")
            return False
    
    def send_request(self, method: str, params: list = None) -> Dict[str, Any]:
        """MCPサーバーにリクエストを送信（タイムアウト付き）"""
        if not self.server_process:
            if not self.start_server():
                return {"error": "MCPサーバーの起動に失敗しました"}
        if params is None:
            params = []
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params
            }
            request_str = json.dumps(request) + "\n"
            self.server_process.stdin.write(request_str)
            self.server_process.stdin.flush()
            
            # タイムアウト設定（10秒）
            start_time = time.time()
            while time.time() - start_time < 10:
                # selectでstdoutにデータが来ているか確認（非ブロッキング）
                ready, _, _ = select.select([self.server_process.stdout], [], [], 0.1)
                if ready:
                    response_line = self.server_process.stdout.readline()
                    if response_line:
                        response = json.loads(response_line.strip())
                        return response
            
            return {"error": "MCPサーバーからのレスポンスがタイムアウトしました"}
        except Exception as e:
            return {"error": f"MCP通信エラー: {str(e)}"}

# Pydanticモデル
class MemoCreate(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = None

class MemoUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 50

# MCPサーバーインスタンス
mcp_server = MCPServer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    print("AI Memo App API サーバーを起動中...")
    if mcp_server.start_server():
        print("MCPサーバーが正常に起動しました")
    else:
        print("MCPサーバーの起動に失敗しました")
    
    yield
    
    # 終了時
    if mcp_server.server_process:
        mcp_server.server_process.terminate()
        print("MCPサーバーを停止しました")

# FastAPIアプリケーション
app = FastAPI(
    title="AI Memo App API",
    description="AIを活用したメモ帳アプリケーションのAPI",
    version="0.1.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "AI Memo App API",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/memos")
async def list_memos(limit: int = 100, offset: int = 0):
    """すべてのメモを取得（DB 直アクセス）"""
    try:
        memos = db_manager.list_memos(limit=limit, offset=offset)
        return memos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tags")
async def get_all_tags():
    """すべてのタグを取得（DB 直アクセス）"""
    try:
        return db_manager.get_all_tags()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """統計情報を取得（DB 直アクセス）"""
    try:
        count = db_manager.get_memo_count()
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memos")
async def create_memo(memo: MemoCreate, bg: BackgroundTasks):
    """メモ作成 → 先に DB 保存、AI はバックグラウンド"""
    # 1) 先にプレーン保存して ID を返す
    saved = db_manager.create_memo(
        title=memo.title,
        content=memo.content,
        tags=memo.tags or [],
        summary=None
    )
    # 2) AI 要約 + タグ生成を裏で実行
    bg.add_task(
        mcp_server.send_request,
        "update_memo",        # AI 再計算用ツールを流用
        [saved["id"], None, saved["content"], saved["tags"]]
    )
    return saved

@app.get("/memos/{memo_id}")
async def get_memo(memo_id: str):
    """指定されたメモを取得（DB 直アクセス）"""
    try:
        memo = db_manager.get_memo(memo_id)
        if not memo:
            raise HTTPException(status_code=404, detail="メモが見つかりません")
        return memo
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/memos/{memo_id}")
async def update_memo(memo_id: str, memo: MemoUpdate):
    """メモを更新"""
    try:
        params = [memo_id]
        if memo.title is not None:
            params.append(memo.title)
        else:
            params.append(None)
        if memo.content is not None:
            params.append(memo.content)
        else:
            params.append(None)
        if memo.tags is not None:
            params.append(memo.tags)
        else:
            params.append(None)
        result = mcp_server.send_request("update_memo", params)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result.get("result", result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memos/{memo_id}")
async def delete_memo(memo_id: str):
    """メモを削除（DB 直アクセス）"""
    try:
        success = db_manager.delete_memo(memo_id)
        if success:
            return {"message": "メモが正常に削除されました"}
        else:
            raise HTTPException(status_code=404, detail="メモが見つかりません")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memos/search")
async def search_memos(search_query: SearchQuery):
    """メモを検索（DB 直アクセス）"""
    try:
        return db_manager.search_memos(query=search_query.query, limit=search_query.limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memos/search/{query}")
async def search_memos_get(query: str, limit: int = 50):
    """メモを検索（GET版, DB 直アクセス）"""
    try:
        return db_manager.search_memos(query=query, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memos/tag/{tag_name}")
async def get_memos_by_tag(tag_name: str, limit: int = 50):
    """タグでメモを検索（DB 直アクセス）"""
    try:
        return db_manager.get_memos_by_tag(tag_name=tag_name, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 