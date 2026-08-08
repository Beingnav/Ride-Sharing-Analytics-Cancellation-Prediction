-- =====================================================================
-- 05_advanced_analysis.sql
-- Ride-Sharing Analytics & Cancellation Prediction
-- Advanced SQL: window functions, CTEs, ranking, route + driver analysis.
-- =====================================================================

USE ride_sharing_analytics;

-- ---------------------------------------------------------------------
-- Top 10 highest-revenue routes (pickup city -> drop city)
-- ---------------------------------------------------------------------
WITH route_revenue AS (
    SELECT
        pl.city AS pickup_city,
        dl.city AS drop_city,
        COUNT(*) AS trips,
        SUM(t.fare_amount) AS total_revenue
    FROM trips t
    JOIN locations pl ON pl.location_id = t.pickup_location_id
    JOIN locations dl ON dl.location_id = t.drop_location_id
    WHERE t.trip_status = 'Completed'
    GROUP BY pl.city, dl.city
)
SELECT *, RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank
FROM route_revenue
ORDER BY total_revenue DESC
LIMIT 10;

-- ---------------------------------------------------------------------
-- Driver ranking by revenue within each city (window function)
-- ---------------------------------------------------------------------
SELECT
    d.city,
    d.driver_id,
    d.first_name,
    d.last_name,
    SUM(t.fare_amount) AS driver_revenue,
    RANK() OVER (PARTITION BY d.city ORDER BY SUM(t.fare_amount) DESC) AS city_rank
FROM drivers d
JOIN trips t ON t.driver_id = d.driver_id AND t.trip_status = 'Completed'
GROUP BY d.city, d.driver_id, d.first_name, d.last_name;

-- ---------------------------------------------------------------------
-- Month-over-month revenue growth (window function: LAG)
-- ---------------------------------------------------------------------
WITH monthly_revenue AS (
    SELECT
        DATE_FORMAT(request_datetime, '%Y-%m-01') AS month_start,
        SUM(fare_amount) AS revenue
    FROM trips
    WHERE trip_status = 'Completed'
    GROUP BY month_start
)
SELECT
    month_start,
    revenue,
    LAG(revenue) OVER (ORDER BY month_start) AS prev_month_revenue,
    ROUND(
        100 * (revenue - LAG(revenue) OVER (ORDER BY month_start))
        / NULLIF(LAG(revenue) OVER (ORDER BY month_start), 0), 2
    ) AS mom_growth_pct
FROM monthly_revenue
ORDER BY month_start;

-- ---------------------------------------------------------------------
-- Running total of daily revenue (window function: SUM OVER)
-- ---------------------------------------------------------------------
WITH daily_revenue AS (
    SELECT DATE(request_datetime) AS trip_date, SUM(fare_amount) AS revenue
    FROM trips
    WHERE trip_status = 'Completed'
    GROUP BY trip_date
)
SELECT
    trip_date,
    revenue,
    SUM(revenue) OVER (ORDER BY trip_date) AS running_total_revenue,
    ROUND(AVG(revenue) OVER (ORDER BY trip_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS revenue_7day_avg
FROM daily_revenue
ORDER BY trip_date;

-- ---------------------------------------------------------------------
-- Rider trip sequence + time-since-previous-trip (window function: LAG)
-- Used to sanity-check the "days since last trip" feature built in Python.
-- ---------------------------------------------------------------------
SELECT
    rider_id,
    trip_id,
    request_datetime,
    ROW_NUMBER() OVER (PARTITION BY rider_id ORDER BY request_datetime) AS trip_sequence,
    DATEDIFF(
        request_datetime,
        LAG(request_datetime) OVER (PARTITION BY rider_id ORDER BY request_datetime)
    ) AS days_since_prev_trip
FROM trips
ORDER BY rider_id, request_datetime;

-- ---------------------------------------------------------------------
-- Cancellation rate by pickup city, ranked worst-first
-- ---------------------------------------------------------------------
SELECT
    pl.city,
    COUNT(*) AS total_trips,
    SUM(CASE WHEN t.trip_status LIKE 'Cancelled%' THEN 1 ELSE 0 END) AS cancelled_trips,
    ROUND(100 * SUM(CASE WHEN t.trip_status LIKE 'Cancelled%' THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancellation_rate_pct,
    RANK() OVER (ORDER BY SUM(CASE WHEN t.trip_status LIKE 'Cancelled%' THEN 1 ELSE 0 END) / COUNT(*) DESC) AS risk_rank
FROM trips t
JOIN locations pl ON pl.location_id = t.pickup_location_id
GROUP BY pl.city;

-- ---------------------------------------------------------------------
-- Top 5 most active riders per city (window function: ROW_NUMBER)
-- ---------------------------------------------------------------------
WITH rider_trip_counts AS (
    SELECT
        r.city,
        r.rider_id,
        COUNT(*) AS trip_count,
        ROW_NUMBER() OVER (PARTITION BY r.city ORDER BY COUNT(*) DESC) AS rn
    FROM riders r
    JOIN trips t ON t.rider_id = r.rider_id
    GROUP BY r.city, r.rider_id
)
SELECT city, rider_id, trip_count
FROM rider_trip_counts
WHERE rn <= 5
ORDER BY city, trip_count DESC;
