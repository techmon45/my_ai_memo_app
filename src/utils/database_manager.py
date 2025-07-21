from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from src.models.database import get_db, Memo, Tag, init_db

class DatabaseManager:
    """データベース操作を管理するクラス"""
    
    def __init__(self):
        # データベースの初期化
        init_db()
    
    def create_memo(self, title: str, content: str, tags: List[str] = None, summary: str = None) -> Dict[str, Any]:
        """メモを作成"""
        db = next(get_db())
        try:
            memo_id = str(uuid.uuid4())
            
            # メモを作成
            memo = Memo(
                id=memo_id,
                title=title,
                content=content,
                summary=summary,
                status="draft"
            )
            
            # タグを処理
            if tags:
                for tag_name in tags:
                    tag = self._get_or_create_tag(db, tag_name)
                    memo.tags.append(tag)
            
            db.add(memo)
            db.commit()
            db.refresh(memo)
            
            return memo.to_dict()
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_memo(self, memo_id: str) -> Optional[Dict[str, Any]]:
        """メモを取得"""
        db = next(get_db())
        try:
            memo = db.query(Memo).filter(Memo.id == memo_id).first()
            return memo.to_dict() if memo else None
        finally:
            db.close()
    
    def list_memos(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """すべてのメモを取得"""
        db = next(get_db())
        try:
            memos = db.query(Memo).order_by(Memo.updated_at.desc()).offset(offset).limit(limit).all()
            return [memo.to_dict() for memo in memos]
        finally:
            db.close()
    
    def update_memo(self, memo_id: str, title: str = None, content: str = None, 
                   tags: List[str] = None, summary: str = None) -> Optional[Dict[str, Any]]:
        """メモを更新"""
        db = next(get_db())
        try:
            memo = db.query(Memo).filter(Memo.id == memo_id).first()
            if not memo:
                return None
            
            # フィールドを更新
            if title is not None:
                memo.title = title
            if content is not None:
                memo.content = content
            if summary is not None:
                memo.summary = summary
            
            # タグを更新
            if tags is not None:
                memo.tags.clear()
                for tag_name in tags:
                    tag = self._get_or_create_tag(db, tag_name)
                    memo.tags.append(tag)
            
            memo.updated_at = datetime.now()
            db.commit()
            db.refresh(memo)
            
            return memo.to_dict()
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def delete_memo(self, memo_id: str) -> bool:
        """メモを削除"""
        db = next(get_db())
        try:
            memo = db.query(Memo).filter(Memo.id == memo_id).first()
            if not memo:
                return False
            
            db.delete(memo)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def search_memos(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """メモを検索"""
        db = next(get_db())
        try:
            # タイトル、内容、タグで検索
            search_filter = or_(
                Memo.title.ilike(f"%{query}%"),
                Memo.content.ilike(f"%{query}%"),
                Tag.name.ilike(f"%{query}%")
            )
            
            memos = db.query(Memo).join(Memo.tags, isouter=True).filter(search_filter).distinct().order_by(Memo.updated_at.desc()).limit(limit).all()
            return [memo.to_dict() for memo in memos]
            
        finally:
            db.close()
    
    def get_memos_by_tag(self, tag_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """タグでメモを検索"""
        db = next(get_db())
        try:
            memos = db.query(Memo).join(Memo.tags).filter(Tag.name == tag_name).order_by(Memo.updated_at.desc()).limit(limit).all()
            return [memo.to_dict() for memo in memos]
        finally:
            db.close()
    
    def get_all_tags(self) -> List[str]:
        """すべてのタグを取得"""
        db = next(get_db())
        try:
            tags = db.query(Tag.name).all()
            return [tag[0] for tag in tags]
        finally:
            db.close()
    
    def get_memo_count(self) -> int:
        """メモの総数を取得"""
        db = next(get_db())
        try:
            return db.query(Memo).count()
        finally:
            db.close()
    
    def _get_or_create_tag(self, db: Session, tag_name: str) -> Tag:
        """タグを取得または作成"""
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        return tag 