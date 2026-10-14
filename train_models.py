"""
Convective Weather Model Training & Evaluation Pipeline
======================================================
Project: AI-Based Thunderstorm & Convective Nowcasting System
Location Domain: Karnataka (Bangalore HAL Observatory / Coastal & Inland KA)

Description:
    Trains, validates, and benchmarks multiple machine learning architectures
    for predicting convective weather events:
    - Zero data leakage: excludes same-day precipitation/condition metrics.
    - Dynamic chronological split across full dataset (80% Train, 20% Test).
    - Refits winning best model architecture on 100% of historical records.
    - Benchmarks: Logistic Regression, Random Forest, and HistGradientBoosting (GBDT).
    - Saves serialized model artifact and feature schema for live nowcasting.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

from config import PROCESSED_DIR, MODELS_DIR


def load_and_split_data(features_csv: str):
    """
    Load feature dataset and perform chronological train/test split.
    """
    print(f"[1/5] Loading processed dataset from: '{features_csv}'...")
    df = pd.read_csv(features_csv)
    df["datetime"] = pd.to_datetime(df["datetime"])

    # Exclude contemporary rain measurements and raw descriptive labels
    leakage_and_metadata = [
        "target_convective_rain",
        "target_severe_convective",
        "precip",
        "precip_mm",
        "precipprob",
        "precipcover",
        "preciptype",
        "conditions",
        "description",
        "icon",
        "datetime",
        "name",
        "stations",
        "sunrise",
        "sunset",
        "segment_id",
        "year",
        "temp", "tempmax", "tempmin", "feelslike", "feelslikemax", "feelslikemin",
        "dew", "windspeed", "windgust", "sealevelpressure"
    ]

    feature_cols = [c for c in df.columns if c not in leakage_and_metadata]
    target_col = "target_convective_rain"

    min_year = df["year"].min()
    max_year = df["year"].max()
    split_ratio = 0.70
    split_year = int(min_year + split_ratio * (max_year - min_year))

    train_mask = df["year"] <= split_year
    test_mask = df["year"] > split_year

    X_train = df.loc[train_mask, feature_cols].fillna(0)
    y_train = df.loc[train_mask, target_col]

    X_test = df.loc[test_mask, feature_cols].fillna(0)
    y_test = df.loc[test_mask, target_col]

    X_full = df[feature_cols].fillna(0)
    y_full = df[target_col]

    print(f"      Total records: {len(df):,} across years {min_year} to {max_year}")
    print(f"      Selected {len(feature_cols)} clean predictive atmospheric features.")
    print(f"      Train set (70% | {min_year}-{split_year}): {X_train.shape[0]:,} samples (Positive class: {y_train.mean()*100:.1f}%)")
    print(f"      Test set  (30% | {split_year+1}-{max_year}):  {X_test.shape[0]:,} samples (Positive class: {y_test.mean()*100:.1f}%)")

    return X_train, y_train, X_test, y_test, X_full, y_full, feature_cols, min_year, max_year, split_year


def build_model_candidates():
    """Define candidate classification models."""
    models = {
        "Logistic Regression (Baseline)": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42))
        ]),
        "Random Forest Classifier": RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        ),
        "HistGradientBoosting (GBDT)": HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.08,
            max_leaf_nodes=31,
            class_weight="balanced",
            random_state=42
        )
    }
    return models


def evaluate_model(name: str, model, X_train, y_train, X_test, y_test):
    """Train model, predict on holdout test set, and compute key evaluation metrics."""
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)

    results = {
        "model_name": name,
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4),
        "confusion_matrix": cm.tolist()
    }
    return results, y_pred, y_prob


def run_training():
    """Execute complete training and evaluation pipeline."""
    features_csv = str(PROCESSED_DIR / "karnataka_convective_features.csv")
    if not os.path.exists(features_csv):
        print(f"[ERROR] Processed features file not found at: '{features_csv}'")
        print("Please run 'python preprocess_features.py' first.")
        return

    # 1. Load Data
    X_train, y_train, X_test, y_test, X_full, y_full, feature_cols, min_year, max_year, split_year = load_and_split_data(features_csv)

    # 2. Build Models
    models = build_model_candidates()
    print(f"\n[2/5] Benchmarking {len(models)} model architectures...")

    results_list = []
    trained_models = {}

    for name, model in models.items():
        print(f"      -> Training & Evaluating: {name}...")
        res, y_pred, y_prob = evaluate_model(name, model, X_train, y_train, X_test, y_test)
        results_list.append(res)
        trained_models[name] = model

    # 3. Present Results Table
    print(f"\n[3/5] Benchmark Performance on Holdout Test Set ({split_year+1}-{max_year}):")
    res_df = pd.DataFrame(results_list)[["model_name", "accuracy", "precision", "recall", "f1_score", "roc_auc"]]
    print("=" * 75)
    print(res_df.to_string(index=False))
    print("=" * 75)

    # 4. Select Best Model Architecture based on F1-Score & ROC-AUC
    best_res = max(results_list, key=lambda x: (x["f1_score"] + x["roc_auc"]))
    best_name = best_res["model_name"]
    print(f"\n[4/5] Selected Best Model Architecture: '{best_name}'")
    print(f"      Holdout F1-Score: {best_res['f1_score']:.4f} | ROC-AUC: {best_res['roc_auc']:.4f} | Accuracy: {best_res['accuracy']*100:.2f}%")

    # 5. Retrain Final Model on 100% of Historical Dataset (2000-2027)
    print(f"\n[5/5] Refitting final '{best_name}' artifact on ALL {len(X_full):,} records ({min_year}-{max_year})...")
    final_model = build_model_candidates()[best_name]
    final_model.fit(X_full, y_full)

    # 6. Save Model Artifacts
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "best_convective_model.joblib"
    joblib.dump(final_model, model_path)

    with open(MODELS_DIR / "feature_columns.json", "w") as f:
        json.dump(feature_cols, f, indent=2)

    with open(MODELS_DIR / "metrics_summary.json", "w") as f:
        json.dump(results_list, f, indent=2)

    print(f"      Saved retrained model artifact to: '{model_path}'")
    print(f"      Saved feature schema to: '{MODELS_DIR / 'feature_columns.json'}'")
    print(f"      Saved evaluation metrics to: '{MODELS_DIR / 'metrics_summary.json'}'")
    print("\nModel Retraining Complete! The system is fully updated for live nowcasting predictions.\n")


if __name__ == "__main__":
    run_training()
