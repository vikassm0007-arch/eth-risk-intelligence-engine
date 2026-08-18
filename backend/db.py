"""
Database Models & Connection Pool
AI-Powered Real-Time Ethereum Transaction Risk Intelligence Platform
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import (
    Column, String, BigInteger, Float, Boolean, DateTime, Text, ForeignKey, Integer, func
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.config import settings

Base = declarative_base()

class TransactionModel(Base):
    __tablename__ = "transactions"

    tx_hash = Column(String(66), primary_key=True, index=True)
    block_number = Column(BigInteger, nullable=True)
    block_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    from_address = Column(String(42), nullable=False, index=True)
    to_address = Column(String(42), nullable=True, index=True)
    value_eth = Column(Float, nullable=False)
    value_usd = Column(Float, nullable=False)
    gas_price_gwei = Column(Float, nullable=False)
    gas_limit = Column(BigInteger, nullable=False)
    nonce = Column(BigInteger, nullable=False)
    input_data = Column(Text, nullable=True)
    is_erc20 = Column(Boolean, default=False)
    erc20_method = Column(String(10), nullable=True)
    is_unavailable_flag = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    risk_score = relationship("RiskScoreModel", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    alert = relationship("AlertModel", back_populates="transaction", uselist=False, cascade="all, delete-orphan")


class WalletModel(Base):
    __tablename__ = "wallets"

    address = Column(String(42), primary_key=True, index=True)
    first_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_tx_count = Column(Integer, default=1)
    is_sanctioned = Column(Boolean, default=False)
    is_contract = Column(Boolean, default=False)
    total_eth_sent = Column(Float, default=0.0)
    total_eth_received = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cases = relationship("InvestigationCaseModel", back_populates="wallet")


class RiskScoreModel(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(66), ForeignKey("transactions.tx_hash", ondelete="CASCADE"), nullable=False, unique=True)
    ml_probability = Column(Float, nullable=False)
    rule_risk_score = Column(Float, nullable=False)
    composite_risk_score = Column(Float, nullable=False)
    alert_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    execution_time_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    transaction = relationship("TransactionModel", back_populates="risk_score")


class AlertModel(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(66), ForeignKey("transactions.tx_hash", ondelete="CASCADE"), nullable=False, unique=True)
    alert_level = Column(String(20), nullable=False)
    summary = Column(Text, nullable=False)
    top_shap_drivers_json = Column(Text, nullable=False)  # Stored as JSON string
    status = Column(String(20), default="UNRESOLVED")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    transaction = relationship("TransactionModel", back_populates="alert")


class InvestigationCaseModel(Base):
    __tablename__ = "investigation_cases"

    case_id = Column(String(36), primary_key=True)
    wallet_address = Column(String(42), ForeignKey("wallets.address"), nullable=False)
    status = Column(String(20), default="OPEN")  # OPEN, IN_REVIEW, CLOSED
    priority = Column(String(20), default="HIGH")
    risk_score = Column(Float, nullable=False)
    open_alerts_count = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    wallet = relationship("WalletModel", back_populates="cases")


# Async Engine & Session Setup
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
