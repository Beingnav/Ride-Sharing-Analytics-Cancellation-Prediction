# Power BI Dashboard

No `.pbix` ships in this repo — Power BI Desktop is a **Windows-only** GUI
application (no Mac build exists), so nothing here could be run through it
to produce or verify a compiled `.pbix`. Two things are included instead.

## Option A — Open `RideSharingAnalytics.pbip` (Windows, Power BI Desktop)

A [Power BI Project](https://learn.microsoft.com/power-bi/developer/projects/projects-overview)
— the modern git-friendly format (TMDL semantic model + PBIR report
definition) that Power BI Desktop can open directly. It was hand-written
without access to Power BI Desktop to test it, so here's the honest
confidence breakdown:

| Component | Confidence | What it is |
|---|---|---|
| `RideSharingAnalytics.pbip`, `.platform`, `definition.pbism`, `definition.pbir` | High — small, stable, well-documented formats | Project wiring / pointer files |
| `RideSharingAnalytics.SemanticModel/definition/*.tmdl` | High | 5 tables (Trips, Predictions, ModelComparison, ShapImportance, StatTests), all 17 DAX measures from the guide below, and the Trips↔Predictions relationship — this is the part actually worth trusting |
| `RideSharingAnalytics.Report/definition/...` | **Experimental** | One page ("Executive Overview") with 4 card visuals. The report-layout JSON schema is the most fragile, fastest-changing part of the whole `.pbip` format, and this is the one piece I could not verify opens correctly |

**Before opening it, set the data path** — Power BI Desktop will prompt for
a parameter called `RepoRootPath` (used so the CSV file paths aren't
hardcoded to my machine): set it to the absolute local path of this
repo, e.g. `C:\Users\YourName\Ride-Sharing-Analytics-Cancellation-Prediction`.
(`Transform data → Edit Parameters` if it doesn't prompt automatically.)

**If it fails to open, or the report page errors out:** delete the
`RideSharingAnalytics.Report` folder, keep `RideSharingAnalytics.SemanticModel`,
and in Power BI Desktop do `File → New Report` against that local semantic
model instead — the tables/measures/relationship should load fine even if
the hand-authored report page doesn't, and you're back to building visuals
by hand per the guide below (which was the plan either way).

## Option B — Build it manually (works on any setup)

The rest of this document — DAX measures + page-by-page layout — using
Power BI Desktop's ordinary "Get Data" flow. This is the reliable path
regardless of whether Option A works for you.

## 1. Get data

Simplest path — import CSVs directly, no MySQL required:

| Power BI table name | Source file |
|---|---|
| `Trips` | `data/processed/trips_analysis_ready.csv` |
| `Predictions` | `data/processed/cancellation_predictions.csv` |
| `ModelComparison` | `data/processed/model_comparison.csv` |
| `ShapImportance` | `data/processed/shap_feature_importance.csv` |
| `StatTests` | `data/processed/statistical_test_results.csv` |

Or connect live to MySQL (`Get Data → MySQL database`, server = your local
instance, database = `ride_sharing_analytics`) and import the views from
`sql/02_create_tables.sql` (`vw_trip_details`, `vw_driver_performance`,
`vw_rider_activity`) plus the base tables — either works, the DAX below is
written against `Trips` (i.e. `trips_analysis_ready.csv` / `vw_trip_details`,
which have the same columns) so it's identical either way.

## 2. Data model

Set relationships:

- `Trips[trip_id]` → `Predictions[trip_id]` (one-to-one)
- Add a `Date` table (`Home → New Table`) if you want proper time
  intelligence:
  ```dax
  DateTable = CALENDAR(MIN(Trips[request_datetime]), MAX(Trips[request_datetime]))
  ```
  and relate `DateTable[Date]` → `Trips[request_datetime]` (by date).

## 3. DAX measures

Paste these into a new measures table (`Home → Enter Data`, name it
`_Measures`, then add each as a new measure on it).

```dax
Total Trips = COUNTROWS(Trips)

Completed Trips =
CALCULATE(COUNTROWS(Trips), Trips[trip_status] = "Completed")

Cancelled Trips =
CALCULATE(COUNTROWS(Trips), Trips[is_cancelled] = 1)

Cancellation Rate =
DIVIDE([Cancelled Trips], [Total Trips])

Total Revenue =
CALCULATE(SUM(Trips[fare_amount]), Trips[trip_status] = "Completed")

Average Fare =
CALCULATE(AVERAGE(Trips[fare_amount]), Trips[trip_status] = "Completed")

Average Distance (km) =
CALCULATE(AVERAGE(Trips[distance_km]), Trips[trip_status] = "Completed")

Average Duration (min) =
CALCULATE(AVERAGE(Trips[duration_min]), Trips[trip_status] = "Completed")

Fare per KM =
DIVIDE([Total Revenue],
    CALCULATE(SUM(Trips[distance_km]), Trips[trip_status] = "Completed"))

Active Riders = DISTINCTCOUNT(Trips[rider_id])

Active Drivers = DISTINCTCOUNT(Trips[driver_id])

Trips per Rider = DIVIDE([Total Trips], [Active Riders])

Trips per Driver = DIVIDE([Total Trips], [Active Drivers])

Revenue per Driver = DIVIDE([Total Revenue], [Active Drivers])

Average Rating =
CALCULATE(AVERAGE(Trips[driver_rating_for_rider]), Trips[trip_status] = "Completed")

Repeat Customer Rate =
VAR RiderTripCounts =
    SUMMARIZE(
        FILTER(Trips, Trips[trip_status] = "Completed"),
        Trips[rider_id],
        "CompletedTrips", CALCULATE(COUNTROWS(Trips))
    )
VAR RepeatRiders = COUNTROWS(FILTER(RiderTripCounts, [CompletedTrips] > 1))
VAR TotalRiders = COUNTROWS(RiderTripCounts)
RETURN DIVIDE(RepeatRiders, TotalRiders)

High Risk Trips =
CALCULATE(COUNTROWS(Predictions), Predictions[risk_tier] = "High")

Avg Cancellation Probability =
AVERAGE(Predictions[predicted_cancel_probability])
```

## 4. Page-by-page layout

### Page 1 — Executive Overview
- **KPI cards**: `[Total Trips]`, `[Total Revenue]`, `[Completed Trips]`,
  `[Cancellation Rate]`, `[Active Riders]`, `[Active Drivers]`,
  `[Average Fare]`, `[Average Rating]`
- **Line chart**: revenue trend — `request_datetime` (by day/week) on X,
  `[Total Revenue]` on Y
- **Line chart**: trip trend — same X, `[Total Trips]` on Y
- **Bar chart**: `pickup_city` on X, `[Total Trips]` on Y
- **Bar/pie**: `vehicle_type` on X or legend, `[Total Revenue]` on Y

### Page 2 — Demand & Operations
- **Column chart**: `request_hour` on X, `[Total Trips]` on Y
- **Column chart**: `request_day` on X, `[Total Trips]` on Y
- **Matrix/heatmap**: `request_dow` on rows, `request_hour` on columns,
  `[Total Trips]` as values (conditional formatting = background color)
- **Card**: peak hour/day (use a measure with `TOPN`, or just read off the
  heatmap)
- **Bar chart**: `pickup_city` + `area_name` (needs a join back to
  `locations.csv` if you want area-level detail, not just city)
- **Bar chart**: `cancellation_reason` on Y, count on X (filter
  `trip_status <> "Completed"`)

### Page 3 — Driver Performance
- **Cards**: `[Active Drivers]`, `[Revenue per Driver]`, `[Trips per Driver]`
- **Table/matrix**: `driver_id`, trip count, revenue, cancellation rate —
  sorted descending by revenue (this is exactly
  `sql/05_advanced_analysis.sql`'s driver-ranking query; you can also pull
  `vw_driver_performance` straight from MySQL for this table)
- **Bar chart**: top 15 drivers by revenue
- **Scatter**: `driver_avg_rating` (X) vs. driver-level cancellation rate
  (Y), bubble size = trip count — the "driver performance matrix"
- **Bar chart**: revenue by `vehicle_type`

### Page 4 — Customer & Cancellation Risk
- **Cards**: `[Active Riders]`, `[Repeat Customer Rate]`,
  `[High Risk Trips]`, `[Avg Cancellation Probability]`
- **Bar chart**: RFM segment (import `sql/08_customer_segmentation.sql`'s
  output as a table) on X, rider count on Y
- **Line chart**: monthly active riders / new / returning (import
  `sql/07_customer_retention.sql`'s output)
- **Donut chart**: `Predictions[risk_tier]` — Low/Medium/High split
- **Table**: high-risk trips — filter `Predictions[risk_tier] = "High"`,
  columns `trip_id`, `predicted_cancel_probability`, `rider_id`, `driver_id`
- **Bar chart**: `ShapImportance` table — `feature` on Y,
  `mean_abs_shap` on X, sorted descending (this is your model-explainability
  visual, straight from the SHAP notebook's output)

## 5. Once built

Export screenshots of each page to `dashboard/01_executive_overview.png`,
`02_demand_operations.png`, `03_driver_performance.png`,
`04_customer_cancellation_risk.png`, and save the `.pbix` itself into this
`powerbi/` folder. Then add the corresponding `![...]` image embeds to the
main `README.md` (see the Power BI Dashboard section there for the exact
filenames it expects).
