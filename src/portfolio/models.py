#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.security.db import Base


class PortfolioModel(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128), default="default")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    holdings: Mapped[list["HoldingModel"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )


class HoldingModel(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))
    code: Mapped[str] = mapped_column(String(8), index=True)  # 例: "7203"
    side: Mapped[str] = mapped_column(String(4))  # BUY or SELL
    price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[int] = mapped_column(Integer)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    portfolio: Mapped[PortfolioModel] = relationship(back_populates="holdings")


