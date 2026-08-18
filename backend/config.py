"""
System Configuration & Constants
AI-Powered Real-Time Ethereum Transaction Risk Intelligence Platform
"""

import os
from typing import List, Set

class Settings:
    PROJECT_NAME: str = "Ethereum Real-Time Risk Intelligence Platform"
    VERSION: str = "1.0.0"
    
    # RPC Failover URLs (Alchemy, Ankr, Cloudflare, Public Nodes)
    DEFAULT_RPC_ENDPOINTS: List[str] = [
        "https://cloudflare-eth.com",
        "https://rpc.ankr.com/eth",
        "https://ethereum.publicnode.com"
    ]
    
    # DB & Redis Config
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./eth_risk.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    USE_IN_MEMORY_REDIS_FALLBACK: bool = True  # Fallback to simulated Redis dict if Redis is offline
    
    # Sanctioned Entities & High-Risk Contracts (OFAC List & Known Mixers)
    OFAC_SANCTIONED_ADDRESSES: Set[str] = {
        "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",  # Tornado Cash Router
        "0x70e36f6bf80a52b3b46b3af8e106cc0ed743e8e4",  # Tornado Cash 100 ETH
        "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936",  # Tornado Cash 1 ETH
        "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",  # Tornado Cash 10 ETH
        "0xa160cd373d021a8776f174248d64230965330d10",  # Tornado Cash 0.1 ETH
        "0x3cffd56b47b7b41c56258d9c7731abdc360e0739",  # Lazarus Group Associated
        "0x098b716b8aaf21512996dc57eb0615e2383e2f96"   # Ronin Bridge Hack
    }
    
    # ERC-20 Methods Signatures
    ERC20_TRANSFER_METHOD: str = "0xa9059cbb"
    ERC20_TRANSFER_FROM_METHOD: str = "0x23b872dd"
    ERC20_APPROVE_METHOD: str = "0x095ea7b3"
    
    # Risk Engine Parameters
    RULE_RISK_SANCTIONED_WEIGHT: float = 100.0
    RULE_RISK_SUDDEN_DRAIN_WEIGHT: float = 40.0
    RULE_RISK_HIGH_VELOCITY_WEIGHT: float = 30.0
    RULE_RISK_GAS_SPIKE_WEIGHT: float = 20.0
    
    # Risk Alerts Thresholds
    ALERT_LOW: float = 0.0
    ALERT_MEDIUM: float = 40.0
    ALERT_HIGH: float = 70.0
    ALERT_CRITICAL: float = 90.0

settings = Settings()
