#!/usr/bin/env python3
"""
AI Memo App 起動スクリプト
"""

import subprocess
import sys
import time
import os
from pathlib import Path
import requests


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
        # まず直接実行を試して詳細なエラーを取得
        print("📝 APIサーバーの詳細エラーをチェック中...")
        test_process = subprocess.run([
            "python", "src/backend/api_server.py"
        ], capture_output=True, text=True, timeout=10)
        
        if test_process.returncode != 0:
            print(f"❌ APIサーバーが即座に終了しました（終了コード: {test_process.returncode}）")
            print(f"📝 標準出力: {test_process.stdout}")
            print(f"🚨 エラー出力: {test_process.stderr}")
            raise Exception(f"APIサーバーが起動に失敗しました: {test_process.stderr}")
        
    except subprocess.TimeoutExpired:
        print("⏱️  APIサーバーが10秒間実行中（正常）")
        
        # 正常に動作している可能性があるので、バックグラウンドで起動
        print("🚀 APIサーバーをバックグラウンドで起動中...")
        api_process = subprocess.Popen([
            "python", "src/backend/api_server.py"
        ])
        
        # 少し待機
        time.sleep(3)
        
        # プロセスの状態を確認
        if api_process.poll() is not None:
            print(f"❌ バックグラウンドプロセスが終了しました（終了コード: {api_process.returncode}）")
            raise Exception(f"APIサーバーが起動に失敗しました。終了コード: {api_process.returncode}")
        
        print("✅ APIサーバープロセスは実行中です")
        
        # ヘルスチェック
        print("🏥 ヘルスチェックを実行中...")
        for attempt in range(10):
            try:
                response = requests.get("http://localhost:8000/health", timeout=3)
                if response.status_code == 200:
                    print("✅ APIサーバーが正常に起動しました")
                    return api_process
                else:
                    print(f"⚠️  ヘルスチェック失敗 (試行 {attempt + 1}/10): ステータス {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"⚠️  ヘルスチェック失敗 (試行 {attempt + 1}/10): 接続拒否")
            
            if attempt < 9:
                time.sleep(1)
        
        # 全て失敗した場合
        print("🔍 APIサーバーの詳細な状態を確認中...")
        if api_process.poll() is None:
            print("❓ APIサーバープロセスはまだ実行中ですが、ヘルスチェックに応答しません")
        else:
            print(f"💀 APIサーバープロセスが終了しました（終了コード: {api_process.returncode}）")
        
        raise Exception("APIサーバーのヘルスチェックがすべて失敗しました")
            
    except Exception as e:
        if "APIサーバー" in str(e):
            raise
        else:
            raise Exception(f"APIサーバーの起動エラー: {e}")

def start_streamlit_app():
    """Streamlitアプリを起動"""
    print("🌐 Streamlitアプリを起動中...")
    try:
        # Streamlitアプリの起動
        streamlit_process = subprocess.Popen([
            "streamlit", "run", "src/frontend/app.py",
            "--server.port", "8501",
        ])
        
        print("✅ Streamlitアプリが起動しました")
        print("🌐 ブラウザで http://localhost:8501 にアクセスしてください")
        return streamlit_process
        
    except Exception as e:
        raise Exception(f"Streamlitアプリの起動エラー: {e}")

def main():
    """メイン関数"""
    print("🤖 AI Memo App 起動スクリプト")
    print("=" * 50)
    
    # 依存関係の確認
    if not check_dependencies():
        return
    
    # APIサーバーの起動
    api_process = None
    try:
        api_process = start_api_server()
    except Exception as e:
        print(f"❌ APIサーバーの起動に失敗: {e}")
        print("⚠️  APIサーバーなしでStreamlitアプリのみを起動します")
        print("💡 APIサーバーの問題を修正後、再度起動してください")
    
    # Streamlitアプリの起動
    try:
        streamlit_process = start_streamlit_app()
    except Exception as e:
        print(f"❌ Streamlitアプリの起動に失敗: {e}")
        if api_process:
            api_process.terminate()
        return
    
    print("\n🎉 アプリケーションが起動しました！")
    print("📝 使用方法:")
    print("   1. ブラウザで http://localhost:8501 にアクセス")
    if api_process:
        print("   2. サイドバーから「新しいメモを作成」をクリック")
        print("   3. メモのタイトルと内容を入力")
        print("   4. 保存するとAIによる要約とタグ付けが実行されます")
    else:
        print("   ⚠️  APIサーバーが起動していないため、一部機能が制限されます")
    
    # アプリケーションの終了を待機
    try:
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 アプリケーションを停止中...")
        streamlit_process.terminate()
        if api_process:
            api_process.terminate()
        print("✅ アプリケーションが停止しました")

if __name__ == "__main__":
    main() 