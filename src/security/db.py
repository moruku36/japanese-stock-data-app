#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
認証・ユーザー情報のDB層
開発: SQLite、 本番: 環境変数 DATABASE_URL (例: postgresql+psycopg://user:pass@host/db)
"""

import os
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, String, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default="standard")
    permissions: Mapped[str] = mapped_column(String(1024), default="")  # カンマ区切り
    password_hash: Mapped[str] = mapped_column(String(256))
    password_salt: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


def get_engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        # デフォルトはSQLiteローカル
        url = "sqlite:///security.sqlite3"
    return create_engine(url, future=True)


def get_session_factory():
    engine = get_engine()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


