"""
Hybrid Risk Analysis Engine & TreeSHAP Explainability Module
AI-Powered Real-Time Ethereum Transaction Risk Intelligence Platform
"""

import time
import numpy as np
import pandas as pd
import xgboost as xgb
import shap
from typing import Dict, Any, List, Tuple
from backend.config import settings

FEATURE_COLUMNS = [
    "value_usd",
    "value_eth",
    "gas_price_gwei",
    "gas_spike_ratio",
    "is_contract_interaction",
    "is_erc20_transfer",
    "wallet_age_days",
    "tx_count_24h",
    "tx_count_7d",
    "interacts_with_sanctioned",
    "velocity_burst_5m",
    "sudden_drain_index",
    "fan_out_degree",
    "fan_in_degree"
]

class HybridRiskEngine:
    def __init__(self):
        self.model: xgb.XGBClassifier = None
        self.explainer: shap.TreeExplainer = None
        self._initialize_and_train_model()

    def _initialize_and_train_model(self):
        """
        Pre-trains an XGBoost risk model on synthetic EVM transaction telemetry.
        Generates standard baseline distributions and malicious attack archetypes.
        """
        np.random.seed(42)
        n_samples = 1500

        # Normal EVM behavior
        normal_data = {
            "value_usd": np.random.exponential(scale=200, size=n_samples),
            "value_eth": np.random.exponential(scale=0.1, size=n_samples),
            "gas_price_gwei": np.random.normal(loc=20.0, scale=3.0, size=n_samples),
            "gas_spike_ratio": np.random.normal(loc=1.0, scale=0.2, size=n_samples),
            "is_contract_interaction": np.random.choice([0.0, 1.0], size=n_samples, p=[0.7, 0.3]),
            "is_erc20_transfer": np.random.choice([0.0, 1.0], size=n_samples, p=[0.6, 0.4]),
            "wallet_age_days": np.random.uniform(10, 1000, size=n_samples),
            "tx_count_24h": np.random.poisson(lam=3, size=n_samples),
            "tx_count_7d": np.random.poisson(lam=15, size=n_samples),
            "interacts_with_sanctioned": np.zeros(n_samples),
            "velocity_burst_5m": np.random.poisson(lam=0.5, size=n_samples),
            "sudden_drain_index": np.random.beta(a=0.5, b=5.0, size=n_samples),
            "fan_out_degree": np.random.poisson(lam=2, size=n_samples),
            "fan_in_degree": np.random.poisson(lam=2, size=n_samples),
        }

        # Malicious attack patterns (Tornado cash, flash loans, bot bursts, drainers)
        n_attack = 300
        attack_data = {
            "value_usd": np.random.uniform(10000, 500000, size=n_attack),
            "value_eth": np.random.uniform(5.0, 150.0, size=n_attack),
            "gas_price_gwei": np.random.uniform(80.0, 300.0, size=n_attack),
            "gas_spike_ratio": np.random.uniform(4.0, 15.0, size=n_attack),
            "is_contract_interaction": np.ones(n_attack),
            "is_erc20_transfer": np.random.choice([0.0, 1.0], size=n_attack, p=[0.3, 0.7]),
            "wallet_age_days": np.random.exponential(scale=2.0, size=n_attack),  # Fresh wallets
            "tx_count_24h": np.random.poisson(lam=25, size=n_attack),
            "tx_count_7d": np.random.poisson(lam=40, size=n_attack),
            "interacts_with_sanctioned": np.random.choice([0.0, 1.0], size=n_attack, p=[0.5, 0.5]),
            "velocity_burst_5m": np.random.poisson(lam=8, size=n_attack),  # Burst velocity
            "sudden_drain_index": np.random.uniform(0.85, 1.0, size=n_attack),  # Sudden drain > 85%
            "fan_out_degree": np.random.poisson(lam=12, size=n_attack),
            "fan_in_degree": np.random.poisson(lam=1, size=n_attack),
        }

        df_normal = pd.DataFrame(normal_data)
        df_normal["label"] = 0

        df_attack = pd.DataFrame(attack_data)
        df_attack["label"] = 1

        df_all = pd.concat([df_normal, df_attack], ignore_index=True)
        X = df_all[FEATURE_COLUMNS]
        y = df_all["label"]

        self.model = xgb.XGBClassifier(
            n_estimators=50,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            eval_metric="logloss"
        )
        self.model.fit(X, y)

        # Initialize TreeSHAP explainer for fast <15ms C-binding calculations
        self.explainer = shap.TreeExplainer(self.model)

        # Warmup TreeSHAP matrix to avoid cold-start JIT overhead
        _dummy_df = pd.DataFrame([[0.0] * len(FEATURE_COLUMNS)], columns=FEATURE_COLUMNS)
        _ = self.explainer.shap_values(_dummy_df)

    def compute_heuristic_rules(self, features: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Deterministic heuristics engine for immediate red flag identification.
        """
        rule_score = 0.0
        reasons = []

        # Rule 1: Direct interaction with Sanctioned entity / Tornado Cash
        if features.get("interacts_with_sanctioned", 0.0) > 0.5:
            rule_score += settings.RULE_RISK_SANCTIONED_WEIGHT
            reasons.append("CRITICAL: Direct interaction with OFAC-sanctioned entity / Tornado Cash mixer")

        # Rule 2: Sudden balance drain (> 90% of total balance moved)
        drain_idx = features.get("sudden_drain_index", 0.0)
        if drain_idx >= 0.90:
            rule_score += settings.RULE_RISK_SUDDEN_DRAIN_WEIGHT
            reasons.append(f"HIGH: Sudden balance drain detected ({drain_idx * 100:.1f}% of wallet assets moved)")

        # Rule 3: Burst Transaction Velocity
        velocity = features.get("velocity_burst_5m", 0.0)
        if velocity >= 5:
            rule_score += settings.RULE_RISK_HIGH_VELOCITY_WEIGHT
            reasons.append(f"HIGH: High transaction velocity burst ({int(velocity)} txs in 5 min window)")

        # Rule 4: Gas Price Spike
        gas_spike = features.get("gas_spike_ratio", 1.0)
        if gas_spike >= 4.0:
            rule_score += settings.RULE_RISK_GAS_SPIKE_WEIGHT
            reasons.append(f"MEDIUM: Abnormal gas price spike ({gas_spike:.1f}x network base fee)")

        # Rule 5: High INR Transaction Threshold (> ₹1 Crore INR / ₹10,000,000)
        val_inr = features.get("value_inr", 0.0)
        if val_inr >= 10000000.0:
            rule_score += 35.0
            reasons.append(f"HIGH: High INR volume transaction exceeding ₹1 Crore threshold (₹{val_inr / 10000000.0:.2f} Cr)")

        return min(100.0, rule_score), reasons

    def evaluate(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates hybrid rules + XGBoost ML model and computes sub-15ms TreeSHAP explanations.
        """
        start_time = time.time()

        # Extract ML feature vector
        x_vec = np.array([[features.get(col, 0.0) for col in FEATURE_COLUMNS]])
        df_x = pd.DataFrame(x_vec, columns=FEATURE_COLUMNS)

        # 1. ML Probability
        ml_prob = float(self.model.predict_proba(df_x)[0][1])

        # 2. Rule Engine Assessment
        rule_score, rule_reasons = self.compute_heuristic_rules(features)

        # 3. Composite Aggregator Formula
        composite_score = min(100.0, (ml_prob * 70.0) + rule_score)

        # 4. TreeSHAP Explanation Extraction
        shap_values = self.explainer.shap_values(df_x)[0]
        
        # Pair feature names with SHAP contributions
        feature_shap_pairs = []
        for i, col in enumerate(FEATURE_COLUMNS):
            val = float(shap_values[i])
            feature_shap_pairs.append({
                "feature": col,
                "shap_value": val,
                "feature_value": float(x_vec[0][i])
            })

        # Sort by impact (highest positive contribution to risk score)
        feature_shap_pairs.sort(key=lambda x: x["shap_value"], reverse=True)
        top_positive_drivers = [p for p in feature_shap_pairs if p["shap_value"] > 0][:3]

        # Translate top drivers to human-readable explanations
        human_explanations = []
        for driver in top_positive_drivers:
            feat = driver["feature"]
            val = driver["feature_value"]
            if feat == "velocity_burst_5m":
                human_explanations.append(f"High velocity burst: {int(val)} transactions in 5 minutes")
            elif feat == "sudden_drain_index":
                human_explanations.append(f"Sudden wallet drain index: {val * 100:.1f}% moved in single transaction")
            elif feat == "interacts_with_sanctioned" and val > 0:
                human_explanations.append("Direct transfer to/from OFAC sanctioned entity")
            elif feat == "gas_spike_ratio":
                human_explanations.append(f"Gas price spike: {val:.1f}x higher than network base fee")
            elif feat == "value_usd":
                human_explanations.append(f"High USD transaction volume: ${val:,.2f}")
            elif feat == "wallet_age_days" and val < 3.0:
                human_explanations.append(f"Fresh unverified wallet: Created {val:.1f} days ago")
            else:
                human_explanations.append(f"Elevated risk metric for '{feat}': {val:.2f}")

        # Combine rule reasons with SHAP drivers
        all_reasons = list(dict.fromkeys(rule_reasons + human_explanations))

        # Determine Alert Level
        if composite_score >= settings.ALERT_CRITICAL:
            alert_level = "CRITICAL"
        elif composite_score >= settings.ALERT_HIGH:
            alert_level = "HIGH"
        elif composite_score >= settings.ALERT_MEDIUM:
            alert_level = "MEDIUM"
        else:
            alert_level = "LOW"

        elapsed_ms = (time.time() - start_time) * 1000.0

        return {
            "ml_probability": round(ml_prob, 4),
            "rule_risk_score": round(rule_score, 2),
            "composite_risk_score": round(composite_score, 2),
            "alert_level": alert_level,
            "reasons": all_reasons[:4],
            "top_shap_drivers": feature_shap_pairs[:6],
            "execution_time_ms": round(elapsed_ms, 2)
        }

risk_engine = HybridRiskEngine()
