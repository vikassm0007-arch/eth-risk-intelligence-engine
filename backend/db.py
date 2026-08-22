"""
Database Models & Connection Pool (Phase 3 History & Audit Logging)
AI-Powered Real-Time Ethereum Transaction Risk Intelligence Platform
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import (
    Column, String, BigInteger, Float, Boolean, DateTime, Text, ForeignKey, Integer, func
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.config import settings

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    wallet_address = Column(String(42), unique=True, nullable=True, index=True)
    role = Column(String(50), nullable=False, default="Junior Analyst")
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

    assigned_cases = relationship("CaseModel", back_populates="assigned_analyst")
    notes = relationship("CaseNoteModel", back_populates="author")


class TransactionsHistoryModel(Base):
    __tablename__ = "transactions_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    block_number = Column(BigInteger, nullable=True)
    from_addr = Column(String(42), nullable=False, index=True)
    to_addr = Column(String(42), nullable=True, index=True)
    value_eth = Column(Float, nullable=False)
    value_inr = Column(Float, nullable=False)
    gas_price_gwei = Column(Float, nullable=False)
    gas_inr = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    explanations = relationship("RiskExplanationsModel", back_populates="transaction", cascade="all, delete-orphan")


class RiskExplanationsModel(Base):
    __tablename__ = "risk_explanations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(66), ForeignKey("transactions_history.tx_hash", ondelete="CASCADE"), nullable=False)
    feature_name = Column(String(100), nullable=False)
    shap_value = Column(Float, nullable=False)
    explanation_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("TransactionsHistoryModel", back_populates="explanations")


class WalletProfilesModel(Base):
    __tablename__ = "wallet_profiles"

    address = Column(String(42), primary_key=True, index=True)
    total_tx_count = Column(Integer, default=1)
    high_risk_tx_count = Column(Integer, default=0)
    total_volume_inr = Column(Float, default=0.0)
    is_sanctioned = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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


class RiskScoreModel(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(66), ForeignKey("transactions.tx_hash", ondelete="CASCADE"), nullable=False, unique=True)
    ml_probability = Column(Float, nullable=False)
    rule_risk_score = Column(Float, nullable=False)
    composite_risk_score = Column(Float, nullable=False)
    alert_level = Column(String(20), nullable=False)
    execution_time_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("TransactionModel", back_populates="risk_score")


class AlertModel(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(66), ForeignKey("transactions.tx_hash", ondelete="CASCADE"), nullable=False, unique=True)
    alert_level = Column(String(20), nullable=False)
    summary = Column(Text, nullable=False)
    top_shap_drivers_json = Column(Text, nullable=False)
    status = Column(String(20), default="UNRESOLVED")
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("TransactionModel", back_populates="alert")


class CaseModel(Base):
    __tablename__ = "cases"

    id = Column(String(36), primary_key=True)
    tx_hash = Column(String(66), nullable=False, index=True)
    wallet_address = Column(String(42), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    alert_level = Column(String(20), nullable=False)
    status = Column(String(30), default="NEW ALERT")
    priority = Column(String(20), default="HIGH")
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to_name = Column(String(100), nullable=True)
    flagged_value_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_analyst = relationship("UserModel", back_populates="assigned_cases")
    notes = relationship("CaseNoteModel", back_populates="case", cascade="all, delete-orphan")


class CaseNoteModel(Base):
    __tablename__ = "case_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author_name = Column(String(100), nullable=False)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="notes")
    author = relationship("UserModel", back_populates="notes")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)
    target_resource = Column(String(255), nullable=False)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Async Engine & Session Setup
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session
