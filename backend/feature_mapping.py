"""
Real-Time Feature Mapper for EVM Transaction Telemetry to Dataset Feature Schema
EVM Risk Intelligence Platform
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

# Complete feature schema matching transaction_dataset.csv (47 features)
DATASET_FEATURE_SCHEMA = [
    'Avg min between sent tnx',
    'Avg min between received tnx',
    'Time Diff between first and last (Mins)',
    'Sent tnx',
    'Received Tnx',
    'Number of Created Contracts',
    'Unique Received From Addresses',
    'Unique Sent To Addresses',
    'min value received',
    'max value received',
    'avg val received',
    'min val sent',
    'max val sent',
    'avg val sent',
    'min value sent to contract',
    'max val sent to contract',
    'avg value sent to contract',
    'total transactions (including tnx to create contract',
    'total Ether sent',
    'total ether received',
    'total ether sent contracts',
    'total ether balance',
    'Total ERC20 tnxs',
    'ERC20 total Ether received',
    'ERC20 total ether sent',
    'ERC20 total Ether sent contract',
    'ERC20 uniq sent addr',
    'ERC20 uniq rec addr',
    'ERC20 uniq sent addr.1',
    'ERC20 uniq rec contract addr',
    'ERC20 avg time between sent tnx',
    'ERC20 avg time between rec tnx',
    'ERC20 avg time between rec 2 tnx',
    'ERC20 avg time between contract tnx',
    'ERC20 min val rec',
    'ERC20 max val rec',
    'ERC20 avg val rec',
    'ERC20 min val sent',
    'ERC20 max val sent',
    'ERC20 avg val sent',
    'ERC20 min val sent contract',
    'ERC20 max val sent contract',
    'ERC20 avg val sent contract',
    'ERC20 uniq sent token name',
    'ERC20 uniq rec token name',
    'ERC20 most sent token type',
    'ERC20_most_rec_token_type'
]

class RealTimeFeatureMapper:
    """
    Maps real-time streaming EVM payload metrics & in-memory sliding window feature state
    to the 47-feature vector expected by the trained fraud detection model.
    """
    def __init__(self, feature_names: List[str] = None):
        self.feature_names = feature_names or DATASET_FEATURE_SCHEMA

    def map_live_payload_to_feature_dict(self, tx_payload: Dict[str, Any], wallet_profile: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Extracts metrics from live payload & wallet state to populate dataset feature vector.
        """
        profile = wallet_profile or {}
        val_eth = float(tx_payload.get("value_eth", 0.0))
        is_contract = 1.0 if tx_payload.get("is_contract", False) or tx_payload.get("input_data", "0x") != "0x" else 0.0
        is_erc20 = 1.0 if tx_payload.get("is_erc20", False) else 0.0

        # Extract account history features from in-memory profile or defaults
        sent_tnx = float(profile.get("sent_tnx", 1.0))
        rec_tnx = float(profile.get("rec_tnx", 1.0))
        tot_tnx = sent_tnx + rec_tnx
        
        tot_ether_sent = float(profile.get("total_eth_sent", val_eth))
        tot_ether_rec = float(profile.get("total_eth_rec", 0.0))
        eth_balance = tot_ether_rec - tot_ether_sent

        # Map to complete feature set
        feature_dict = {
            'Avg min between sent tnx': float(profile.get("avg_min_sent", 15.5)),
            'Avg min between received tnx': float(profile.get("avg_min_rec", 120.0)),
            'Time Diff between first and last (Mins)': float(profile.get("time_diff_mins", 1440.0)),
            'Sent tnx': sent_tnx,
            'Received Tnx': rec_tnx,
            'Number of Created Contracts': float(profile.get("created_contracts", 0.0)),
            'Unique Received From Addresses': float(profile.get("uniq_rec_addr", 2.0)),
            'Unique Sent To Addresses': float(profile.get("uniq_sent_addr", 1.0)),
            'min value received': float(profile.get("min_val_rec", 0.05)),
            'max value received': float(profile.get("max_val_rec", max(val_eth, 1.0))),
            'avg val received': float(profile.get("avg_val_rec", max(val_eth / 2, 0.5))),
            'min val sent': float(profile.get("min_val_sent", min(val_eth, 0.01))),
            'max val sent': float(profile.get("max_val_sent", max(val_eth, 0.1))),
            'avg val sent': float(profile.get("avg_val_sent", val_eth)),
            'min value sent to contract': val_eth if is_contract else 0.0,
            'max val sent to contract': val_eth if is_contract else 0.0,
            'avg value sent to contract': val_eth if is_contract else 0.0,
            'total transactions (including tnx to create contract': tot_tnx,
            'total Ether sent': tot_ether_sent,
            'total ether received': tot_ether_rec,
            'total ether sent contracts': tot_ether_sent if is_contract else 0.0,
            'total ether balance': eth_balance,
            'Total ERC20 tnxs': 1.0 if is_erc20 else float(profile.get("erc20_tnx_count", 0.0)),
            'ERC20 total Ether received': float(profile.get("erc20_total_ether_rec", 0.0)),
            'ERC20 total ether sent': float(profile.get("erc20_total_ether_sent", val_eth if is_erc20 else 0.0)),
            'ERC20 total Ether sent contract': 0.0,
            'ERC20 uniq sent addr': float(profile.get("erc20_uniq_sent_addr", 1.0 if is_erc20 else 0.0)),
            'ERC20 uniq rec addr': float(profile.get("erc20_uniq_rec_addr", 1.0 if is_erc20 else 0.0)),
            'ERC20 uniq sent addr.1': 0.0,
            'ERC20 uniq rec contract addr': 0.0,
            'ERC20 avg time between sent tnx': 0.0,
            'ERC20 avg time between rec tnx': 0.0,
            'ERC20 avg time between rec 2 tnx': 0.0,
            'ERC20 avg time between contract tnx': 0.0,
            'ERC20 min val rec': 0.0,
            'ERC20 max val rec': 0.0,
            'ERC20 avg val rec': 0.0,
            'ERC20 min val sent': val_eth if is_erc20 else 0.0,
            'ERC20 max val sent': val_eth if is_erc20 else 0.0,
            'ERC20 avg val sent': val_eth if is_erc20 else 0.0,
            'ERC20 min val sent contract': 0.0,
            'ERC20 max val sent contract': 0.0,
            'ERC20 avg val sent contract': 0.0,
            'ERC20 uniq sent token name': 1.0 if is_erc20 else 0.0,
            'ERC20 uniq rec token name': 0.0,
            'ERC20 most sent token type': 0.0,
            'ERC20_most_rec_token_type': 0.0
        }

        return feature_dict

    def to_feature_vector(self, feature_dict: Dict[str, float]) -> np.ndarray:
        """Converts feature dictionary to ordered 1D numpy array."""
        vec = [feature_dict.get(fname, 0.0) for fname in self.feature_names]
        return np.array(vec, dtype=np.float64)

feature_mapper = RealTimeFeatureMapper()
