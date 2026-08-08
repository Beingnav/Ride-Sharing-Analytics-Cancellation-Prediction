# 🚖 Ride-Sharing Analytics & Cancellation Prediction

### End-to-End Data Analytics & Machine Learning Project

**SQL • Python • Statistics • Machine Learning • SHAP • Power BI • Streamlit**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)](https://www.mysql.com/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-yellow?logo=powerbi)](https://powerbi.microsoft.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)](https://streamlit.io/)
[![Scikit--learn](https://img.shields.io/badge/Scikit--learn-Machine%20Learning-F7931E?logo=scikit-learn)](https://scikit-learn.org/)
[![SHAP](https://img.shields.io/badge/SHAP-Explainable%20AI-purple)](https://shap.readthedocs.io/)

---

## 📌 Project Overview

An end-to-end ride-sharing analytics and machine learning project focused on:

- 🚗 Ride demand and operational performance
- 💰 Revenue and pricing analysis
- 👥 Customer behavior and retention
- ❌ Cancellation analysis
- 🤖 Cancellation-risk prediction
- 🔎 Explainable AI using SHAP
- 📊 Business intelligence dashboards

The project combines **MySQL, Python, Statistics, Machine Learning, SHAP, Power BI, and Streamlit** to transform ride-sharing data into actionable business insights.

> **Dataset:** Synthetic data created for portfolio and educational purposes. This project is not affiliated with Uber, Ola, Lyft, Rapido, or any other ride-sharing company.

---

## 🔗 Project Navigation

| Component | Description |
|---|---|
| 🗄️ [SQL](sql/) | Database design and business analysis |
| 🐍 [Python](python/) | Data cleaning, EDA, statistics and ML |
| 🤖 [Models](models/) | Trained model and preprocessing artifacts |
| 🔎 [ML Visualizations](images/ml/) | Model evaluation and SHAP results |
| 📊 [Dashboard](dashboard/) | Business dashboard previews |
| 📈 [Power BI](powerbi/) | Power BI project and dashboard documentation |
| 🚀 [Streamlit App](app/) | Interactive analytics and prediction application |
| 📄 [Reports](reports/) | Project documentation and reports |

---

# 🎯 Business Problem
Ride-sharing platforms need to balance **customer demand, driver availability, revenue, cancellations, customer satisfaction, and operational efficiency**.

This project analyzes ride-sharing operations and customer behavior to identify patterns that can support better business decisions.

## Key Business Questions

- 🚗 When is ride demand highest?
- 📍 Which cities and routes generate the most demand?
- 💰 Which cities, routes, drivers, and vehicle types generate the most revenue?
- ❌ What factors are associated with ride cancellations?
- 📈 How does surge pricing relate to cancellation behavior?
- 👨‍✈️ Which drivers demonstrate the strongest performance?
- 👥 Which customers are most valuable?
- 🔄 What is the repeat customer and retention rate?
- 🤖 Can cancellation risk be predicted before a trip?
- 🔎 Which features contribute most to cancellation risk?

## 🎯 Project Objectives

### 📊 Operations Analytics
- Analyze ride demand by hour, day, and city
- Identify peak booking periods
- Analyze pickup and drop locations
- Evaluate driver and vehicle performance

### 💰 Revenue Analytics
- Calculate total and average revenue
- Analyze revenue by city, driver, vehicle, and route
- Calculate average fare and fare per kilometer

### 👥 Customer Analytics
- Analyze active and returning riders
- Measure customer retention
- Perform RFM-style customer segmentation
- Identify valuable and at-risk customers

### ❌ Cancellation Analytics
- Calculate cancellation rate
- Analyze cancellation reasons
- Identify cancellation patterns
- Investigate the relationship between surge pricing and cancellations

### 🤖 Predictive Analytics
- Build cancellation prediction models
- Compare classification algorithms
- Evaluate model performance
- Explain predictions using SHAP

---

# 🏆 Key Results

## 📊 Statistical Findings

| Analysis                      |                    Result |
| ------------------------------ | -------------------------: |
| High-surge cancellation rate  |                 **29.7%** |
| Lower-surge cancellation rate |                 **17.5%** |
| Distance vs Fare              |             **r = 0.585** |
| Duration vs Fare              |             **r = 0.563** |
| Driver Rating vs Cancellation | **r = -0.076, p < 0.001** |
| Fare Regression               |            **R² = 0.391** |

### Business Interpretation

The analysis suggests that cancellation behavior is associated with factors such as:

* Surge pricing
* Peak-hour demand
* Driver historical cancellation behavior
* Driver ratings
* Trip characteristics

These relationships are further investigated using machine learning and SHAP.

---

# 🤖 Machine Learning

## Prediction Objective

Predict whether a requested ride will be cancelled.

```text
0 → Completed
1 → Cancelled
```

### Models Evaluated

1. Logistic Regression
2. Random Forest
3. XGBoost

---

## 📏 Model Performance

The current evaluation uses a **time-based test split**.

| Model                |  Accuracy | Precision |    Recall |  F1-Score |   ROC-AUC |
| --------------------- | --------: | --------: | --------: | --------: | --------: |
| 🥇 **Random Forest** | **80.4%** | **47.6%** | **23.7%** | **31.6%** | **0.677** |
| Logistic Regression  |     77.4% |     35.0% |     21.5% |     26.6% |     0.616 |

*(XGBoost joins this table automatically once trained — its macOS wheel needs `brew install libomp`, which wasn't installed in the environment this run came from.)*

### Best Current Model

**Random Forest** provides the strongest F1-score and ROC-AUC in the current evaluated run.

> The results are reported from the actual model evaluation. No fabricated performance metrics are used.

---

# ⚠️ Data Leakage Prevention

A major focus of the project is preventing information from the future from entering the prediction model.

The following outcome/post-trip fields are excluded:

```text
trip_status
cancellation_reason
post-trip ratings
future rider behavior
future driver behavior
```

Historical rider and driver features are calculated using information available **before the current trip**.

The evaluation uses a **chronological train/test split** to better represent a real-world prediction scenario.

---

# 🔎 Explainable AI — SHAP

SHAP is used to understand which features influence cancellation predictions.

## Top Predictive Features

| Rank | Feature                    |
| ---: | --------------------------- |
|    1 | `surge_multiplier`         |
|    2 | `distance_km`              |
|    3 | `driver_avg_rating`        |
|    4 | `driver_prior_cancel_rate` |
|    5 | `is_peak_hour`             |
|    6 | `driver_experience_days`   |
|    7 | `request_hour`             |

### Explainability Workflow

```text
Machine Learning Model
        ↓
    SHAP Explainer
        ↓
Feature Contributions
        ↓
Prediction Explanation
        ↓
Business Interpretation
```

This makes the model more useful for operations teams because predictions can be connected to understandable business factors.

---

# 🚦 Cancellation Risk

Predicted probabilities can be converted into operational risk categories:

| Cancellation Probability | Risk      |
| ------------------------: | --------- |
|                  `< 30%` | 🟢 Low    |
|              `30% – 60%` | 🟡 Medium |
|                  `> 60%` | 🔴 High   |

> These thresholds are configurable and should be calibrated using real business costs before production deployment.

---

# 💰 Revenue Analytics

The project analyzes:

* Total revenue
* Revenue by city
* Revenue by driver
* Revenue by vehicle type
* Revenue by route
* Average fare
* Fare per kilometer
* Monthly revenue
* Month-over-month growth

---

# 🚗 Operations Analytics

Key operational metrics include:

* Total trips
* Completed trips
* Cancelled trips
* Cancellation rate
* Trips by hour
* Trips by day
* Peak booking periods
* City-level demand
* Pickup locations
* Drop locations
* Driver performance
* Vehicle performance
* Payment methods

---

# 👥 Customer Analytics

Customer behavior is analyzed using:

### Customer KPIs

* Active Riders
* New Riders
* Returning Riders
* Repeat Customer Rate
* Monthly Retention
* Trip Frequency
* Customer Monetary Value
* Historical Customer Value

---

## 📌 RFM Segmentation

Customers are analyzed using:

```text
Recency
   +
Frequency
   +
Monetary Value
   ↓
Customer Segment
```

### Segments

```text
⭐ VIP Customers
💎 Loyal Customers
👤 Regular Customers
🆕 New Customers
⚠️ At-Risk Customers
```

This can support targeted retention and customer engagement strategies.

---

# 📊 Power BI Dashboard

The project is designed around four business-focused dashboard pages.

## 1️⃣ Executive Overview

### KPIs

* Total Trips
* Total Revenue
* Completed Trips
* Cancellation Rate
* Active Riders
* Active Drivers
* Average Fare
* Average Rating

### Visuals

* Revenue trend
* Trip trend
* City performance
* Vehicle performance

---

## 2️⃣ Demand & Operations

### Visuals

* Hourly demand
* Daily demand
* Peak periods
* Demand heatmap
* City demand
* Pickup locations
* Drop locations
* Cancellation reasons

---

## 3️⃣ Driver Performance

### Analysis

* Driver ranking
* Revenue per driver
* Trips per driver
* Driver cancellation rate
* Vehicle performance
* Driver performance matrix

---

## 4️⃣ Customer & Cancellation Risk

### Analysis

* Active riders
* New vs returning riders
* RFM segmentation
* Retention
* Customer value
* Cancellation probability
* High-risk trips

> Power BI Desktop is Windows-only and wasn't available to produce or
> verify a real `.pbix` in the environment this project was built in. The
> repository includes a hand-authored Power BI Project
> (`powerbi/RideSharingAnalytics.pbip` — TMDL semantic model + a report
> shell) plus the full DAX/build guide in [`powerbi/README.md`](powerbi/README.md)
> for building the genuine dashboard in Power BI Desktop.

---

# 🖥️ Dashboard Preview

Since a verified `.pbix` export isn't possible here, the four images below
are matplotlib-composed previews built from the **actual pipeline data**
(`data/processed/*.csv`) rather than real Power BI screenshots — the
numbers are genuine, the rendering engine isn't Power BI. They already
live in this repo:

```text
dashboard/
├── 01_executive_overview.png
├── 02_demand_operations.png
├── 03_driver_performance.png
├── 04_customer_cancellation_risk.png
└── generate_previews.py   ← regenerates all 4 from current data
```

![Executive Overview](dashboard/01_executive_overview.png)

![Demand & Operations](dashboard/02_demand_operations.png)

![Driver Performance](dashboard/03_driver_performance.png)

![Customer & Cancellation Risk](dashboard/04_customer_cancellation_risk.png)

> **If you build the real dashboard in Power BI Desktop:** export your own
> screenshots over these four files (same filenames) so this section shows
> the genuine report instead of the preview.

---

# 🚀 Streamlit Application

The repository includes a Streamlit application for interactive exploration.

### Features

* 📊 Executive analytics
* 🚗 Demand analysis
* 👨‍✈️ Driver performance
* 👥 Customer analytics
* ❌ Cancellation-risk prediction
* 🔎 SHAP explanations

### Run Locally

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

### 🌐 Public Demo

**Coming soon**

> Replace this section with the actual Streamlit URL after deployment. Do not label a localhost application as a live demo.

---

# 🗄️ Data Model

The project uses a relational structure containing:

```text
Riders
Drivers
Vehicles
Locations
Trips
Payments
Ratings
```

### Relationships

```text
Riders       1 ─────── * Trips
Drivers      1 ─────── * Trips
Drivers      1 ─────── 1 Vehicles
Locations    1 ─────── * Trips
Trips        1 ─────── * Payments
Trips        1 ─────── * Ratings
```

---

# 🧠 SQL Analysis

The SQL layer demonstrates real-world analytical SQL.

### SQL Concepts

```text
SELECT
JOINs
GROUP BY
HAVING
CASE WHEN
Subqueries
CTEs
Window Functions
RANK()
DENSE_RANK()
ROW_NUMBER()
LAG()
NTILE()
Date Functions
Views
Indexes
Aggregate Functions
```

### SQL Modules

| File                           | Purpose                  |
| --------------------------------- | -------------------------- |
| `01_create_database.sql`       | Create database          |
| `02_create_tables.sql`         | Create relational schema |
| `03_load_data.sql`             | Load data                |
| `04_basic_analysis.sql`        | Basic analysis           |
| `05_advanced_analysis.sql`     | Advanced SQL              |
| `06_business_kpis.sql`         | Business KPIs            |
| `07_customer_retention.sql`    | Retention analysis       |
| `08_customer_segmentation.sql` | RFM segmentation         |

---

# 🐍 Python & EDA

Python is used for:

### Data Cleaning

* Missing-value analysis
* Duplicate detection
* Data validation
* Data-type validation
* Outlier analysis

### Exploratory Data Analysis

* Demand trends
* Revenue distribution
* Cancellation behavior
* Customer behavior
* Driver performance
* Vehicle performance
* City performance
* Pricing patterns

### Libraries

```text
Pandas
NumPy
Matplotlib
Seaborn
Plotly
```

---

# 📈 Statistical Analysis

Statistical techniques include:

* Chi-Square Test
* Welch's T-Test
* Pearson Correlation
* Regression Analysis
* Confidence Intervals
* Effect Size

### Example Hypothesis

**H₀:** Surge pricing has no association with cancellation behavior.

**H₁:** Surge pricing is associated with cancellation behavior.

Statistical significance:

```text
α = 0.05
```

---

# 🏗️ End-to-End Architecture

```text
                    RAW DATA
                       │
                       ▼
              ┌─────────────────┐
              │      MySQL      │
              │ Relational Data │
              └────────┬────────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       SQL Analytics        Python / Pandas
             │                   │
             │                   ▼
             │                  EDA
             │                   │
             │                   ▼
             │           Statistical Tests
             │                   │
             └─────────┬─────────┘
                       ▼
              Feature Engineering
                       │
                       ▼
              Machine Learning
                       │
              ┌────────┴────────┐
              ▼                 ▼
        Random Forest        XGBoost
              │                 │
              └────────┬────────┘
                       ▼
                     SHAP
                       │
                       ▼
              Cancellation Risk
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          Power BI           Streamlit
             │                   │
             └─────────┬─────────┘
                       ▼
                BUSINESS INSIGHTS
```

---

# 📁 Repository Structure

```text
Ride-Sharing-Analytics-Cancellation-Prediction/
│
├── 📁 app/
│   ├── streamlit_app.py
│   └── README.md
│
├── 📁 dashboard/
│   ├── 01_executive_overview.png
│   ├── 02_demand_operations.png
│   ├── 03_driver_performance.png
│   ├── 04_customer_cancellation_risk.png
│   └── generate_previews.py
│
├── 📁 data/
│   ├── raw/
│   └── processed/
│
├── 📁 images/
│   ├── eda/
│   └── ml/
│
├── 📁 models/
│
├── 📁 powerbi/
│   ├── RideSharingAnalytics.pbip
│   ├── RideSharingAnalytics.SemanticModel/
│   ├── RideSharingAnalytics.Report/
│   └── README.md
│
├── 📁 python/
│   ├── 01_data_generation.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda.ipynb
│   ├── 04_statistical_analysis.ipynb
│   ├── 05_feature_engineering.ipynb
│   ├── 06_cancellation_prediction.ipynb
│   └── 07_model_explainability.ipynb
│
├── 📁 reports/
│
├── 📁 sql/
│   ├── 01_create_database.sql
│   ├── 02_create_tables.sql
│   ├── 03_load_data.sql
│   ├── 04_basic_analysis.sql
│   ├── 05_advanced_analysis.sql
│   ├── 06_business_kpis.sql
│   ├── 07_customer_retention.sql
│   └── 08_customer_segmentation.sql
│
├── 📄 .gitignore
├── 📄 CONTRIBUTING.md
├── 📄 LICENSE
├── 📄 README.md
└── 📄 requirements.txt
```

---

# 🚀 Installation

## 1. Clone Repository

```bash
git clone https://github.com/Beingnav/Ride-Sharing-Analytics-Cancellation-Prediction.git
```

```bash
cd Ride-Sharing-Analytics-Cancellation-Prediction
```

---

## 2. Create Virtual Environment

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🗄️ MySQL Setup

Execute the SQL files in this order:

```text
01_create_database.sql
        ↓
02_create_tables.sql
        ↓
03_load_data.sql
        ↓
04_basic_analysis.sql
        ↓
05_advanced_analysis.sql
        ↓
06_business_kpis.sql
        ↓
07_customer_retention.sql
        ↓
08_customer_segmentation.sql
```

---

# 🐍 Python Workflow

Run the notebooks sequentially:

```text
01_data_generation.ipynb
        ↓
02_data_cleaning.ipynb
        ↓
03_eda.ipynb
        ↓
04_statistical_analysis.ipynb
        ↓
05_feature_engineering.ipynb
        ↓
06_cancellation_prediction.ipynb
        ↓
07_model_explainability.ipynb
```

---

# 📊 Core KPIs

```text
Total Trips
Completed Trips
Cancelled Trips
Cancellation Rate
Total Revenue
Average Fare
Average Distance
Average Duration
Fare per Kilometer
Active Riders
Active Drivers
Trips per Rider
Trips per Driver
Revenue per Driver
Revenue by City
Revenue by Vehicle Type
Revenue by Route
Peak Booking Hour
Peak Booking Day
Repeat Customer Rate
Retention Rate
Customer Value
High-Risk Trips
```

---

# 💡 Business Recommendations

The analysis framework can support:

### 🚗 Demand Optimization

Improve driver allocation during high-demand periods and locations.

### ❌ Cancellation Reduction

Identify high-risk bookings and investigate pricing, driver availability, pickup time, and demand conditions.

### 💰 Revenue Optimization

Focus on high-performing cities, routes, vehicle types, and customer segments.

### 👨‍✈️ Driver Operations

Monitor driver utilization, ratings, performance, and historical cancellation behavior.

### 👥 Customer Retention

Use RFM segmentation to create targeted retention strategies.

---

# ⚠️ Limitations

This project uses synthetic data.

Therefore:

* Results should not be interpreted as actual industry statistics.
* Model performance depends on the synthetic data-generating process.
* Production deployment requires real operational data.
* Risk thresholds require calibration using actual business costs.
* Production models require monitoring for data drift and concept drift.

---

# 🔮 Future Scope

* Demand forecasting
* Customer churn prediction
* Driver supply forecasting
* Geospatial analytics
* Dynamic pricing optimization
* Real-time cancellation prediction
* FastAPI deployment
* Streamlit Cloud deployment
* Cloud database integration
* Automated model retraining
* Model monitoring
* Real-time analytics

---

# 🧠 Skills Demonstrated

### Data Analytics

* Data Cleaning
* Exploratory Data Analysis
* KPI Development
* Business Analysis
* Data Visualization

### SQL

* Joins
* Aggregations
* CTEs
* Subqueries
* Window Functions
* Ranking
* Views
* Indexes
* Date Functions

### Python

* Pandas
* NumPy
* Matplotlib
* Seaborn
* Plotly

### Statistics

* Hypothesis Testing
* Chi-Square
* T-Test
* Correlation
* Regression
* Confidence Intervals
* Effect Size

### Machine Learning

* Classification
* Logistic Regression
* Random Forest
* XGBoost
* Feature Engineering
* Model Evaluation
* Time-Based Validation
* Data Leakage Prevention

### Explainable AI

* SHAP
* Feature Importance
* Prediction Explanation

### Business Intelligence

* Power BI
* DAX
* Data Modeling
* Interactive Dashboards
* KPI Design

---

# 📌 Project Status

| Component            | Status                                            |
| --------------------- | -------------------------------------------------- |
| MySQL Database       | ✅ Complete                                        |
| SQL Analysis         | ✅ Complete                                        |
| Python EDA           | ✅ Complete                                        |
| Statistical Analysis | ✅ Complete                                        |
| Feature Engineering  | ✅ Complete                                        |
| ML Pipeline          | ✅ Complete                                        |
| SHAP Analysis        | ✅ Complete                                        |
| Power BI             | 🟡 `.pbip` + preview mockups ready; verified `.pbix` pending (Windows-only tool) |
| Streamlit App        | 🟡 Local application ready                        |
| Public Demo          | 🔴 Not deployed                                   |

---

# 🔮 Next Development Milestones

```text
[✓] SQL Analytics
[✓] Python EDA
[✓] Statistical Analysis
[✓] Feature Engineering
[✓] Machine Learning
[✓] SHAP Explainability
[✓] Dashboard Preview Screenshots
[ ] Verified Power BI .pbix (requires Windows + Power BI Desktop)
[ ] Streamlit Deployment
[ ] Public Demo
[ ] Final Case Study
```

---

# 👨‍💻 Author

## Navdeep Taliyan

**Aspiring Data Analyst | Data Science Enthusiast**

### Core Skills

**SQL · Python · Power BI · Excel · Statistics · Machine Learning · Data Visualization**

### GitHub

https://github.com/Beingnav

### LinkedIn

https://www.linkedin.com/in/navdeep-taliyan-7270a824/

---

# ⭐ Support

If you find this project useful, consider giving the repository a ⭐.

---

## 📄 License

This project is licensed under the **MIT License**.
