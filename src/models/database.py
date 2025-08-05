from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# データベース設定
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./memo_app.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# タグとメモの多対多関係のための中間テーブル
memo_tags = Table(
    'memo_tags',
    Base.metadata,
    Column('memo_id', String, ForeignKey('memos.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Memo(Base):
    """メモテーブル"""
    __tablename__ = "memos"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(String(20), default="draft", index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)
    
    # リレーションシップ
    tags = relationship("Tag", secondary=memo_tags, back_populates="memos")
    
    def to_dict(self) -> dict:
        """メモを辞書形式に変換"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "status": self.status,
            "tags": [tag.name for tag in self.tags],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Tag(Base):
    """タグテーブル"""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    
    # リレーションシップ
    memos = relationship("Memo", secondary=memo_tags, back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(name='{self.name}')>"

# データベースの初期化
def init_db():
    """データベースを初期化"""
    Base.metadata.create_all(bind=engine)

# FastAPI専用: Dependency Injection用のジェネレーター関数
def get_db():
    """FastAPI用データベースセッション取得（Dependency Injection用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 