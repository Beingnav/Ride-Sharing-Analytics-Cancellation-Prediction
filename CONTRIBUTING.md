# Contributing

This is a personal portfolio project, but suggestions and fixes are welcome.

1. Fork the repository and create a feature branch off `main`.
2. Keep changes scoped — one notebook/script or one SQL file per PR where possible.
3. If you change the data schema (`sql/02_create_tables.sql`), regenerate the
   affected notebooks (`python/01_data_generation.ipynb` onward) so the CSVs
   in `data/` stay consistent with the schema.
4. Run the notebooks top-to-bottom before opening a PR to confirm the pipeline
   still executes end-to-end without errors.
5. Open a pull request describing what changed and why.

## Reporting issues

Open a GitHub issue with:
- What you ran (which notebook/script or SQL file)
- What you expected vs. what happened
- Your Python version and OS (XGBoost/SHAP install issues are often
  platform-specific — see `requirements.txt` for the macOS OpenMP note)
