from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import subprocess
import json
import sys
import os
from datetime import datetime
import uuid

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
                stderr=subprocess.PIPE,
                text=True
            )
            return True
        except Exception as e:
            print(f"Error starting MCP server: {e}")
            return False
    
    def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """MCPサーバーにリクエストを送信"""
        if not self.server_process:
            if not self.start_server():
                return {"error": "MCPサーバーの起動に失敗しました"}
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params or {}
            }
            
            request_str = json.dumps(request) + "\n"
            self.server_process.stdin.write(request_str)
            self.server_process.stdin.flush()
            
            # レスポンスを読み取り
            response_line = self.server_process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                return response
            else:
                return {"error": "MCPサーバーからのレスポンスがありません"}
                
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

# FastAPIアプリケーション
app = FastAPI(
    title="AI Memo App API",
    description="AIを活用したメモ帳アプリケーションのAPI",
    version="0.1.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCPサーバーインスタンス
mcp_server = MCPServer()

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    print("🚀 AI Memo App API サーバーを起動中...")
    # MCPサーバーを起動
    if mcp_server.start_server():
        print("✅ MCPサーバーが正常に起動しました")
    else:
        print("❌ MCPサーバーの起動に失敗しました")

@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    if mcp_server.server_process:
        mcp_server.server_process.terminate()
        print("🛑 MCPサーバーを停止しました")

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

@app.post("/memos")
async def create_memo(memo: MemoCreate):
    """メモを作成"""
    try:
        result = mcp_server.send_request("create_memo", {
            "title": memo.title,
            "content": memo.content,
            "tags": memo.tags or []
        })
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result.get("result", result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memos")
async def list_memos():
    """すべてのメモを取得"""
    try:
        result = mcp_server.send_request("list_memos")
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result.get("result", result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memos/{memo_id}")
async def get_memo(memo_id: str):
    """指定されたメモを取得"""
    try:
        result = mcp_server.send_request("get_memo", {"memo_id": memo_id})
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result.get("result", result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/memos/{memo_id}")
async def update_memo(memo_id: str, memo: MemoUpdate):
    """メモを更新"""
    try:
        params = {"memo_id": memo_id}
        if memo.title is not None:
            params["title"] = memo.title
        if memo.content is not None:
            params["content"] = memo.content
        if memo.tags is not None:
            params["tags"] = memo.tags
        
        result = mcp_server.send_request("update_memo", params)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result.get("result", result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memos/{memo_id}")
async def delete_memo(memo_id: str):
    """メモを削除"""
    try:
        result = mcp_server.send_request("delete_memo", {"memo_id": memo_id})
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result.get("result", result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memos/search/{query}")
async def search_memos(query: str):
    """メモを検索"""
    try:
        result = mcp_server.send_request("search_memos", {"query": query})
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result.get("result", result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 