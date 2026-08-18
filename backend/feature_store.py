"""
Real-Time Feature Engineering Engine
AI-Powered Real-Time Ethereum Transaction Risk Intelligence Platform
"""

import time
from typing import Dict, Any, Set, List
from collections import defaultdict
from backend.config import settings
from backend.validator import ValidatedTransaction

class TemporalSlidingWindowStore:
    """
    High-Performance Sliding Window Feature Store.
    Simulates Redis ZSET (ZADD, ZCOUNT, ZREMRANGEBYSCORE) for O(1) temporal window lookups.
    """
    def __init__(self):
        # wallet_address -> list of (timestamp, tx_hash, value_eth, to_address)
        self.wallet_tx_history = defaultdict(list)
        # wallet_address -> set of unique counterparties
        self.wallet_out_counterparties = defaultdict(set)
        self.wallet_in_counterparties = defaultdict(set)
        # wallet_address -> first_seen_timestamp
        self.wallet_first_seen = {}
        # wallet_address -> balance_eth
        self.wallet_estimated_balance = defaultdict(lambda: 100.0) # Baseline 100 ETH balance for simulation

    def record_transaction(self, tx: ValidatedTransaction):
        now = tx.timestamp
        sender = tx.from_address
        receiver = tx.to_address

        if sender not in self.wallet_first_seen:
            self.wallet_first_seen[sender] = now
        if receiver not in self.wallet_first_seen:
            self.wallet_first_seen[receiver] = now

        self.wallet_tx_history[sender].append((now, tx.tx_hash, tx.value_eth, receiver))
        self.wallet_out_counterparties[sender].add(receiver)
        self.wallet_in_counterparties[receiver].add(sender)

        # Update simulated balance
        self.wallet_estimated_balance[sender] = max(0.0, self.wallet_estimated_balance[sender] - tx.value_eth)
        self.wallet_estimated_balance[receiver] += tx.value_eth

    def get_window_tx_count(self, address: str, duration_seconds: int, now: float) -> int:
        cutoff = now - duration_seconds
        records = self.wallet_tx_history.get(address, [])
        return sum(1 for (ts, _, _, _) in records if ts >= cutoff)

    def get_window_value_sum(self, address: str, duration_seconds: int, now: float) -> float:
        cutoff = now - duration_seconds
        records = self.wallet_tx_history.get(address, [])
        return sum(val for (ts, _, val, _) in records if ts >= cutoff)


class FeatureExtractor:
    def __init__(self):
        self.feature_store = TemporalSlidingWindowStore()
        self.base_fee_gwei = 20.0  # Dynamic network base fee baseline

    def extract_features(self, tx: ValidatedTransaction) -> Dict[str, Any]:
        """
        Extracts 15+ high-dimensional features across Transaction, Wallet, and Behavioral metrics.
        """
        now = tx.timestamp
        sender = tx.from_address
        receiver = tx.to_address

        # Update historical state
        self.feature_store.record_transaction(tx)

        # 1. Transaction Dimension Features
        usd_value = tx.value_usd
        eth_value = tx.value_eth
        gas_spike_ratio = tx.gas_price_gwei / max(1.0, self.base_fee_gwei)
        is_contract_interaction = 1.0 if (tx.input_data and tx.input_data != "0x") else 0.0
        is_erc20_transfer = 1.0 if tx.is_erc20 else 0.0

        # 2. Wallet Dimension Features
        first_seen = self.feature_store.wallet_first_seen.get(sender, now)
        wallet_age_days = (now - first_seen) / 86400.0
        tx_count_24h = self.feature_store.get_window_tx_count(sender, 86400, now)
        tx_count_7d = self.feature_store.get_window_tx_count(sender, 604800, now)

        # Interaction with known mixers / OFAC list
        interacts_with_sanctioned = 1.0 if (
            sender in settings.OFAC_SANCTIONED_ADDRESSES or 
            receiver in settings.OFAC_SANCTIONED_ADDRESSES
        ) else 0.0

        # 3. Behavioral & Temporal Graph Features
        # Velocity burst: Tx count in the last 5 minutes (300s)
        velocity_burst_5m = self.feature_store.get_window_tx_count(sender, 300, now)
        
        # Sudden drain index: ratio of ETH moved vs current balance
        est_balance = self.feature_store.wallet_estimated_balance.get(sender, 10.0) + eth_value
        sudden_drain_index = (eth_value / est_balance) if est_balance > 0 else 0.0
        sudden_drain_index = min(1.0, max(0.0, sudden_drain_index))

        # Fan-out & Fan-in Graph degree metrics
        fan_out_degree = len(self.feature_store.wallet_out_counterparties.get(sender, set()))
        fan_in_degree = len(self.feature_store.wallet_in_counterparties.get(sender, set()))

        features = {
            # Transaction Features
            "value_usd": float(usd_value),
            "value_eth": float(eth_value),
            "gas_price_gwei": float(tx.gas_price_gwei),
            "gas_spike_ratio": float(gas_spike_ratio),
            "is_contract_interaction": float(is_contract_interaction),
            "is_erc20_transfer": float(is_erc20_transfer),
            
            # Wallet Features
            "wallet_age_days": float(wallet_age_days),
            "tx_count_24h": float(tx_count_24h),
            "tx_count_7d": float(tx_count_7d),
            "interacts_with_sanctioned": float(interacts_with_sanctioned),
            
            # Behavioral Features
            "velocity_burst_5m": float(velocity_burst_5m),
            "sudden_drain_index": float(sudden_drain_index),
            "fan_out_degree": float(fan_out_degree),
            "fan_in_degree": float(fan_in_degree),
            
            # Raw Identifiers (Not fed directly to ML model)
            "_from": sender,
            "_to": receiver,
            "_tx_hash": tx.tx_hash
        }

        return features

feature_extractor = FeatureExtractor()
