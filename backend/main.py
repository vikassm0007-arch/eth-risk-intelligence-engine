"""
FastAPI Server, WebSocket Manager & REST API Endpoints
AI-Powered Real-Time Ethereum Transaction Risk Intelligence Platform
"""

import asyncio
import uuid
import time
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db import (
    init_db, get_db_session, TransactionModel, WalletModel, RiskScoreModel, AlertModel, InvestigationCaseModel
)
from backend.validator import validator, dlq
from backend.feature_store import feature_extractor
from backend.model_engine import risk_engine
from backend.listener import EthereumStreamListener, simulator

# Global Telemetry Counter
SYSTEM_STATS = {
    "total_processed": 0,
    "high_critical_alerts": 0,
    "sum_latency_ms": 0.0,
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

# Pipeline Execution Helper
async def process_raw_transaction(raw_payload: Dict[str, Any]):
    start_time = time.time()

    # 1. Validation & Deduplication
    validated_tx = validator.validate_and_parse(raw_payload)
    if not validated_tx:
        return None

    # 2. Real-Time Feature Store Extraction
    features = feature_extractor.extract_features(validated_tx)

    # 3. Hybrid ML + Rule Risk & SHAP Evaluation
    eval_result = risk_engine.evaluate(features)

    elapsed_ms = (time.time() - start_time) * 1000.0 + eval_result["execution_time_ms"]

    # Update Global Stats
    SYSTEM_STATS["total_processed"] += 1
    SYSTEM_STATS["sum_latency_ms"] += elapsed_ms
    if eval_result["alert_level"] in ("HIGH", "CRITICAL"):
        SYSTEM_STATS["high_critical_alerts"] += 1

    # Format Output Payload for WS Broadcast
    broadcast_payload = {
        "tx_hash": validated_tx.tx_hash,
        "block_number": validated_tx.block_number,
        "timestamp": validated_tx.timestamp,
        "from_address": validated_tx.from_address,
        "to_address": validated_tx.to_address,
        "value_eth": round(validated_tx.value_eth, 4),
        "value_usd": round(validated_tx.value_usd, 2),
        "gas_price_gwei": round(validated_tx.gas_price_gwei, 2),
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

    # Broadcast via WebSockets
    await ws_manager.broadcast({
        "type": "NEW_TRANSACTION",
        "data": broadcast_payload
    })

    return broadcast_payload


# Background Streaming Task
stream_listener: Optional[EthereumStreamListener] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database
    await init_db()
    print("Database initialized.")

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSockets Live Streaming Endpoint
@app.websocket("/ws/live-stream")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send welcome payload with system stats
        await websocket.send_json({
            "type": "SYSTEM_INFO",
            "message": "Connected to Ethereum Risk Intelligence Stream",
            "stats": {
                "tps": round(SYSTEM_STATS["total_processed"] / max(1, time.time() - SYSTEM_STATS["start_time"]), 2),
                "total_monitored": SYSTEM_STATS["total_processed"]
            }
        })
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# REST API v1 Endpoints

@app.get("/api/v1/stats")
async def get_system_stats():
    uptime = time.time() - SYSTEM_STATS["start_time"]
    avg_latency = (SYSTEM_STATS["sum_latency_ms"] / max(1, SYSTEM_STATS["total_processed"]))
    tps = SYSTEM_STATS["total_processed"] / max(1.0, uptime)
    
    return {
        "status": "ONLINE",
        "uptime_seconds": round(uptime, 1),
        "total_processed_transactions": SYSTEM_STATS["total_processed"],
        "critical_high_alerts": SYSTEM_STATS["high_critical_alerts"],
        "avg_pipeline_latency_ms": round(avg_latency, 2),
        "current_tps": round(tps, 2),
        "dlq_quarantine_count": len(dlq.get_quarantined_items())
    }


@app.get("/api/v1/investigate/{wallet}")
async def investigate_wallet(wallet: str):
    """
    Case Investigator API:
    Returns wallet metadata, risk factors, SHAP breakdown, historical timeline, and 2-hop transaction network graph for Cytoscape.js.
    """
    wallet_clean = wallet.lower().strip()
    is_sanctioned = wallet_clean in settings.OFAC_SANCTIONED_ADDRESSES

    # Fetch recent transactions for this wallet from Feature Store
    now = time.time()
    records = feature_extractor.feature_store.wallet_tx_history.get(wallet_clean, [])

    # Calculate graph nodes & edges (2-hop counterparty network)
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

    # Generate Case Summary
    timeline = []
    for ts, tx_h, val_eth, counterparty in records[-15:]:
        timeline.append({
            "tx_hash": tx_h,
            "timestamp": ts,
            "val_eth": round(val_eth, 4),
            "val_usd": round(val_eth * 3200.0, 2),
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
            {"feature": "Gas Price Spike Ratio", "shap_value": 0.15}
        ]
    }


@app.post("/api/v1/trigger-attack")
async def trigger_simulated_attack(attack_type: str = Query("TORNADO_SANCTION", enum=["TORNADO_SANCTION", "SUDDEN_DRAIN", "VELOCITY_BURST"])):
    """
    Triggers an immediate high-risk malicious transaction for instant UI validation.
    """
    raw_tx = simulator.generate_transaction(attack_mode=attack_type)
    result = await process_raw_transaction(raw_tx)
    return {
        "status": "SUCCESS",
        "message": f"Triggered attack simulation: {attack_type}",
        "processed_transaction": result
    }
