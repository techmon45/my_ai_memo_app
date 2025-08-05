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
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            server_path = os.path.join(project_root, "server.py")
            
            self.server_process = subprocess.Popen(
                [sys.executable, server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # ✅ 実際の起動確認
            time.sleep(1)  # 起動を待つ
            
            # プロセスが生きているかチェック
            if self.server_process.poll() is not None:
                return False  # プロセスが既に終了している
            
            # 実際に通信テスト
            try:
                test_response = self.send_request("ping")
                return "error" not in test_response
            except:
                return False
                
        except Exception as e:
            print(f"Error starting MCP server: {e}")
            return False
    
    def send_request(self, method: str, params: list = []) -> Dict[str, Any]:
        """MCPサーバーにリクエストを送信（デバッグ用）"""
        if not self.server_process:
            if not self.start_server():
                return {"error": "MCPサーバーの起動に失敗しました"}
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
            
            # ✅ 実際のレスポンスを受信
            response_line = self.server_process.stdout.readline()
            response = json.loads(response_line)
            return response
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

# AIプレビュー用リクエストモデル
class PreviewRequest(BaseModel):
    content: str

# MCPサーバーインスタンス
mcp_server = MCPServer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    print("AI Memo App API サーバーを起動中...")
    
    # 一時的にMCPサーバー起動をスキップ（デバッグ用）
    print("⚠️  MCPサーバーの起動をスキップします（デバッグ用）")
    
    # 元のコード（一時的にコメントアウト）
    # if mcp_server.start_server():
    #     print("MCPサーバーが正常に起動しました")
    # else:
    #     print("MCPサーバーの起動に失敗しました")
    
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
async def create_memo(memo: MemoCreate):
    """メモ作成（AI 処理込み）"""
    try:
        # AI 処理を直接実行
        from src.utils.ai_processor import AIProcessor
        ai_processor = AIProcessor()
        ai_result = ai_processor.process_memo(memo.content)
        
        # AI タグとユーザータグを結合
        all_tags = list(set((memo.tags or []) + ai_result["tags"]))
        
        # DB に保存
        saved = db_manager.create_memo(
            title=memo.title,
            content=memo.content,
            tags=all_tags,
            summary=ai_result["summary"]
        )
        return saved
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    """メモを更新（DB 直アクセス）"""
    try:
        # 内容が変更された場合、AIで再処理
        ai_result = {"summary": None, "tags": []}
        if memo.content:
            from src.utils.ai_processor import AIProcessor
            ai_processor = AIProcessor()
            ai_result = ai_processor.process_memo(memo.content)
            
            # AI タグとユーザータグを結合
            if memo.tags is None:
                memo.tags = []
            all_tags = list(set(memo.tags + ai_result["tags"]))
        else:
            all_tags = memo.tags
        
        # データベースを更新
        updated_memo = db_manager.update_memo(
            memo_id=memo_id,
            title=memo.title,
            content=memo.content,
            tags=all_tags,
            summary=ai_result["summary"] if memo.content else None
        )
        
        if not updated_memo:
            raise HTTPException(status_code=404, detail="メモが見つかりません")
        
        return updated_memo
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

# ---------------- AIプレビューエンドポイント ----------------

@app.post("/ai/preview")
async def ai_preview(preview: PreviewRequest):
    """AI による要約・タグ付けプレビュー（直接呼び出し版）"""
    try:
        # MCP を経由せず、直接 AIProcessor を使用
        from src.utils.ai_processor import AIProcessor
        
        # AIProcessor の初期化
        ai_processor = AIProcessor()
        result = ai_processor.process_memo(preview.content)
        
        return result
    except Exception as e:
        print(f"AI preview error: {e}")
        raise HTTPException(status_code=500, detail=f"AI 処理エラー: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 