<div align="center">

# 🛡️ EVM Risk Intelligence Platform

**Sub-second stream processing, graph-based feature engineering, and Explainable AI (XAI) for EVM transaction risk & fraud detection.**

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.0-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-FF6F00?style=for-the-badge&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io)
[![Redis](https://img.shields.io/badge/Redis-Sliding_Feature_Store-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

## 📌 Executive Summary

While EVM-compatible public blockchains offer complete transaction transparency, they lack intrinsic security mechanisms to detect fraudulent or malicious activity in real time. The **EVM Risk Intelligence Platform** is an enterprise-grade transaction surveillance platform that streams live EVM mempool and block data, computes dynamic graph and behavioral features in memory, applies a hybrid **Rule Engine + Machine Learning (XGBoost)** model, and outputs sub-second risk scores with **SHAP-based human explanations**.

Built for compliance teams, security analysts, and Web3 protocols to monitor, detect, and investigate money laundering, phishing attacks, stolen wallet drains, and scam contracts in real time.

---

## 🏗️ System Architecture

```text
┌────────────────────────┐
│   EVM WEBSOCKET NODE   │
│ (Ethereum, Polygon,    │
│  Arbitrum, BSC, etc.)  │
└───────────┬────────────┘
            │ Real-time Stream
            ▼
┌────────────────────────┐
│ DATA VALIDATION & DLQ  │ ◄── [Redis Bloom Filter Deduplication]
│  (Dead Letter Queue)   │
└───────────┬────────────┘
            │ Validated Payloads
            ▼
┌────────────────────────┐
│ IN-MEMORY FEATURE STORE│ ◄── [Redis Sliding Windows: 1h, 24h, 7d]
│ Transaction / Behavioral│
└───────────┬────────────┘
            │ Real-time Feature Vector
            ▼
┌────────────────────────┐
│  HYBRID RISK ENGINE    │ ───► [Deterministic Sanction Rules]
│  (XGBoost + SHAP XAI)  │ ───► [ML Probability Scoring (0-100)]
└───────────┬────────────┘
            │ Score + SHAP Explanation Drivers
            ▼
┌────────────────────────┐
│   LIVE DASHBOARD &     │ ───► [WebSockets / SSE]
│  INVESTIGATOR PORTAL   │ ───► [Cytoscape.js Transaction Graph]
└────────────────────────┘
```

---

## ✨ Key Features

* **⚡ Real-Time Multi-Chain Ingestion:** Asynchronous WebSocket listeners processing block and mempool data across EVM networks via Web3.py.
* **🧠 Real-Time Feature Engineering:** Low-latency sliding-window aggregation using Redis sorted sets (`ZADD`) for velocity, account balance variance, and interaction frequency.
* **⚖️ Hybrid Risk Engine:** Combines instant heuristic sanctions checking (OFAC, Tornado Cash interactions) with continuous probability scoring from an optimized XGBoost classifier.
* **🔍 Explainable AI (SHAP):** Translates complex model parameters into actionable text explanations for compliance teams (e.g., *"Velocity burst: 14 transactions within 180 seconds"*).
* **🕸️ Interactive Graph Visualization:** Displays 2-hop wallet relationship graphs using Cytoscape.js to expose money laundering rings and fan-out structures.
* **🔐 Enterprise Access & Case Workflow:** Role-Based Access Control (RBAC) supporting Web3 wallet signatures (SIWE - Sign-In with Ethereum) and standard OAuth2, complete with a multi-stage case management Kanban board.

---

## 🛠️ Tech Stack

| Layer | Technology |
| --- | --- |
| **Blockchain Client** | Web3.py, WebSockets, Ethers.js, Anvil / Hardhat (Local Forking) |
| **Backend & Ingestion** | Python 3.11, FastAPI, Pydantic, Asyncio |
| **In-Memory Feature Store** | Redis (Sliding window key-value cache, Pub/Sub) |
| **Machine Learning & XAI** | XGBoost, LightGBM, SHAP, Scikit-learn, Pandas |
| **Database** | PostgreSQL, SQLAlchemy, Alembic |
| **Frontend Dashboard** | Next.js 14, React, Tailwind CSS, Cytoscape.js, Recharts |
| **Security & Auth** | Web3 SIWE (Sign-In with Ethereum), PyJWT, Passlib (bcrypt) |

---

## 🚀 Quickstart Guide

### Prerequisites

* **Python 3.11+**
* **Node.js 18+**
* **Redis Server** (Running on port `6379`)
* **EVM RPC Node URL** (Alchemy, Infura, or Ankr)

### 1. Clone & Setup Environment

```bash
git clone https://github.com/vikassm0007-arch/eth-risk-intelligence-engine.git
cd eth-risk-intelligence-engine
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI Server & Ingestion Engine
python -m uvicorn backend.main:app --reload --port 8001
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run Development Server
npm run dev -p 3001
```

Navigate to `http://localhost:3001` to view the dashboard.

---

## 📊 Risk Engine & SHAP Output Sample

When a transaction is flagged, the platform produces a JSON payload containing both quantitative metrics and natural language explanations:

```json
{
  "tx_hash": "0x8f3c...b210",
  "from_address": "0x71C...a49B",
  "to_address": "0x12D...e811",
  "risk_score": 87.4,
  "risk_level": "HIGH",
  "shap_explanations": [
    {
      "feature": "velocity_burst_5m",
      "effect": "+32.1",
      "reason": "High transaction velocity: 11 transactions within 5 minutes."
    },
    {
      "feature": "drain_ratio",
      "effect": "+24.5",
      "reason": "Single transaction moved 94% of total account balance."
    }
  ],
  "action_required": "Escalate to Senior Investigator"
}
```

---

## 💼 Case Management Lifecycle

1. **Auto-Alert Triggered:** Risk engine flags transactions with a score $> 70$.
2. **Case Creation:** Automatically assigned to the analyst queue via WebSockets.
3. **Analyst Review:** Investigator examines the Cytoscape 2-hop transaction graph, historical wallet activity, and SHAP drivers.
4. **Resolution & Feedback Loop:** Analyst sets status to `True Positive` or `False Positive`, continuously improving the underlying ML model.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
