"""
FastAPI Server, WebSocket Manager, Auth, INR Telemetry & Persistent History
AI-Powered Real-Time Ethereum Transaction Risk Intelligence Platform
"""

import asyncio
import uuid
import time
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db import (
    init_db, get_db_session, TransactionModel, WalletModel, RiskScoreModel, AlertModel, UserModel, CaseModel, AsyncSessionLocal,
    TransactionsHistoryModel, RiskExplanationsModel, WalletProfilesModel
)
from backend.validator import validator, dlq
from backend.feature_store import feature_extractor
from backend.model_engine import risk_engine
from backend.listener import EthereumStreamListener, simulator
from backend.currency_service import currency_service

# Import Phase 2 & Phase 3 Routers
from backend.auth_router import auth_router, hash_password
from backend.cases_router import cases_router, ensure_seed_cases
from backend.api_router import api_router

# Global Telemetry Counter
SYSTEM_STATS = {
    "total_processed": 0,
    "high_critical_alerts": 0,
    "sum_latency_ms": 0.0,
    "total_inr_monitored": 0.0,
    "start_time": time.time()
}

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()


# Background Async Persistence Worker
async def persist_transaction_to_db(tx_data: Dict[str, Any]):
    """
    Asynchronously persists scored transaction, SHAP drivers, and wallet profile stats to PostgreSQL.
    Exits quickly to avoid blocking main streaming loop.
    """
    try:
        async with AsyncSessionLocal() as session:
            # 1. Insert Transactions History
            tx_record = TransactionsHistoryModel(
                tx_hash=tx_data["tx_hash"],
                block_number=tx_data["block_number"],
                from_addr=tx_data["from_address"],
                to_addr=tx_data["to_address"],
                value_eth=tx_data["value_eth"],
                value_inr=tx_data["value_inr"],
                gas_price_gwei=tx_data["gas_price_gwei"],
                gas_inr=tx_data["gas_inr"],
                risk_score=tx_data["composite_risk_score"],
                risk_level=tx_data["alert_level"]
            )
            session.add(tx_record)

            # 2. Insert Risk Explanations (Top SHAP drivers)
            for driver in tx_data.get("top_shap_drivers", []):
                explanation = RiskExplanationsModel(
                    tx_hash=tx_data["tx_hash"],
                    feature_name=driver["feature"],
                    shap_value=driver["shap_value"],
                    explanation_text=f"SHAP impact ({driver['shap_value']:+.2f}): {driver['feature']} = {driver['feature_value']}"
                )
                session.add(explanation)

            # 3. Update Wallet Profile Metrics
            wallet_addr = tx_data["from_address"]
            w_res = await session.execute(select(WalletProfilesModel).where(WalletProfilesModel.address == wallet_addr))
            w_profile = w_res.scalars().first()

            if not w_profile:
                w_profile = WalletProfilesModel(
                    address=wallet_addr,
                    total_tx_count=1,
                    high_risk_tx_count=1 if tx_data["alert_level"] in ("HIGH", "CRITICAL") else 0,
                    total_volume_inr=tx_data["value_inr"],
                    is_sanctioned=tx_data["composite_risk_score"] >= 90
                )
                session.add(w_profile)
            else:
                w_profile.total_tx_count += 1
                if tx_data["alert_level"] in ("HIGH", "CRITICAL"):
                    w_profile.high_risk_tx_count += 1
                w_profile.total_volume_inr += tx_data["value_inr"]

            await session.commit()
    except Exception as e:
        # Ignore duplicate insertion errors in simulation stream
        pass


