"""Generates the 4 dashboard preview PNGs in this folder from real project data.
Not a Power BI export (Power BI Desktop is Windows-only and unavailable in the
environment this project was built in) — a matplotlib-composed mockup of what
the four pages in ../powerbi/README.md look like once built, using the actual
numbers from this project's pipeline output (../data/processed/*.csv).

Run from this directory (dashboard/), with the project venv active:
    cd dashboard && python3 generate_previews.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
from pathlib import Path

PROCESSED = Path("../data/processed")
OUT = Path(".")

trips = pd.read_csv(PROCESSED / "trips_analysis_ready.csv", parse_dates=["request_datetime"])
predictions = pd.read_csv(PROCESSED / "cancellation_predictions.csv", parse_dates=["request_datetime"])
model_comparison = pd.read_csv(PROCESSED / "model_comparison.csv")
shap_importance = pd.read_csv(PROCESSED / "shap_feature_importance.csv")
completed = trips.loc[trips.trip_status == "Completed"]

# --- palette / style, consistent with ../images/eda + ../images/ml ---
NAVY = "#1F2A44"
ACCENT = "#4C72B0"
GREEN = "#55A868"
ORANGE = "#DD8452"
RED = "#C44E52"
PURPLE = "#8172B2"
BG = "#F4F6FA"
CARD_BG = "#FFFFFF"

plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.edgecolor": "#D8DEE9",
    "axes.grid": True,
    "grid.color": "#E6E9F0",
    "grid.linewidth": 0.6,
})


def page_header(fig, title, subtitle):
    fig.patches.append(mpatches.Rectangle((0, 0.955), 1, 0.045, transform=fig.transFigure,
                                           color=NAVY, zorder=0, linewidth=0))
    fig.text(0.018, 0.975, "RIDE-SHARING ANALYTICS", fontsize=11, color="white",
              va="center", weight="bold")
    fig.text(0.018, 0.933, title, fontsize=19, color=NAVY, va="center", weight="bold")
    fig.text(0.018, 0.910, subtitle, fontsize=9.5, color="#5B6472", va="center")


def kpi_card(ax, label, value, color):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(mpatches.FancyBboxPatch((0.02, 0.06), 0.96, 0.88, boxstyle="round,pad=0.02,rounding_size=0.05",
                                          linewidth=0, facecolor=CARD_BG, zorder=1))
    ax.add_patch(mpatches.Rectangle((0.02, 0.06), 0.045, 0.88, facecolor=color, zorder=2, linewidth=0))
    ax.text(0.16, 0.60, str(value), fontsize=19, weight="bold", color=NAVY, va="center", zorder=3)
    ax.text(0.16, 0.28, label, fontsize=9.5, color="#5B6472", va="center", zorder=3)


def savefig(fig, name):
    fig.patch.set_facecolor(BG)
    fig.savefig(OUT / name, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"saved dashboard/{name}")


# ===========================================================================
# Page 1 — Executive Overview
# ===========================================================================
fig = plt.figure(figsize=(15, 9))
page_header(fig, "Executive Overview", "Company-wide KPIs across all trips, riders, and drivers")

gs = gridspec.GridSpec(3, 4, figure=fig, top=0.87, bottom=0.06, left=0.03, right=0.98, hspace=0.55, wspace=0.35)

kpis = [
    ("Total Trips", f"{len(trips):,}", ACCENT),
    ("Total Revenue", f"₹{completed.fare_amount.sum()/1e6:.2f}M", GREEN),
    ("Completed Trips", f"{len(completed):,}", ACCENT),
    ("Cancellation Rate", f"{trips.is_cancelled.mean()*100:.1f}%", RED),
    ("Active Riders", f"{trips.rider_id.nunique():,}", PURPLE),
    ("Active Drivers", f"{trips.driver_id.nunique():,}", PURPLE),
    ("Average Fare", f"₹{completed.fare_amount.mean():.0f}", ORANGE),
    ("Average Rating", f"{completed.driver_rating_for_rider.mean():.2f} ★", ORANGE),
]
for i, (label, value, color) in enumerate(kpis):
    ax = fig.add_subplot(gs[0, i % 4] if i < 4 else gs[1, i % 4])
    kpi_card(ax, label, value, color)

ax_trend = fig.add_subplot(gs[2, 0:2])
weekly_rev = completed.set_index("request_datetime").resample("W")["fare_amount"].sum()
ax_trend.plot(weekly_rev.index, weekly_rev.values, color=ACCENT, linewidth=2)
ax_trend.fill_between(weekly_rev.index, weekly_rev.values, color=ACCENT, alpha=0.12)
ax_trend.set_title("Revenue Trend (Weekly)", fontsize=10.5, weight="bold", color=NAVY, loc="left")
ax_trend.tick_params(labelsize=8)

ax_city = fig.add_subplot(gs[2, 2])
rev_city = completed.groupby("pickup_city").fare_amount.sum().sort_values(ascending=False)
ax_city.bar(rev_city.index, rev_city.values / 1e3, color=ACCENT)
ax_city.set_title("Trips by City (Revenue, ₹K)", fontsize=10.5, weight="bold", color=NAVY, loc="left")
ax_city.tick_params(axis="x", rotation=45, labelsize=7.5)
ax_city.tick_params(axis="y", labelsize=8)

ax_veh = fig.add_subplot(gs[2, 3])
rev_veh = completed.groupby("vehicle_type").fare_amount.sum().sort_values(ascending=False)
colors_veh = [ACCENT, GREEN, ORANGE, PURPLE, RED][:len(rev_veh)]
ax_veh.bar(rev_veh.index, rev_veh.values / 1e3, color=colors_veh)
ax_veh.set_title("Revenue by Vehicle Type (₹K)", fontsize=10.5, weight="bold", color=NAVY, loc="left")
ax_veh.tick_params(axis="x", rotation=45, labelsize=7.5)
ax_veh.tick_params(axis="y", labelsize=8)

savefig(fig, "01_executive_overview.png")

# ===========================================================================
# Page 2 — Demand & Operations
# ===========================================================================
fig = plt.figure(figsize=(15, 9))
page_header(fig, "Demand & Operations", "When and where rides are requested, and why they're cancelled")

gs = gridspec.GridSpec(2, 3, figure=fig, top=0.87, bottom=0.08, left=0.04, right=0.98, hspace=0.5, wspace=0.32)

ax_hour = fig.add_subplot(gs[0, 0])
hourly = trips.groupby("request_hour").size()
ax_hour.plot(hourly.index, hourly.values, color=ACCENT, marker="o", markersize=3, linewidth=1.8)
ax_hour.set_title("Hourly Demand", fontsize=10.5, weight="bold", color=NAVY, loc="left")
ax_hour.tick_params(labelsize=8)

ax_day = fig.add_subplot(gs[0, 1])
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
daily = trips.groupby("request_day").size().reindex(day_order)
ax_day.bar([d[:3] for d in daily.index], daily.values, color=GREEN)
ax_day.set_title("Daily Demand", fontsize=10.5, weight="bold", color=NAVY, loc="left")
ax_day.tick_params(labelsize=8)

ax_heat = fig.add_subplot(gs[0, 2])
heat = trips.groupby(["request_dow", "request_hour"]).size().unstack(fill_value=0)
im = ax_heat.imshow(heat.values, aspect="auto", cmap="Blues")
ax_heat.set_yticks(range(7)); ax_heat.set_yticklabels([d[:3] for d in day_order], fontsize=7.5)
ax_heat.set_xticks(range(0, 24, 4)); ax_heat.set_xticklabels(range(0, 24, 4), fontsize=7.5)
ax_heat.set_title("Demand Heatmap (Day × Hour)", fontsize=10.5, weight="bold", color=NAVY, loc="left")

ax_reason = fig.add_subplot(gs[1, 0:2])
reasons = trips.loc[trips.trip_status != "Completed", "cancellation_reason"].value_counts().head(8)
ax_reason.barh(reasons.index[::-1], reasons.values[::-1], color=RED)
ax_reason.set_title("Top Cancellation Reasons", fontsize=10.5, weight="bold", color=NAVY, loc="left")
ax_reason.tick_params(labelsize=8)

ax_citycancel = fig.add_subplot(gs[1, 2])
cancel_city = (trips.groupby("pickup_city").is_cancelled.mean() * 100).sort_values(ascending=False)
ax_citycancel.bar(cancel_city.index, cancel_city.values, color=ORANGE)
ax_citycancel.set_title("Cancellation Rate by City (%)", fontsize=10.5, weight="bold", color=NAVY, loc="left")
ax_citycancel.tick_params(axis="x", rotation=45, labelsize=7.5)
ax_citycancel.tick_params(axis="y", labelsize=8)

savefig(fig, "02_demand_operations.png")

# ===========================================================================
# Page 3 — Driver Performance
# ===========================================================================
fig = plt.figure(figsize=(15, 9))
page_header(fig, "Driver Performance", "Revenue, ranking, and cancellation behavior by driver")

gs = gridspec.GridSpec(3, 3, figure=fig, top=0.87, bottom=0.06, left=0.03, right=0.98, hspace=0.55, wspace=0.35)

driver_perf = (
    completed.groupby("driver_id")
    .agg(trips=("trip_id", "count"), revenue=("fare_amount", "sum"), avg_rating=("driver_avg_rating", "first"))
    .reset_index()
)
cancel_by_driver = (trips.groupby("driver_id").is_cancelled.mean() * 100).reset_index(name="cancellation_rate_pct")
driver_perf = driver_perf.merge(cancel_by_driver, on="driver_id")

kpis3 = [
    ("Active Drivers", f"{trips.driver_id.nunique():,}", ACCENT),
    ("Revenue / Driver", f"₹{completed.fare_amount.sum()/trips.driver_id.nunique():,.0f}", GREEN),
    ("Trips / Driver", f"{len(trips)/trips.driver_id.nunique():.1f}", PURPLE),
]
for i, (label, value, color) in enumerate(kpis3):
    ax = fig.add_subplot(gs[0, i])
    kpi_card(ax, label, value, color)

ax_top = fig.add_subplot(gs[1:, 0:2])
top15 = driver_perf.sort_values("revenue", ascending=False).head(15).sort_values("revenue")
ax_top.barh(top15.driver_id.astype(str), top15.revenue, color=ACCENT)
ax_top.set_title("Top 15 Drivers by Revenue", fontsize=10.5, weight="bold", color=NAVY, loc="left")
ax_top.tick_params(labelsize=7.5)

ax_scatter = fig.add_subplot(gs[1, 2])
sizes = (driver_perf.trips / driver_perf.trips.max()) * 200 + 10
ax_scatter.scatter(driver_perf.avg_rating, driver_perf.cancellation_rate_pct, s=sizes, color=ORANGE, alpha=0.6, edgecolor="white")
ax_scatter.set_title("Rating vs. Cancellation Rate", fontsize=10.5, weight="bold", color=NAVY, loc="left")
ax_scatter.set_xlabel("Driver Rating", fontsize=8)
ax_scatter.set_ylabel("Cancel Rate (%)", fontsize=8)
ax_scatter.tick_params(labelsize=7.5)

ax_veh3 = fig.add_subplot(gs[2, 2])
rev_veh3 = completed.groupby("vehicle_type").fare_amount.sum().sort_values(ascending=False)
ax_veh3.bar(rev_veh3.index, rev_veh3.values / 1e3, color=GREEN)
ax_veh3.set_title("Vehicle Performance (Revenue ₹K)", fontsize=10.5, weight="bold", color=NAVY, loc="left")
ax_veh3.tick_params(axis="x", rotation=45, labelsize=7)
ax_veh3.tick_params(axis="y", labelsize=7.5)

savefig(fig, "03_driver_performance.png")

# ===========================================================================
# Page 4 — Customer & Cancellation Risk
# ===========================================================================
fig = plt.figure(figsize=(15, 9))
page_header(fig, "Customer & Cancellation Risk", "Rider engagement and ML-driven cancellation risk")

gs = gridspec.GridSpec(3, 4, figure=fig, top=0.87, bottom=0.06, left=0.03, right=0.98, hspace=0.55, wspace=0.35)

rider_completed_counts = completed.groupby("rider_id").size()
repeat_rate = (rider_completed_counts > 1).mean() * 100

kpis4 = [
    ("Active Riders", f"{trips.rider_id.nunique():,}", ACCENT),
    ("Repeat Customer Rate", f"{repeat_rate:.1f}%", GREEN),
    ("High-Risk Trips", f"{(predictions.risk_tier == 'High').sum():,}", RED),
    ("Avg Cancel Probability", f"{predictions.predicted_cancel_probability.mean()*100:.1f}%", ORANGE),
]
for i, (label, value, color) in enumerate(kpis4):
    ax = fig.add_subplot(gs[0, i])
    kpi_card(ax, label, value, color)

ax_donut = fig.add_subplot(gs[1:, 0:2])
risk_counts = predictions.risk_tier.value_counts().reindex(["Low", "Medium", "High"]).fillna(0)
colors_risk = [GREEN, ORANGE, RED]
wedges, _, autotexts = ax_donut.pie(
    risk_counts.values, labels=risk_counts.index, autopct="%1.1f%%", startangle=90,
    colors=colors_risk, wedgeprops=dict(width=0.42, edgecolor=BG), pctdistance=0.79,
    textprops={"fontsize": 9},
)
ax_donut.set_title("Cancellation Risk Tier Distribution (test set)", fontsize=10.5, weight="bold", color=NAVY, loc="left")

ax_shap = fig.add_subplot(gs[1:, 2:4])
top_shap = shap_importance.head(10).sort_values("mean_abs_shap")
ax_shap.barh(top_shap.feature, top_shap.mean_abs_shap, color=PURPLE)
ax_shap.set_title("What Drives Cancellation Risk (SHAP mean |value|)", fontsize=10.5, weight="bold", color=NAVY, loc="left")
ax_shap.tick_params(labelsize=8)

savefig(fig, "04_customer_cancellation_risk.png")

print("\nAll 4 dashboard preview PNGs saved to dashboard/")
