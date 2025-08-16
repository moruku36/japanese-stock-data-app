#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
from pathlib import Path


def _sqlite_url(tmp_name: str) -> str:
    p = Path(tempfile.gettempdir()) / tmp_name
    # Windowsでも通るようにスラッシュに正規化
    return "sqlite:///" + str(p).replace("\\", "/")


def test_create_and_authenticate_user_db(monkeypatch):
    # 必須ENV設定
    monkeypatch.setenv("JWT_SECRET_KEY", "dev_secret")
    monkeypatch.setenv("SECURITY_PASSWORD", "pw")
    monkeypatch.setenv("SECURITY_SALT", "salt")
    monkeypatch.setenv("DATABASE_URL", _sqlite_url("test_security.sqlite3"))

    from src.security.enhanced_security_manager import (
        EnhancedSecurityManager,
        UserRole,
    )

    sm = EnhancedSecurityManager()

    user = sm.create_user("u1", "u1@example.com", "Passw0rd!", UserRole.STANDARD)
    assert user is not None
    assert user.username == "u1"

    sid = sm.authenticate_user("u1", "Passw0rd!")
    assert sid is not None

    # 間違いパスワード
    sid2 = sm.authenticate_user("u1", "wrong")
    assert sid2 is None


