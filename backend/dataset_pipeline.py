"""
Ethereum Fraud Detection Dataset Ingestion & Preprocessing Pipeline
EVM Risk Intelligence Platform
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from imblearn.over_sampling import SMOTE

class EthereumDatasetPipeline:
    def __init__(self, csv_path: str = None):
        if csv_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(base_dir, "data", "transaction_dataset.csv")
            if not os.path.exists(csv_path):
                # Fallback to downloads if local relative path missing
                csv_path = os.path.expanduser("~/Downloads/transaction_dataset.csv")

        self.csv_path = csv_path
        self.scaler = StandardScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_names: List[str] = []
        self.drop_columns = ["Unnamed: 0", "Index", "Address"]
        self.categorical_cols = ["ERC20 most sent token type", "ERC20_most_rec_token_type"]

    def load_data(self) -> pd.DataFrame:
        """Loads dataset and strips column whitespace."""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Dataset file not found at: {self.csv_path}")
        
        df = pd.read_csv(self.csv_path)
        # Clean column names (strip whitespace)
        df.columns = df.columns.str.strip()
        return df

    def preprocess(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Cleans identifier columns, handles missing values, and encodes categorical token types.
        """
        df_clean = df.copy()

        # Drop identifiers
        cols_to_drop = [c for c in self.drop_columns if c in df_clean.columns]
        df_clean = df_clean.drop(columns=cols_to_drop)

        # Target label separation
        if "FLAG" not in df_clean.columns:
            raise KeyError("Target column 'FLAG' not found in dataset")

        y = df_clean["FLAG"].astype(int)
        X = df_clean.drop(columns=["FLAG"])

        # Handle Categorical Columns
        for col in self.categorical_cols:
            if col in X.columns:
                X[col] = X[col].fillna("None").astype(str)
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col])
                self.label_encoders[col] = le

        # Handle Numeric missing values (impute with 0.0 or median)
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        X[numeric_cols] = X[numeric_cols].fillna(0.0)

        self.feature_names = list(X.columns)
        return X, y

    def prepare_pipeline(self) -> Dict[str, Any]:
        """
        Executes full preprocessing, train-test split (80/20), StandardScaler, and SMOTE oversampling.
        """
        df_raw = self.load_data()
        
        # Raw statistics for UI Showcase
        total_records = len(df_raw)
        original_class_counts = df_raw["FLAG"].value_counts().to_dict()
        fraud_ratio = round(original_class_counts.get(1, 0) / total_records * 100, 2)
        legit_count = original_class_counts.get(0, 0)
        fraud_count = original_class_counts.get(1, 0)

        # Unique token count
        all_tokens = set()
        if "ERC20 most sent token type" in df_raw.columns:
            all_tokens.update(df_raw["ERC20 most sent token type"].dropna().unique())
        if "ERC20_most_rec_token_type" in df_raw.columns:
            all_tokens.update(df_raw["ERC20_most_rec_token_type"].dropna().unique())

        X, y = self.preprocess(df_raw)

        # Stratified 80/20 train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Fit StandardScaler on train, transform train and test
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Apply SMOTE to balance train set target distribution
        smote = SMOTE(random_state=42)
        X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)

        smote_class_counts = pd.Series(y_train_res).value_counts().to_dict()

        return {
            "X_train_res": X_train_res,
            "X_test_scaled": X_test_scaled,
            "y_train_res": y_train_res,
            "y_test": y_test,
            "X_test_raw": X_test,
            "feature_names": self.feature_names,
            "scaler": self.scaler,
            "label_encoders": self.label_encoders,
            "stats": {
                "total_records": total_records,
                "total_features": len(self.feature_names),
                "legit_count": legit_count,
                "fraud_count": fraud_count,
                "fraud_ratio_pct": fraud_ratio,
                "total_erc20_tokens": len(all_tokens),
                "original_class_counts": original_class_counts,
                "smote_class_counts": smote_class_counts
            },
            "df_raw": df_raw
        }

if __name__ == "__main__":
    pipeline = EthereumDatasetPipeline()
    res = pipeline.prepare_pipeline()
    print("Dataset Pipeline Initialized Successfully:")
    print(f" -> Total Records: {res['stats']['total_records']}")
    print(f" -> Features Count: {res['stats']['total_features']}")
    print(f" -> Class Distribution: Legit={res['stats']['legit_count']}, Fraud={res['stats']['fraud_count']} ({res['stats']['fraud_ratio_pct']}%)")
    print(f" -> SMOTE Balanced Train Set Shape: {res['X_train_res'].shape}")
