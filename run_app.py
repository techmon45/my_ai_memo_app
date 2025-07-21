#!/usr/bin/env python3
"""
AI Memo App 起動スクリプト
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_dependencies():
    """依存関係の確認"""
    try:
        import streamlit
        import fastapi
        import uvicorn
        import openai
        print("✅ 依存関係が正常にインストールされています")
        return True
    except ImportError as e:
        print(f"❌ 依存関係が不足しています: {e}")
        print("💡 以下のコマンドを実行してください:")
        print("   uv sync")
        return False

def start_api_server():
    """APIサーバーを起動"""
    print("🚀 APIサーバーを起動中...")
    try:
        # APIサーバーの起動
        api_process = subprocess.Popen([
            "python", "src/backend/api_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="cp932")
        
        # サーバーの起動を待つ
        time.sleep(3)
        
        # プロセスの状態を確認
        if api_process.poll() is not None:
            # プロセスが終了している場合、エラー出力を確認
            stdout, stderr = api_process.communicate()
            print(f"❌ APIサーバーが起動に失敗しました")
            if stderr:
                print(f"エラー詳細: {stderr}")  # decode不要
            return None
        
        # ヘルスチェック
        import requests
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ APIサーバーが正常に起動しました")
                return api_process
            else:
                print(f"❌ APIサーバーのヘルスチェックに失敗しました (ステータス: {response.status_code})")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ APIサーバーに接続できません: {e}")
            return None
            
    except Exception as e:
        print(f"❌ APIサーバーの起動エラー: {e}")
        return None

def start_streamlit_app():
    """Streamlitアプリを起動"""
    print("🌐 Streamlitアプリを起動中...")
    try:
        # Streamlitアプリの起動
        streamlit_process = subprocess.Popen([
            "streamlit", "run", "src/frontend/app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
        print("✅ Streamlitアプリが起動しました")
        print("🌐 ブラウザで http://localhost:8501 にアクセスしてください")
        return streamlit_process
        
    except Exception as e:
        print(f"❌ Streamlitアプリの起動エラー: {e}")
        return None

def main():
    """メイン関数"""
    print("🤖 AI Memo App 起動スクリプト")
    print("=" * 50)
    
    # 依存関係の確認
    if not check_dependencies():
        return
    
    # APIサーバーの起動
    api_process = start_api_server()
    if not api_process:
        print("❌ APIサーバーの起動に失敗しました")
        return
    
    # Streamlitアプリの起動
    streamlit_process = start_streamlit_app()
    if not streamlit_process:
        print("❌ Streamlitアプリの起動に失敗しました")
        api_process.terminate()
        return
    
    print("\n🎉 アプリケーションが正常に起動しました！")
    print("📝 使用方法:")
    print("   1. ブラウザで http://localhost:8501 にアクセス")
    print("   2. サイドバーから「新しいメモを作成」をクリック")
    print("   3. メモのタイトルと内容を入力")
    print("   4. 保存するとAIによる要約とタグ付けが実行されます")
    print("\n🛑 アプリケーションを停止するには Ctrl+C を押してください")
    
    try:
        # プロセスが終了するまで待機
        api_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 アプリケーションを停止中...")
        api_process.terminate()
        streamlit_process.terminate()
        print("✅ アプリケーションが停止しました")

if __name__ == "__main__":
    main() 