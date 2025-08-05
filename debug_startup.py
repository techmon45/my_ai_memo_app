#!/usr/bin/env python3
"""
DatabaseManager 初期化デバッグスクリプト
"""

try:
    print("=== DatabaseManager 初期化デバッグ ===")
    
    # Step 1: 基本的なインポートテスト
    print("1. モジュールのインポートテスト...")
    from src.models.database import SessionLocal, Memo, Tag, init_db
    print("   ✅ database models")
    
    # Step 2: データベース初期化
    print("2. データベース初期化テスト...")
    init_db()
    print("   ✅ init_db()")
    
    # Step 3: セッション作成テスト
    print("3. セッション作成テスト...")
    db = SessionLocal()
    db.close()
    print("   ✅ SessionLocal")
    
    # Step 4: DatabaseManagerインポート
    print("4. DatabaseManager インポートテスト...")
    from src.utils.database_manager import DatabaseManager
    print("   ✅ DatabaseManager import")
    
    # Step 5: DatabaseManager初期化
    print("5. DatabaseManager 初期化テスト...")
    db_manager = DatabaseManager()
    print("   ✅ DatabaseManager init")
    
    print("🎉 すべてのテストが成功しました")
    
except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()