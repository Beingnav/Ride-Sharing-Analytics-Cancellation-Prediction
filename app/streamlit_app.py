"""
Ride-Sharing Analytics & Cancellation Prediction — Live Demo

Two things this app does, both against real project artifacts (no mock
data):
  1. Analytics Dashboard — interactive version of the four Power BI pages
     described in powerbi/README.md, built from data/processed/*.csv.
  2. Cancellation Risk Predictor — fill in a hypothetical trip, get a live
     prediction from the actual trained model (models/*.pkl), with a
     real-time SHAP explanation of that specific prediction.

Run from the repo root (with the venv active):
    streamlit run app/streamlit_app.py
"""

import json
from datetime import date, time, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"

st.set_page_config(
    page_title="Ride-Sharing Analytics — Live Demo",
    page_icon="🚖",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Data / model loading
# ---------------------------------------------------------------------------

@st.cache_data
def load_data():
    trips = pd.read_csv(DATA_PROCESSED / "trips_analysis_ready.csv", parse_dates=["request_datetime"])
    predictions = pd.read_csv(DATA_PROCESSED / "cancellation_predictions.csv", parse_dates=["request_datetime"])
    model_comparison = pd.read_csv(DATA_PROCESSED / "model_comparison.csv")
    shap_importance = pd.read_csv(DATA_PROCESSED / "shap_feature_importance.csv")
    return trips, predictions, model_comparison, shap_importance


@st.cache_resource
def load_model_bundle():
    metadata = json.loads((MODELS_DIR / "model_metadata.json").read_text())
    model = joblib.load(MODELS_DIR / metadata["model_filename"])
    scaler = joblib.load(MODELS_DIR / "scaler.pkl")
    feature_columns = json.loads((MODELS_DIR / "feature_columns.json").read_text())
    raw_columns = json.loads((MODELS_DIR / "raw_feature_columns.json").read_text())
    categorical_options = json.loads((MODELS_DIR / "categorical_options.json").read_text())
    feature_ranges = json.loads((MODELS_DIR / "feature_ranges.json").read_text())
    base_fare_by_vehicle = json.loads((MODELS_DIR / "base_fare_by_vehicle_type.json").read_text())
    return {
        "model": model, "scaler": scaler, "metadata": metadata,
        "feature_columns": feature_columns, "raw_columns": raw_columns,
        "categorical_options": categorical_options, "feature_ranges": feature_ranges,
        "base_fare_by_vehicle": base_fare_by_vehicle,
    }


try:
    trips, predictions, model_comparison, shap_importance = load_data()
    bundle = load_model_bundle()
    ARTIFACTS_OK = True
except FileNotFoundError as exc:
    ARTIFACTS_OK = False
    MISSING_FILE = str(exc)


def risk_tier(p, cuts):
    if p < cuts["low_max"]:
        return "Low", "🟢"
    elif p < cuts["medium_max"]:
        return "Medium", "🟡"
    return "High", "🔴"


def predict_cancellation(raw_row: dict, bundle: dict):
    """raw_row: dict of {feature_name: value} for every column in raw_columns['all']."""
    raw_cols = bundle["raw_columns"]
    row_df = pd.DataFrame([raw_row])[raw_cols["all"]]
    encoded = pd.get_dummies(row_df, columns=raw_cols["categorical"])
    encoded = encoded.reindex(columns=bundle["feature_columns"], fill_value=0).astype(float)

    if bundle["metadata"]["is_linear_model"]:
        model_input = pd.DataFrame(
            bundle["scaler"].transform(encoded), columns=bundle["feature_columns"]
        )
    else:
        model_input = encoded

    proba = float(bundle["model"].predict_proba(model_input)[0, 1])
    tier, emoji = risk_tier(proba, bundle["metadata"]["risk_tier_cuts"])
    return proba, tier, emoji, encoded, model_input


def explain_prediction(model_input: pd.DataFrame, bundle: dict):
    """Live, single-row explanation. Tree models get real SHAP (TreeExplainer,
    fast even per-request). The linear model gets an exact closed-form
    equivalent (coef * standardized value) without needing a shap background
    dataset shipped alongside the app."""
    feature_columns = bundle["feature_columns"]
    model = bundle["model"]

    if bundle["metadata"]["is_linear_model"]:
        contributions = model.coef_[0] * model_input.iloc[0].values
    else:
        import shap
        explainer = shap.TreeExplainer(model)
        raw = explainer.shap_values(model_input)
        if isinstance(raw, list):
            values = raw[1]
        elif np.array(raw).ndim == 3:
            values = np.array(raw)[:, :, 1]
        else:
            values = raw
        contributions = np.array(values)[0]

    contrib_df = pd.DataFrame({"feature": feature_columns, "contribution": contributions})
    contrib_df["abs_contribution"] = contrib_df.contribution.abs()
    return contrib_df.sort_values("abs_contribution", ascending=False).head(8)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

st.title("🚖 Ride-Sharing Analytics & Cancellation Prediction")
st.caption("Live demo — analytics dashboard and cancellation-risk predictor, both running against real pipeline output.")

if not ARTIFACTS_OK:
    st.error(
        f"Missing artifact: {MISSING_FILE}\n\n"
        "Run the notebooks in `python/` in order (01 through 07) first — "
        "this app reads their output from `data/processed/` and `models/`, "
        "it doesn't compute anything itself."
    )
    st.stop()

page = st.sidebar.radio("Navigate", ["📊 Analytics Dashboard", "🚦 Cancellation Risk Predictor"])
st.sidebar.divider()
st.sidebar.markdown(
    f"**Model in use:** {bundle['metadata']['best_model_name']}\n\n"
    f"**Decision threshold:** {bundle['metadata']['decision_threshold']}\n\n"
    "See `README.md` for the full model comparison and how this was chosen."
)
if not bundle["metadata"]["xgboost_available_at_training_time"]:
    st.sidebar.caption(
        "⚠️ XGBoost wasn't available when this model was trained (needs "
        "`brew install libomp` on macOS). Re-run notebook 06 after "
        "installing it to compare against XGBoost too."
    )

# ---------------------------------------------------------------------------
# Page 1 — Analytics Dashboard
# ---------------------------------------------------------------------------
if page == "📊 Analytics Dashboard":
    completed = trips.loc[trips.trip_status == "Completed"]

    tab1, tab2, tab3, tab4 = st.tabs([
        "Executive Overview", "Demand & Operations", "Driver Performance", "Customer & Cancellation Risk",
    ])

    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Trips", f"{len(trips):,}")
        c2.metric("Total Revenue", f"₹{completed.fare_amount.sum():,.0f}")
        c3.metric("Cancellation Rate", f"{trips.is_cancelled.mean()*100:.1f}%")
        c4.metric("Active Riders", f"{trips.rider_id.nunique():,}")
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Active Drivers", f"{trips.driver_id.nunique():,}")
        c6.metric("Average Fare", f"₹{completed.fare_amount.mean():.2f}")
        c7.metric("Avg Rating", f"{completed.driver_rating_for_rider.mean():.2f} ★")
        c8.metric("Fare / km", f"₹{(completed.fare_amount / completed.distance_km).mean():.2f}")

        col1, col2 = st.columns(2)
        with col1:
            revenue_trend = completed.set_index("request_datetime").resample("W")["fare_amount"].sum().reset_index()
            fig = px.line(revenue_trend, x="request_datetime", y="fare_amount", title="Weekly Revenue Trend")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            rev_vehicle = completed.groupby("vehicle_type")["fare_amount"].sum().sort_values(ascending=False).reset_index()
            fig = px.bar(rev_vehicle, x="vehicle_type", y="fare_amount", title="Revenue by Vehicle Type")
            st.plotly_chart(fig, use_container_width=True)

        rev_city = completed.groupby("pickup_city")["fare_amount"].sum().sort_values(ascending=False).reset_index()
        fig = px.bar(rev_city, x="pickup_city", y="fare_amount", title="Revenue by City")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            hourly = trips.groupby("request_hour").size().reset_index(name="trips")
            fig = px.line(hourly, x="request_hour", y="trips", markers=True, title="Demand by Hour")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            daily = trips.groupby("request_day").size().reindex(day_order).reset_index(name="trips")
            fig = px.bar(daily, x="request_day", y="trips", title="Demand by Day of Week")
            st.plotly_chart(fig, use_container_width=True)

        heat = trips.groupby(["request_dow", "request_hour"]).size().reset_index(name="trips")
        heat_pivot = heat.pivot(index="request_dow", columns="request_hour", values="trips").fillna(0)
        heat_pivot.index = [day_order[i] for i in heat_pivot.index]
        fig = px.imshow(heat_pivot, aspect="auto", title="Demand Heatmap (Day × Hour)", color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            reasons = trips.loc[trips.trip_status != "Completed", "cancellation_reason"].value_counts().head(8).reset_index()
            reasons.columns = ["reason", "trips"]
            fig = px.bar(reasons, x="trips", y="reason", orientation="h", title="Top Cancellation Reasons")
            st.plotly_chart(fig, use_container_width=True)
        with col4:
            cancel_city = (trips.groupby("pickup_city").is_cancelled.mean() * 100).sort_values(ascending=False).reset_index()
            cancel_city.columns = ["city", "cancellation_rate_pct"]
            fig = px.bar(cancel_city, x="city", y="cancellation_rate_pct", title="Cancellation Rate by City")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        driver_perf = (
            completed.groupby("driver_id")
            .agg(trips=("trip_id", "count"), revenue=("fare_amount", "sum"), avg_rating=("driver_avg_rating", "first"))
            .reset_index()
        )
        cancel_by_driver = (trips.groupby("driver_id").is_cancelled.mean() * 100).reset_index(name="cancellation_rate_pct")
        driver_perf = driver_perf.merge(cancel_by_driver, on="driver_id")

        col1, col2 = st.columns(2)
        with col1:
            top15 = driver_perf.sort_values("revenue", ascending=False).head(15)
            fig = px.bar(top15, x="revenue", y=top15.driver_id.astype(str), orientation="h", title="Top 15 Drivers by Revenue")
            fig.update_yaxes(title="Driver ID", categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.scatter(
                driver_perf, x="avg_rating", y="cancellation_rate_pct", size="trips",
                title="Driver Rating vs. Cancellation Rate (bubble = trip count)",
                labels={"avg_rating": "Driver Rating", "cancellation_rate_pct": "Cancellation Rate (%)"},
            )
            st.plotly_chart(fig, use_container_width=True)

        rev_vehicle_driver = completed.groupby("vehicle_type")["fare_amount"].sum().reset_index()
        fig = px.bar(rev_vehicle_driver, x="vehicle_type", y="fare_amount", title="Vehicle Type Performance (Revenue)")
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        c1, c2, c3, c4 = st.columns(4)
        rider_completed_counts = completed.groupby("rider_id").size()
        repeat_rate = (rider_completed_counts > 1).mean() * 100
        c1.metric("Active Riders", f"{trips.rider_id.nunique():,}")
        c2.metric("Repeat Customer Rate", f"{repeat_rate:.1f}%")
        c3.metric("High-Risk Trips (test set)", f"{(predictions.risk_tier == 'High').sum():,}")
        c4.metric("Avg Cancel Probability", f"{predictions.predicted_cancel_probability.mean():.3f}")

        col1, col2 = st.columns(2)
        with col1:
            risk_counts = predictions.risk_tier.value_counts().reindex(["Low", "Medium", "High"]).reset_index()
            risk_counts.columns = ["risk_tier", "trips"]
            fig = px.pie(risk_counts, names="risk_tier", values="trips", title="Cancellation Risk Tier Distribution (test set)",
                         color="risk_tier", color_discrete_map={"Low": "#55A868", "Medium": "#DD8452", "High": "#C44E52"})
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(shap_importance.head(10).sort_values("mean_abs_shap"), x="mean_abs_shap", y="feature",
                         orientation="h", title="What Drives Cancellation Risk (SHAP)")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Highest-risk trips in the test set")
        high_risk = predictions.loc[predictions.risk_tier == "High"].sort_values(
            "predicted_cancel_probability", ascending=False
        ).head(20)
        st.dataframe(
            high_risk[["trip_id", "rider_id", "driver_id", "request_datetime", "predicted_cancel_probability", "actual_cancelled"]],
            use_container_width=True, hide_index=True,
        )

        st.caption(
            "RFM segmentation and month-over-month retention live in "
            "`sql/07_customer_retention.sql` and `sql/08_customer_segmentation.sql` — "
            "not duplicated here since they're SQL-native window-function queries."
        )


# ---------------------------------------------------------------------------
# Page 2 — Cancellation Risk Predictor
# ---------------------------------------------------------------------------
else:
    st.subheader("🚦 Cancellation Risk Predictor")
    st.markdown(
        f"Fill in a hypothetical trip and get a live prediction from the actual "
        f"trained **{bundle['metadata']['best_model_name']}** model — same "
        f"preprocessing, same feature set, as `python/06_cancellation_prediction.ipynb`."
    )

    ranges = bundle["feature_ranges"]
    options = bundle["categorical_options"]

    PRESETS = {
        "Typical trip": dict(
            distance_km=ranges["distance_km"]["median"], surge_multiplier=1.0,
            hour=14, driver_avg_rating=4.3, driver_experience_days=400,
            driver_prior_cancel_rate=0.15, rider_prior_cancel_rate=0.15,
        ),
        "High-risk (surge + new, low-rated driver)": dict(
            distance_km=ranges["distance_km"]["median"] * 1.5, surge_multiplier=1.9,
            hour=23, driver_avg_rating=3.4, driver_experience_days=10,
            driver_prior_cancel_rate=0.45, rider_prior_cancel_rate=0.35,
        ),
        "Low-risk (off-peak, experienced driver)": dict(
            distance_km=ranges["distance_km"]["median"] * 0.7, surge_multiplier=1.0,
            hour=11, driver_avg_rating=4.8, driver_experience_days=700,
            driver_prior_cancel_rate=0.05, rider_prior_cancel_rate=0.05,
        ),
    }
    preset_choice = st.radio("Quick scenario", list(PRESETS.keys()), horizontal=True)
    preset = PRESETS[preset_choice]

    with st.form("risk_form"):
        st.markdown("**Trip details**")
        col1, col2, col3 = st.columns(3)
        vehicle_type = col1.selectbox("Vehicle type", options["vehicle_type"], index=2)
        pickup_city = col2.selectbox("Pickup city", options["pickup_city"])
        drop_city = col3.selectbox("Drop city", options["pickup_city"],
                                    index=1 if len(options["pickup_city"]) > 1 else 0)

        col4, col5, col6 = st.columns(3)
        distance_km = col4.slider("Distance (km)", 0.5, float(ranges["distance_km"]["max"]), float(preset["distance_km"]))
        surge_multiplier = col5.slider("Surge multiplier", 1.0, float(ranges["surge_multiplier"]["max"]), float(preset["surge_multiplier"]), 0.05)
        payment_method = col6.selectbox("Payment method", options["payment_method"])

        col7, col8 = st.columns(2)
        trip_date = col7.date_input("Trip date", value=date(2025, 6, 15))
        trip_time = col8.time_input("Trip time", value=time(preset["hour"], 0))

        st.markdown("**Rider profile**")
        col9, col10, col11, col12 = st.columns(4)
        age = col9.number_input("Rider age", 18, 80, 30)
        rider_gender = col10.selectbox("Rider gender", options["rider_gender"])
        preferred_payment = col11.selectbox("Preferred payment", options["payment_method"])
        rider_tenure_days = col12.number_input("Rider tenure (days since signup)", 0, 2000, 200)

        col13, col14, col15 = st.columns(3)
        rider_prior_trip_count = col13.number_input("Rider's prior completed trips", 0, 500, 15)
        rider_prior_cancel_rate = col14.slider("Rider's historical cancel rate", 0.0, 1.0, float(preset["rider_prior_cancel_rate"]))
        days_since_rider_last_trip = col15.number_input("Days since rider's last trip", -1, 365, 5)

        st.markdown("**Driver profile**")
        col16, col17, col18 = st.columns(3)
        driver_avg_rating = col16.slider("Driver average rating", 1.0, 5.0, float(preset["driver_avg_rating"]), 0.1)
        driver_experience_days = col17.number_input("Driver experience (days)", 0, 2000, int(preset["driver_experience_days"]))
        driver_prior_trip_count = col18.number_input("Driver's prior completed trips", 0, 5000, 200)

        col19, col20 = st.columns(2)
        driver_prior_cancel_rate = col19.slider("Driver's historical cancel rate", 0.0, 1.0, float(preset["driver_prior_cancel_rate"]))
        days_since_driver_last_trip = col20.number_input("Days since driver's last trip", -1, 365, 1)

        submitted = st.form_submit_button("Predict cancellation risk", type="primary")

    if submitted:
        dt = datetime.combine(trip_date, trip_time)
        raw_row = {
            "distance_km": distance_km,
            "base_fare": bundle["base_fare_by_vehicle"][vehicle_type],
            "surge_multiplier": surge_multiplier,
            "request_hour": dt.hour,
            "request_dow": dt.weekday(),
            "request_month": dt.month,
            "is_weekend": int(dt.weekday() in [5, 6]),
            "is_peak_hour": int(dt.hour in [8, 9, 18, 19, 20]),
            "vehicle_type": vehicle_type,
            "pickup_city": pickup_city,
            "drop_city": drop_city,
            "payment_method": payment_method,
            "rider_gender": rider_gender,
            "age": age,
            "preferred_payment": preferred_payment,
            "rider_tenure_days": rider_tenure_days,
            "driver_avg_rating": driver_avg_rating,
            "driver_experience_days": driver_experience_days,
            "rider_prior_trip_count": rider_prior_trip_count,
            "rider_prior_cancel_rate": rider_prior_cancel_rate,
            "rider_prior_avg_fare": ranges.get("rider_prior_avg_fare", {}).get("median", 140.0),
            "days_since_rider_last_trip": days_since_rider_last_trip,
            "driver_prior_trip_count": driver_prior_trip_count,
            "driver_prior_cancel_rate": driver_prior_cancel_rate,
            "driver_prior_completed_count": int(driver_prior_trip_count * (1 - driver_prior_cancel_rate)),
            "days_since_driver_last_trip": days_since_driver_last_trip,
        }

        proba, tier, emoji, encoded, model_input = predict_cancellation(raw_row, bundle)

        st.divider()
        result_col, gauge_col = st.columns([1, 1])
        with result_col:
            st.metric("Predicted cancellation probability", f"{proba*100:.1f}%")
            st.markdown(f"### {emoji} Risk tier: **{tier}**")
            st.caption(
                f"Cuts: Low < {bundle['metadata']['risk_tier_cuts']['low_max']*100:.0f}% ≤ Medium < "
                f"{bundle['metadata']['risk_tier_cuts']['medium_max']*100:.0f}% ≤ High"
            )
        with gauge_col:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=proba * 100,
                number={"suffix": "%"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#333"},
                    "steps": [
                        {"range": [0, 30], "color": "#55A868"},
                        {"range": [30, 60], "color": "#DD8452"},
                        {"range": [60, 100], "color": "#C44E52"},
                    ],
                },
                title={"text": "Cancellation Risk"},
            ))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Why this prediction? (live SHAP explanation)")
        contrib_df = explain_prediction(model_input, bundle)
        contrib_df["direction"] = np.where(contrib_df.contribution > 0, "↑ raises risk", "↓ lowers risk")
        fig = px.bar(
            contrib_df.sort_values("contribution"), x="contribution", y="feature", orientation="h",
            color="direction", color_discrete_map={"↑ raises risk": "#C44E52", "↓ lowers risk": "#55A868"},
            title="Top feature contributions to this specific prediction",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "This is a live SHAP TreeExplainer run on the exact model that's shipped in "
            "`models/` — the same technique as `python/07_model_explainability.ipynb`, "
            "computed on-demand for this one input instead of the batch test set."
        )
