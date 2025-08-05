import streamlit as st
import json
import requests
import uuid
from datetime import datetime
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="AI Memo App",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0055AA;
        text-align: center;
        margin-bottom: 2rem;
    }
    .memo-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .tag-chip {
        background: #0055AA;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.25rem;
        display: inline-block;
    }
    .summary-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #0055AA;
        margin: 1rem 0;
    }
    .stButton > button {
        background-color: #0055AA;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #004499;
    }
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'memos' not in st.session_state:
    st.session_state.memos = {}
if 'current_memo_id' not in st.session_state:
    st.session_state.current_memo_id = None
if 'selected_tag' not in st.session_state:
    st.session_state.selected_tag = None

class MemoAPI:
    """FastAPIサーバーとの通信を行うクラス"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """HTTPリクエストを送信"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {"Content-Type": "application/json"}
            timeout = 15  # 秒
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": "APIサーバーに接続できません。サーバーが起動しているか確認してください。"}
        except Exception as e:
            return {"error": f"リクエストエラー: {str(e)}"}
    
    def create_memo(self, title: str, content: str, tags: List[str] = None) -> Dict[str, Any]:
        """メモを作成"""
        if tags is None:
            tags = []
        
        data = {
            "title": title,
            "content": content,
            "tags": tags
        }
        
        return self._make_request("POST", "/memos", data)
    
    def get_memo(self, memo_id: str) -> Dict[str, Any]:
        """メモを取得"""
        return self._make_request("GET", f"/memos/{memo_id}")
    
    def list_memos(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """すべてのメモを取得"""
        result = self._make_request("GET", f"/memos?limit={limit}&offset={offset}")
        if "error" in result:
            return []
        return result if isinstance(result, list) else []
    
    def update_memo(self, memo_id: str, title: str = None, content: str = None, tags: List[str] = None) -> Dict[str, Any]:
        """メモを更新"""
        data = {}
        if title is not None:
            data["title"] = title
        if content is not None:
            data["content"] = content
        if tags is not None:
            data["tags"] = tags
        
        return self._make_request("PUT", f"/memos/{memo_id}", data)
    
    def delete_memo(self, memo_id: str) -> Dict[str, Any]:
        """メモを削除"""
        return self._make_request("DELETE", f"/memos/{memo_id}")
    
    def search_memos(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """メモを検索"""
        result = self._make_request("GET", f"/memos/search/{query}?limit={limit}")
        if "error" in result:
            return []
        return result if isinstance(result, list) else []
    
    def get_memos_by_tag(self, tag_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """タグでメモを検索"""
        result = self._make_request("GET", f"/memos/tag/{tag_name}?limit={limit}")
        if "error" in result:
            return []
        return result if isinstance(result, list) else []
    
    def get_all_tags(self) -> List[str]:
        """すべてのタグを取得"""
        result = self._make_request("GET", "/tags")
        if "error" in result:
            return []
        return result if isinstance(result, list) else []
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        result = self._make_request("GET", "/stats")
        return result

    # --- AI プレビュー ---
    def ai_preview(self, content: str) -> Dict[str, Any]:
        data = {"content": content}
        return self._make_request("POST", "/ai/preview", data)

# APIインスタンスの作成
api = MemoAPI()

def main():
    """メインアプリケーション"""
    
    # ヘッダー
    st.markdown('<h1 class="main-header">🤖 AI Memo App</h1>', unsafe_allow_html=True)
    
    # APIサーバーの状態確認（タイムアウト付き）
    try:
        health_check = api._make_request("GET", "/health")
        if "error" in health_check:
            st.error("⚠️ APIサーバーに接続できません。サーバーが起動しているか確認してください。")
            st.info("💡 サーバーを起動するには: `uv run python src/backend/api_server.py`")
            return
    except Exception as e:
        st.error(f"⚠️ APIサーバーとの接続でエラーが発生しました: {e}")
        return
    
    # サイドバー
    with st.sidebar:
        st.header("📝 メモ操作")
        
        # 新規メモ作成
        if st.button("➕ 新しいメモを作成", use_container_width=True):
            st.session_state.current_memo_id = None
            st.session_state.selected_tag = None
            st.rerun()
        
        st.divider()
        
        # 統計情報（エラーハンドリング付き）
        try:
            stats = api.get_stats()
            if "count" in stats:
                st.markdown(f"""
                <div class="stats-card">
                    <h4>📊 統計</h4>
                    <p>メモ数: {stats['count']}件</p>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.warning("統計情報の取得に失敗しました")
        
        st.divider()
        
        # タグ一覧（エラーハンドリング付き）
        st.subheader("🏷️ タグ一覧")
        try:
            tags = api.get_all_tags()
            if tags:
                for tag in tags:
                    if st.button(f"🏷️ {tag}", key=f"tag_{tag}", use_container_width=True):
                        st.session_state.selected_tag = tag
                        st.session_state.current_memo_id = None
                        st.rerun()
            else:
                st.info("タグがありません")
        except Exception as e:
            st.warning("タグ一覧の取得に失敗しました")
        
        st.divider()
        
        # 検索機能
        st.subheader("🔍 検索")
        search_query = st.text_input("キーワードを入力", placeholder="タイトル、内容、タグで検索")
        if search_query:
            try:
                search_results = api.search_memos(search_query)
                st.write(f"検索結果: {len(search_results)}件")
            except Exception as e:
                st.warning("検索に失敗しました")
        
        st.divider()
        
        # メモ一覧（エラーハンドリング付き）
        st.subheader("📋 メモ一覧")
        try:
            memos = api.list_memos()
            if memos:
                for memo in memos:
                    if st.button(f"📄 {memo['title'][:30]}...", key=f"list_{memo['id']}", use_container_width=True):
                        st.session_state.current_memo_id = memo['id']
                        st.session_state.selected_tag = None
                        st.rerun()
            else:
                st.info("メモがありません")
        except Exception as e:
            st.warning("メモ一覧の取得に失敗しました")
    
    # メインコンテンツ
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.session_state.current_memo_id is None and st.session_state.selected_tag is None:
            # 新規メモ作成フォーム
            st.subheader("✏️ 新しいメモを作成")
            
            with st.form("create_memo_form"):
                title = st.text_input("タイトル", placeholder="メモのタイトルを入力")
                content = st.text_area("内容", placeholder="メモの内容を入力", height=200)
                tags_input = st.text_input("タグ（カンマ区切り）", placeholder="タグ1, タグ2, タグ3")
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 保存", use_container_width=True)
                with col2:
                    if st.form_submit_button("🤖 AI処理", use_container_width=True):
                        if content:
                            ai_res = api.ai_preview(content)
                            if "error" in ai_res:
                                st.error(ai_res["error"])
                            else:
                                # AI処理結果をセッション状態に保存
                                st.session_state.ai_result = ai_res
                                st.success("AI 処理完了！下記の「適用」ボタンで反映できます")
                        else:
                            st.warning("内容を入力してください")
                
                # AI処理結果の表示と適用
                if 'ai_result' in st.session_state and st.session_state.ai_result:
                    ai_res = st.session_state.ai_result
                    st.markdown("### 🤖 AI処理結果")
                    st.write("**要約:**")
                    st.write(ai_res.get("summary", "(なし)"))
                    st.write("**タグ候補:** " + ", ".join(ai_res.get("tags", [])))
                    
                    col_apply1, col_apply2 = st.columns(2)
                    with col_apply1:
                        if st.form_submit_button("📝 適用して保存", use_container_width=True):
                            if title and content:
                                # AI結果を適用したタグリストを作成
                                manual_tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
                                combined_tags = list(set(manual_tags + ai_res.get("tags", [])))
                                
                                result = api.create_memo(title, content, combined_tags)
                                if "error" in result:
                                    st.error(f"エラー: {result['error']}")
                                else:
                                    st.success("AI結果を適用してメモが作成されました！")
                                    st.session_state.current_memo_id = result["id"]
                                    st.session_state.ai_result = None  # 結果をクリア
                                    st.rerun()
                            else:
                                st.warning("タイトルと内容を入力してください")
                    with col_apply2:
                        if st.form_submit_button("🗑️ AI結果をクリア", use_container_width=True):
                            st.session_state.ai_result = None
                            st.rerun()
                
                if submitted and title and content:
                    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
                    result = api.create_memo(title, content, tags)
                    
                    if "error" in result:
                        st.error(f"エラー: {result['error']}")
                    else:
                        st.success("メモが作成されました！")
                        st.session_state.current_memo_id = result["id"]
                        st.rerun()
        
        elif st.session_state.selected_tag:
            # タグ別メモ一覧
            st.subheader(f"🏷️ タグ: {st.session_state.selected_tag}")
            tag_memos = api.get_memos_by_tag(st.session_state.selected_tag)
            
            if tag_memos:
                for memo in tag_memos:
                    with st.expander(f"📄 {memo['title']}"):
                        st.write(f"**内容:** {memo['content'][:100]}...")
                        st.write(f"**タグ:** {', '.join(memo['tags'])}")
                        if st.button("編集", key=f"edit_tag_{memo['id']}"):
                            st.session_state.current_memo_id = memo['id']
                            st.session_state.selected_tag = None
                            st.rerun()
            else:
                st.info(f"タグ '{st.session_state.selected_tag}' のメモがありません")
        
        else:
            # メモ編集
            memo = api.get_memo(st.session_state.current_memo_id)
            if "error" not in memo:
                st.subheader("✏️ メモを編集")
                
                with st.form("edit_memo_form"):
                    title = st.text_input("タイトル", value=memo["title"])
                    content = st.text_area("内容", value=memo["content"], height=200)
                    tags_input = st.text_input("タグ（カンマ区切り）", value=", ".join(memo["tags"]))
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.form_submit_button("💾 更新", use_container_width=True):
                            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
                            result = api.update_memo(memo["id"], title, content, tags)
                            
                            if "error" in result:
                                st.error(f"エラー: {result['error']}")
                            else:
                                st.success("メモが更新されました！")
                                st.rerun()
                    
                    with col2:
                        if st.form_submit_button("🤖 AI再処理", use_container_width=True):
                            ai_res = api.ai_preview(content)
                            if "error" in ai_res:
                                st.error(ai_res["error"])
                            else:
                                # AI再処理結果をセッション状態に保存
                                st.session_state.ai_edit_result = ai_res
                                st.success("AI 再処理完了！下記の「適用」ボタンで反映できます")
                
                # AI再処理結果の表示と適用（編集画面用）
                if 'ai_edit_result' in st.session_state and st.session_state.ai_edit_result:
                    ai_res = st.session_state.ai_edit_result
                    st.markdown("### 🤖 AI再処理結果")
                    st.write("**要約:**")
                    st.write(ai_res.get("summary", "(なし)"))
                    st.write("**タグ候補:** " + ", ".join(ai_res.get("tags", [])))
                    
                    col_edit1, col_edit2 = st.columns(2)
                    with col_edit1:
                        if st.form_submit_button("📝 AI結果を適用して更新", key="apply_edit", use_container_width=True):
                            # AI結果を適用したタグリストを作成
                            manual_tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
                            combined_tags = list(set(manual_tags + ai_res.get("tags", [])))
                            
                            result = api.update_memo(memo["id"], title, content, combined_tags)
                            if "error" in result:
                                st.error(f"エラー: {result['error']}")
                            else:
                                st.success("AI結果を適用してメモが更新されました！")
                                st.session_state.ai_edit_result = None  # 結果をクリア
                                st.rerun()
                    
                    with col_edit2:
                        if st.form_submit_button("🗑️ 結果をクリア", key="clear_edit", use_container_width=True):
                            st.session_state.ai_edit_result = None
                            st.rerun()
                
                # 削除ボタン（フォーム外に配置）
                if st.button("🗑️ メモを削除", key="delete_memo", use_container_width=True):
                    result = api.delete_memo(memo["id"])
                    if "error" in result:
                        st.error(f"エラー: {result['error']}")
                    else:
                        st.session_state.current_memo_id = None
                        st.success("メモが削除されました！")
                        st.rerun()
            else:
                st.error("メモが見つかりません")
                st.session_state.current_memo_id = None
    
    with col2:
        # メモ詳細表示
        if st.session_state.current_memo_id:
            memo = api.get_memo(st.session_state.current_memo_id)
            if "error" not in memo:
                st.subheader("📄 メモ詳細")
                
                # メモカード
                st.markdown(f"""
                <div class="memo-card">
                    <h3>{memo['title']}</h3>
                    <p><strong>作成日:</strong> {memo['created_at'][:10]}</p>
                    <p><strong>更新日:</strong> {memo['updated_at'][:10]}</p>
                    <p><strong>ステータス:</strong> {memo['status']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 要約
                if memo.get("summary"):
                    st.markdown(f"""
                    <div class="summary-box">
                        <h4>📝 AI要約</h4>
                        <p>{memo['summary']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # タグ
                if memo["tags"]:
                    st.subheader("🏷️ タグ")
                    tag_html = ""
                    for tag in memo["tags"]:
                        tag_html += f'<span class="tag-chip">{tag}</span>'
                    st.markdown(tag_html, unsafe_allow_html=True)
                
                # 内容プレビュー
                st.subheader("📝 内容プレビュー")
                st.text_area("内容", value=memo["content"], height=150, disabled=True)
        
        # 検索結果表示
        elif search_query:
            st.subheader("🔍 検索結果")
            search_results = api.search_memos(search_query)
            if search_results:
                for memo in search_results:
                    with st.expander(f"📄 {memo['title']}"):
                        st.write(f"**内容:** {memo['content'][:100]}...")
                        st.write(f"**タグ:** {', '.join(memo['tags'])}")
                        if st.button("編集", key=f"edit_{memo['id']}"):
                            st.session_state.current_memo_id = memo['id']
                            st.rerun()
            else:
                st.info("検索結果がありません")

if __name__ == "__main__":
    main() 