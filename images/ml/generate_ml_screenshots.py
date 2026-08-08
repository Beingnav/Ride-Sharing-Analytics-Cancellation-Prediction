"""Generates 4 cleanly-named ML screenshots in images/ml/:
  model_comparison.png, confusion_matrix.png, roc_curve.png, shap_feature_importance.png

model_comparison / roc_curve / confusion_matrix are recomputed here (same
train/test split, same model configs, same random_state=42 as
python/06_cancellation_prediction.ipynb) so the ROC curve can show both
models on one chart — the saved cancellation_predictions.csv only has
probabilities for the single winning model, not both.
shap_feature_importance.png is plotted directly from the already-computed
data/processed/shap_feature_importance.csv (no need to rerun SHAP).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, roc_curve,
)

PROCESSED = Path("../../data/processed")
OUT = Path(".")
RANDOM_SEED = 42
DECISION_THRESHOLD = 0.30

NAVY = "#1F2A44"
ACCENT = "#4C72B0"
GREEN = "#55A868"
ORANGE = "#DD8452"
RED = "#C44E52"
PURPLE = "#8172B2"
BG = "#F4F6FA"

plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.edgecolor": "#D8DEE9",
    "axes.grid": True,
    "grid.color": "#E6E9F0",
    "grid.linewidth": 0.6,
})


def savefig(fig, name):
    fig.patch.set_facecolor(BG)
    fig.savefig(OUT / name, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"saved images/ml/{name}")


# ---------------------------------------------------------------------------
# Reproduce notebook 06's exact split + model training
# ---------------------------------------------------------------------------
df = pd.read_csv(PROCESSED / "trips_ml_ready.csv", parse_dates=["request_datetime"])
df = df.sort_values("request_datetime").reset_index(drop=True)

ID_COLS = ["trip_id", "rider_id", "driver_id", "request_datetime"]
TARGET = "is_cancelled"
CATEGORICAL = ["vehicle_type", "pickup_city", "drop_city", "payment_method",
               "rider_gender", "preferred_payment"]

combined = pd.get_dummies(df.drop(columns=ID_COLS + [TARGET]), columns=CATEGORICAL, drop_first=True)
feature_names = combined.columns.tolist()

split_idx = int(len(df) * 0.8)
train_df = df.iloc[:split_idx].copy()
test_df = df.iloc[split_idx:].copy()

X_train = combined.iloc[:split_idx].reset_index(drop=True)
X_test = combined.iloc[split_idx:].reset_index(drop=True)
y_train = train_df[TARGET].reset_index(drop=True)
y_test = test_df[TARGET].reset_index(drop=True)

scaler = StandardScaler()
X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=feature_names)
X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=feature_names)

models = {}
log_reg = LogisticRegression(max_iter=1000, random_state=RANDOM_SEED)
log_reg.fit(X_train_scaled, y_train)
models["Logistic Regression"] = (log_reg, X_test_scaled)

rf = RandomForestClassifier(n_estimators=300, max_depth=10, min_samples_leaf=20,
                             random_state=RANDOM_SEED, n_jobs=-1)
rf.fit(X_train, y_train)
models["Random Forest"] = (rf, X_test)

try:
    from xgboost import XGBClassifier
    xgb_model = XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.05,
                               subsample=0.8, colsample_bytree=0.8, eval_metric="logloss",
                               random_state=RANDOM_SEED, n_jobs=-1)
    xgb_model.fit(X_train, y_train)
    models["XGBoost"] = (xgb_model, X_test)
except Exception as exc:
    print(f"XGBoost unavailable ({exc}); comparing Logistic Regression + Random Forest only.")

comparison_rows = []
predictions_by_model = {}
for name, (model, X_te) in models.items():
    y_proba = model.predict_proba(X_te)[:, 1]
    y_pred = (y_proba >= DECISION_THRESHOLD).astype(int)
    comparison_rows.append({
        "model": name,
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_proba),
    })
    predictions_by_model[name] = y_proba

model_comparison = pd.DataFrame(comparison_rows).sort_values("f1_score", ascending=False)
best_model_name = model_comparison.iloc[0]["model"]
print(model_comparison.round(4))
print(f"Best model: {best_model_name}")

# ===========================================================================
# 1. model_comparison.png
# ===========================================================================
metrics = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(metrics))
width = 0.8 / len(models)
colors = [ACCENT, GREEN, ORANGE, PURPLE]
for i, (_, row) in enumerate(model_comparison.iterrows()):
    vals = [row[m] for m in metrics]
    ax.bar(x + i * width, vals, width, label=row["model"], color=colors[i % len(colors)])
ax.set_xticks(x + width * (len(models) - 1) / 2)
ax.set_xticklabels(["Accuracy", "Precision", "Recall", "F1", "ROC-AUC"])
ax.set_ylim(0, 1)
ax.set_title("Model Comparison — Test Set (0.30 decision threshold)", fontsize=13, weight="bold", color=NAVY, loc="left")
ax.legend(frameon=False)
savefig(fig, "model_comparison.png")

# ===========================================================================
# 2. roc_curve.png
# ===========================================================================
fig, ax = plt.subplots(figsize=(8, 6.5))
colors_map = {"Logistic Regression": ACCENT, "Random Forest": GREEN, "XGBoost": ORANGE}
for name, y_proba in predictions_by_model.items():
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    auc = roc_auc_score(y_test, y_proba)
    ax.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})", color=colors_map.get(name, NAVY), linewidth=2.2)
ax.plot([0, 1], [0, 1], "--", color="#B0B7C3", alpha=0.8, label="Random")
ax.set_xlabel("False Positive Rate")
ax.set_ylabel("True Positive Rate")
ax.set_title("ROC Curve — Cancellation Prediction Models", fontsize=13, weight="bold", color=NAVY, loc="left")
ax.legend(frameon=False, loc="lower right")
savefig(fig, "roc_curve.png")

# ===========================================================================
# 3. confusion_matrix.png
# ===========================================================================
best_proba = predictions_by_model[best_model_name]
best_pred = (best_proba >= DECISION_THRESHOLD).astype(int)
cm = confusion_matrix(y_test, best_pred)

fig, ax = plt.subplots(figsize=(6.5, 5.5))
im = ax.imshow(cm, cmap="Blues")
ax.set_title(f"Confusion Matrix — {best_model_name} (threshold={DECISION_THRESHOLD})", fontsize=12.5, weight="bold", color=NAVY, loc="left")
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_xticks([0, 1]); ax.set_xticklabels(["Completed", "Cancelled"])
ax.set_yticks([0, 1]); ax.set_yticklabels(["Completed", "Cancelled"])
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", fontsize=13,
                 color="white" if cm[i, j] > cm.max() / 2 else NAVY)
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
savefig(fig, "confusion_matrix.png")

# ===========================================================================
# 4. shap_feature_importance.png (plotted from existing computed CSV)
# ===========================================================================
shap_importance = pd.read_csv(PROCESSED / "shap_feature_importance.csv")
top = shap_importance.head(12).sort_values("mean_abs_shap")

fig, ax = plt.subplots(figsize=(9, 6.5))
ax.barh(top.feature, top.mean_abs_shap, color=PURPLE)
ax.set_title(f"SHAP Global Feature Importance — {best_model_name}", fontsize=13, weight="bold", color=NAVY, loc="left")
ax.set_xlabel("Mean |SHAP value|")
savefig(fig, "shap_feature_importance.png")

print("\nAll 4 ML screenshots saved to images/ml/")