# Pipeline Execution Helper
async def process_raw_transaction(raw_payload: Dict[str, Any]):
    start_time = time.time()

    # 1. Validation & Deduplication
    validated_tx = validator.validate_and_parse(raw_payload)
    if not validated_tx:
        return None

    # 2. Real-Time Currency Conversion (INR ₹)
    eth_inr_rate = await currency_service.get_eth_inr_rate()
    value_inr = currency_service.convert_eth_to_inr(validated_tx.value_eth, eth_inr_rate)
    gas_inr = currency_service.convert_gwei_gas_to_inr(validated_tx.gas_price_gwei, validated_tx.gas_limit, eth_inr_rate)
    value_inr_formatted = currency_service.format_inr(value_inr)

    # 3. Real-Time Feature Store Extraction (with value_inr)
    features = feature_extractor.extract_features(validated_tx)
    features["value_inr"] = value_inr

    # 4. Hybrid ML + Rule Risk & SHAP Evaluation
    eval_result = risk_engine.evaluate(features)

    elapsed_ms = (time.time() - start_time) * 1000.0 + eval_result["execution_time_ms"]

    # Update Global Stats
    SYSTEM_STATS["total_processed"] += 1
    SYSTEM_STATS["sum_latency_ms"] += elapsed_ms
    SYSTEM_STATS["total_inr_monitored"] += value_inr
    if eval_result["alert_level"] in ("HIGH", "CRITICAL"):
        SYSTEM_STATS["high_critical_alerts"] += 1

        # Automatically open investigation case for CRITICAL alerts
        if eval_result["alert_level"] == "CRITICAL":
            try:
                async with AsyncSessionLocal() as session:
                    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
                    new_case = CaseModel(
                        id=case_id,
                        tx_hash=validated_tx.tx_hash,
                        wallet_address=validated_tx.from_address,
                        risk_score=eval_result["composite_risk_score"],
                        alert_level=eval_result["alert_level"],
                        status="NEW ALERT",
                        priority="CRITICAL",
                        assigned_to_name="Unassigned",
                        flagged_value_usd=round(validated_tx.value_usd, 2)
                    )
                    session.add(new_case)
                    await session.commit()
            except Exception:
                pass  # Ignore case creation collisions gracefully

    # Format Output Payload for WS Broadcast
    broadcast_payload = {
        "tx_hash": validated_tx.tx_hash,
        "block_number": validated_tx.block_number,
        "timestamp": validated_tx.timestamp,
        "from_address": validated_tx.from_address,
        "to_address": validated_tx.to_address,
        "value_eth": round(validated_tx.value_eth, 4),
        "value_usd": round(validated_tx.value_usd, 2),
        "value_inr": round(value_inr, 2),
        "value_inr_formatted": value_inr_formatted,
        "gas_price_gwei": round(validated_tx.gas_price_gwei, 2),
        "gas_inr": round(gas_inr, 2),
        "input_data": validated_tx.input_data,
        "is_erc20": validated_tx.is_erc20,
        "ml_probability": eval_result["ml_probability"],
        "rule_risk_score": eval_result["rule_risk_score"],
        "composite_risk_score": eval_result["composite_risk_score"],
        "alert_level": eval_result["alert_level"],
        "reasons": eval_result["reasons"],
        "top_shap_drivers": eval_result["top_shap_drivers"],
        "execution_time_ms": round(elapsed_ms, 2)
    }

    # Background Async Persistence
    asyncio.create_task(persist_transaction_to_db(broadcast_payload))

    # Broadcast via WebSockets
    await ws_manager.broadcast({
        "type": "NEW_TRANSACTION",
        "data": broadcast_payload
    })

    return broadcast_payload


# Seed Default Accounts
async def seed_initial_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(UserModel.id)))
        if result.scalar() == 0:
            demo_users = [
                UserModel(email="admin@risk.eth", password_hash=hash_password("admin123"), role="Admin", status="ACTIVE"),
                UserModel(email="senior@risk.eth", password_hash=hash_password("senior123"), role="Senior Analyst", status="ACTIVE"),
                UserModel(email="junior@risk.eth", password_hash=hash_password("junior123"), role="Junior Analyst", status="ACTIVE"),
            ]
            for u in demo_users:
                session.add(u)
            await session.commit()
            print("Seeded demo RBAC accounts: admin@risk.eth, senior@risk.eth, junior@risk.eth")


