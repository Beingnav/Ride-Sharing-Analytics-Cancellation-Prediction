# images/ml/

Two sets of files here, both real output — no mock data in either:

- **`model_comparison.png`, `roc_curve.png`, `confusion_matrix.png`,
  `shap_feature_importance.png`** — clean, single-purpose charts.
  `model_comparison`/`roc_curve`/`confusion_matrix` are recomputed by
  [`generate_ml_screenshots.py`](generate_ml_screenshots.py) (same
  train/test split, same model configs, same `random_state=42` as
  `python/06_cancellation_prediction.ipynb`) so the ROC curve can show
  every trained model on one chart, not just the winner.
  `shap_feature_importance.png` is plotted straight from the already-computed
  `data/processed/shap_feature_importance.csv`.

- **`01_roc_curves.png` … `05_shap_waterfall_example.png`** — the original
  output of `python/06_cancellation_prediction.ipynb` and
  `07_model_explainability.ipynb` themselves, kept as-is. `05_shap_waterfall_example.png`
  (a single-prediction explanation) doesn't have an equivalent in the set
  above.

Re-run `python3 generate_ml_screenshots.py` from this directory (with the
project venv active) after retraining to refresh the first set.
