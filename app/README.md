# Live Demo (Streamlit)

An interactive app with two pages:

1. **Analytics Dashboard** — Plotly version of the four Power BI pages from
   [`powerbi/README.md`](../powerbi/README.md), reading straight from
   `data/processed/trips_analysis_ready.csv` and `cancellation_predictions.csv`.
2. **Cancellation Risk Predictor** — fill in a hypothetical trip and get a
   live prediction from the actual trained model in `models/`, plus a
   real-time SHAP explanation of that specific prediction (same technique
   as `python/07_model_explainability.ipynb`, run on-demand for one input
   instead of the batch test set).

Nothing in this app is computed independently — it only loads artifacts
that `python/01` through `python/06` already produced. If you haven't run
those notebooks yet (or deleted `data/processed/` or `models/`), the app
will tell you which file is missing on startup instead of crashing.

## Run it

From the repo root, with the project's virtualenv active:

```bash
source .venv/bin/activate        # or however you activate your env
pip install -r requirements.txt  # includes streamlit + plotly
streamlit run app/streamlit_app.py
```

Opens at `http://localhost:8501`.

## Notes

- The predictor reads `models/model_metadata.json` to find out which model
  actually won the comparison (Random Forest or XGBoost, whichever your
  environment trained) and loads that one — no hardcoded model name.
- If you re-run `06_cancellation_prediction.ipynb` after `brew install
  libomp` gets XGBoost working, just restart this app — it'll pick up the
  new model and artifacts automatically.