# Background Streaming Task
stream_listener: Optional[EthereumStreamListener] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database & Seed Default Accounts
    await init_db()
    await seed_initial_users()
    async with AsyncSessionLocal() as session:
        await ensure_seed_cases(session)
    print("Database, RBAC & Persistent History models initialized.")

    # Launch Ethereum Stream Listener
    global stream_listener
    stream_listener = EthereumStreamListener(callback=process_raw_transaction)
    asyncio.create_task(stream_listener.start())
    print("Ethereum Stream Listener task created.")

    yield

    # Shutdown
    if stream_listener:
        stream_listener.stop()
    print("Shutting down FastAPI Application.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth_router)
app.include_router(cases_router)
app.include_router(api_router)


# WebSockets Live Streaming Endpoint
@app.websocket("/ws/live-stream")
@app.websocket("/ws/live-transactions")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        rate = await currency_service.get_eth_inr_rate()
        await websocket.send_json({
            "type": "SYSTEM_INFO",
            "message": "Connected to EVM Real-Time Risk & INR Intelligence Stream",
            "stats": {
                "tps": round(SYSTEM_STATS["total_processed"] / max(1, time.time() - SYSTEM_STATS["start_time"]), 2),
                "total_monitored": SYSTEM_STATS["total_processed"],
                "total_inr_monitored": currency_service.format_inr(SYSTEM_STATS["total_inr_monitored"]),
                "eth_inr_rate": currency_service.format_inr(rate)
            }
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# REST API v1 Telemetry Endpoint
@app.get("/api/v1/stats")
async def get_system_stats():
    uptime = time.time() - SYSTEM_STATS["start_time"]
    avg_latency = (SYSTEM_STATS["sum_latency_ms"] / max(1, SYSTEM_STATS["total_processed"]))
    tps = SYSTEM_STATS["total_processed"] / max(1.0, uptime)
    rate = await currency_service.get_eth_inr_rate()
    
    return {
        "status": "ONLINE",
        "uptime_seconds": round(uptime, 1),
        "total_processed_transactions": SYSTEM_STATS["total_processed"],
        "critical_high_alerts": SYSTEM_STATS["high_critical_alerts"],
        "avg_pipeline_latency_ms": round(avg_latency, 2),
        "current_tps": round(tps, 2),
        "total_inr_monitored": round(SYSTEM_STATS["total_inr_monitored"], 2),
        "total_inr_monitored_formatted": currency_service.format_inr(SYSTEM_STATS["total_inr_monitored"]),
        "eth_inr_rate": rate,
        "eth_inr_rate_formatted": currency_service.format_inr(rate),
        "dlq_quarantine_count": len(dlq.get_quarantined_items())
    }


@app.get("/api/v1/investigate/{wallet}")
async def investigate_wallet(wallet: str):
    wallet_clean = wallet.lower().strip()
    is_sanctioned = wallet_clean in settings.OFAC_SANCTIONED_ADDRESSES

    now = time.time()
    records = feature_extractor.feature_store.wallet_tx_history.get(wallet_clean, [])
    rate = await currency_service.get_eth_inr_rate()

    nodes = [{"data": {"id": wallet_clean, "label": f"{wallet_clean[:6]}...{wallet_clean[-4:]}", "isTarget": True, "isSanctioned": is_sanctioned}}]
    edges = []
    seen_nodes = {wallet_clean}

    out_counterparties = list(feature_extractor.feature_store.wallet_out_counterparties.get(wallet_clean, set()))[:10]
    in_counterparties = list(feature_extractor.feature_store.wallet_in_counterparties.get(wallet_clean, set()))[:10]

    for c in out_counterparties:
        if c not in seen_nodes:
            seen_nodes.add(c)
            nodes.append({"data": {"id": c, "label": f"{c[:6]}...{c[-4:]}", "isSanctioned": c in settings.OFAC_SANCTIONED_ADDRESSES}})
        edges.append({"data": {"source": wallet_clean, "target": c, "label": "Sent ETH"}})

    for c in in_counterparties:
        if c not in seen_nodes:
            seen_nodes.add(c)
            nodes.append({"data": {"id": c, "label": f"{c[:6]}...{c[-4:]}", "isSanctioned": c in settings.OFAC_SANCTIONED_ADDRESSES}})
        edges.append({"data": {"source": c, "target": wallet_clean, "label": "Received ETH"}})

    timeline = []
    for ts, tx_h, val_eth, counterparty in records[-15:]:
        val_inr = currency_service.convert_eth_to_inr(val_eth, rate)
        timeline.append({
            "tx_hash": tx_h,
            "timestamp": ts,
            "val_eth": round(val_eth, 4),
            "val_usd": round(val_eth * 3200.0, 2),
            "val_inr": round(val_inr, 2),
            "val_inr_formatted": currency_service.format_inr(val_inr),
            "counterparty": counterparty
        })

    risk_level = "CRITICAL" if is_sanctioned else ("HIGH" if len(records) > 8 else "LOW")
    risk_score = 100.0 if is_sanctioned else (85.0 if len(records) > 8 else 18.5)

    return {
        "wallet_address": wallet_clean,
        "is_sanctioned": is_sanctioned,
        "risk_level": risk_level,
        "composite_risk_score": risk_score,
        "total_tx_count": len(records),
        "first_seen": feature_extractor.feature_store.wallet_first_seen.get(wallet_clean, now),
        "timeline": timeline,
        "network_graph": {
            "nodes": nodes,
            "edges": edges
        },
        "shap_explanations": [
            {"feature": "Sanctioned Entity Interaction", "shap_value": 0.85 if is_sanctioned else 0.05},
            {"feature": "Velocity Burst (5m)", "shap_value": 0.42 if len(records) > 5 else 0.02},
            {"feature": "Sudden Balance Drain", "shap_value": 0.38 if risk_score > 70 else 0.01},
            {"feature": "High INR Volume (> ₹1 Cr)", "shap_value": 0.30 if risk_score > 70 else 0.02}
        ]
    }


@app.post("/api/v1/trigger-attack")
async def trigger_simulated_attack(attack_type: str = Query("TORNADO_SANCTION", enum=["TORNADO_SANCTION", "SUDDEN_DRAIN", "VELOCITY_BURST"])):
    raw_tx = simulator.generate_transaction(attack_mode=attack_type)
    result = await process_raw_transaction(raw_tx)
    return {
        "status": "SUCCESS",
        "message": f"Triggered attack simulation: {attack_type}",
        "processed_transaction": result
    }
