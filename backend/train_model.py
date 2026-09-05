"""
Model Re-Training & Evaluation Engine with XGBoost, LightGBM & TreeSHAP
EVM Risk Intelligence Platform
"""

import os
import sys
import json
import pickle

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import numpy as np
import pandas as pd
import xgboost as xgb
import lightgbm as lgb
import shap

from typing import Dict, Any, List
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report
)
from backend.dataset_pipeline import EthereumDatasetPipeline

class ModelTrainingEngine:
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(base_dir, "models")
        
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.xgb_model = None
        self.lgb_model = None
        self.explainer = None
        self.metrics: Dict[str, Any] = {}

    def train_and_evaluate(self):
        print("=" * 70)
        print("ETH FRAUD DETECTION MODEL TRAINING & EVALUATION ENGINE")
        print("=" * 70)

        # 1. Load Preprocessed Data via Pipeline
        pipeline = EthereumDatasetPipeline()
        data = pipeline.prepare_pipeline()

        X_train = data["X_train_res"]
        y_train = data["y_train_res"]
        X_test = data["X_test_scaled"]
        y_test = data["y_test"]
        feature_names = data["feature_names"]
        scaler = data["scaler"]
        stats = data["stats"]

        print(f"Dataset Loaded: {stats['total_records']} rows, {stats['total_features']} features")
        print(f"SMOTE Training Set: {X_train.shape[0]} samples | Test Set: {X_test.shape[0]} samples")

        # 2. Train XGBoost Classifier
        print("\n[1/3] Training XGBoost Classifier...")
        xgb_clf = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss"
        )
        xgb_clf.fit(X_train, y_train)
        self.xgb_model = xgb_clf

        xgb_y_pred = xgb_clf.predict(X_test)
        xgb_y_prob = xgb_clf.predict_proba(X_test)[:, 1]

        xgb_cm = confusion_matrix(y_test, xgb_y_pred)
        xgb_metrics = {
            "model_name": "XGBoost Classifier",
            "precision": round(float(precision_score(y_test, xgb_y_pred)), 4),
            "recall": round(float(recall_score(y_test, xgb_y_pred)), 4),
            "f1_score": round(float(f1_score(y_test, xgb_y_pred)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, xgb_y_prob)), 4),
            "confusion_matrix": {
                "true_negative": int(xgb_cm[0][0]),
                "false_positive": int(xgb_cm[0][1]),
                "false_negative": int(xgb_cm[1][0]),
                "true_positive": int(xgb_cm[1][1])
            }
        }
        print(f" -> XGBoost F1-Score: {xgb_metrics['f1_score']} | ROC-AUC: {xgb_metrics['roc_auc']}")

        # 3. Train LightGBM Classifier
        print("\n[2/3] Training LightGBM Classifier...")
        lgb_clf = lgb.LGBMClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.05,
            random_state=42,
            verbose=-1
        )
        lgb_clf.fit(X_train, y_train)
        self.lgb_model = lgb_clf

        lgb_y_pred = lgb_clf.predict(X_test)
        lgb_y_prob = lgb_clf.predict_proba(X_test)[:, 1]

        lgb_cm = confusion_matrix(y_test, lgb_y_pred)
        lgb_metrics = {
            "model_name": "LightGBM Classifier",
            "precision": round(float(precision_score(y_test, lgb_y_pred)), 4),
            "recall": round(float(recall_score(y_test, lgb_y_pred)), 4),
            "f1_score": round(float(f1_score(y_test, lgb_y_pred)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, lgb_y_prob)), 4),
            "confusion_matrix": {
                "true_negative": int(lgb_cm[0][0]),
                "false_positive": int(lgb_cm[0][1]),
                "false_negative": int(lgb_cm[1][0]),
                "true_positive": int(lgb_cm[1][1])
            }
        }
        print(f" -> LightGBM F1-Score: {lgb_metrics['f1_score']} | ROC-AUC: {lgb_metrics['roc_auc']}")

        # 4. Generate Global TreeSHAP Feature Importance
        print("\n[3/3] Computing Global TreeSHAP Explanations...")
        explainer = shap.TreeExplainer(self.xgb_model)
        self.explainer = explainer

        # Compute SHAP on a representative subset (500 test samples)
        shap_sample_size = min(500, len(X_test))
        sample_indices = np.random.choice(len(X_test), shap_sample_size, replace=False)
        X_shap_sample = X_test[sample_indices]

        shap_vals = explainer.shap_values(X_shap_sample)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[1]

        mean_abs_shap = np.mean(np.abs(shap_vals), axis=0)

        shap_rankings = []
        for idx, f_name in enumerate(feature_names):
            shap_rankings.append({
                "feature": f_name,
                "importance": round(float(mean_abs_shap[idx]), 4),
                "description": self._get_feature_description(f_name)
            })

        shap_rankings.sort(key=lambda x: x["importance"], reverse=True)
        top_15_shap = shap_rankings[:15]

        print("Top 5 Global Risk Drivers Identified by TreeSHAP:")
        for r in top_15_shap[:5]:
            print(f"   - {r['feature']}: SHAP value {r['importance']} ({r['description']})")

        # 5. Compile Complete Metrics Payload
        self.metrics = {
            "dataset_stats": stats,
            "xgboost": xgb_metrics,
            "lightgbm": lgb_metrics,
            "top_shap_features": top_15_shap,
            "all_shap_features": shap_rankings,
            "feature_names": feature_names
        }

        # 6. Save Model Artifacts
        model_path = os.path.join(self.output_dir, "model.pkl")
        lgb_path = os.path.join(self.output_dir, "lgbm_model.pkl")
        scaler_path = os.path.join(self.output_dir, "scaler.pkl")
        explainer_path = os.path.join(self.output_dir, "explainer.pkl")
        metrics_path = os.path.join(self.output_dir, "model_metrics.json")

        with open(model_path, "wb") as f:
            pickle.dump(self.xgb_model, f)
        with open(lgb_path, "wb") as f:
            pickle.dump(self.lgb_model, f)
        with open(scaler_path, "wb") as f:
            pickle.dump(scaler, f)
        with open(explainer_path, "wb") as f:
            pickle.dump(self.explainer, f)

        with open(metrics_path, "w") as f:
            json.dump(self.metrics, f, indent=2)

        print("\n" + "=" * 70)
        print(f"ALL MODEL ARTIFACTS SAVED SUCCESSFULLY TO: {self.output_dir}")
        print("=" * 70)
        return self.metrics

    def _get_feature_description(self, feature_name: str) -> str:
        descriptions = {
            'total ether balance': 'Net wallet Ether balance (ETH in vs ETH out)',
            'Avg min between sent tnx': 'Average time interval (minutes) between outgoing transactions',
            'Avg min between received tnx': 'Average time interval (minutes) between incoming transactions',
            'ERC20 total Ether received': 'Total volume of ERC-20 tokens received',
            'ERC20 total ether sent': 'Total volume of ERC-20 tokens sent',
            'max val sent': 'Maximum Ether value sent in a single transaction',
            'total Ether sent': 'Cumulative Ether sent by address',
            'total ether received': 'Cumulative Ether received by address',
            'Unique Sent To Addresses': 'Count of distinct destination addresses sent to',
            'Unique Received From Addresses': 'Count of distinct source addresses received from',
            'Total ERC20 tnxs': 'Total number of ERC-20 token transactions',
            'Sent tnx': 'Total outgoing transaction count',
            'Received Tnx': 'Total incoming transaction count',
            'Time Diff between first and last (Mins)': 'Wallet active lifespan in minutes',
            'min value received': 'Minimum Ether value received',
            'max value received': 'Maximum Ether value received',
            'avg val received': 'Average Ether value received per transaction'
        }
        return descriptions.get(feature_name, f"Risk driver contribution metric for '{feature_name}'")

if __name__ == "__main__":
    trainer = ModelTrainingEngine()
    metrics = trainer.train_and_evaluate()
