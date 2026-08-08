-- =====================================================================
-- 07_customer_retention.sql
-- Ride-Sharing Analytics & Cancellation Prediction
-- Monthly active riders, new vs returning, and month-over-month retention.
-- =====================================================================

USE ride_sharing_analytics;

-- ---------------------------------------------------------------------
-- Monthly active riders + new riders (first-ever completed trip that month)
-- ---------------------------------------------------------------------
WITH rider_first_trip AS (
    SELECT rider_id, MIN(DATE_FORMAT(request_datetime, '%Y-%m-01')) AS first_trip_month
    FROM trips
    WHERE trip_status = 'Completed'
    GROUP BY rider_id
),
monthly_activity AS (
    SELECT
        DATE_FORMAT(request_datetime, '%Y-%m-01') AS activity_month,
        rider_id
    FROM trips
    WHERE trip_status = 'Completed'
    GROUP BY activity_month, rider_id
)
SELECT
    ma.activity_month,
    COUNT(DISTINCT ma.rider_id) AS monthly_active_riders,
    SUM(CASE WHEN rft.first_trip_month = ma.activity_month THEN 1 ELSE 0 END) AS new_riders,
    SUM(CASE WHEN rft.first_trip_month <> ma.activity_month THEN 1 ELSE 0 END) AS returning_riders
FROM monthly_activity ma
JOIN rider_first_trip rft ON rft.rider_id = ma.rider_id
GROUP BY ma.activity_month
ORDER BY ma.activity_month;

-- ---------------------------------------------------------------------
-- Month-over-month retention: of riders active in month N, what % were
-- also active in month N+1?
-- ---------------------------------------------------------------------
WITH monthly_activity AS (
    SELECT DISTINCT
        DATE_FORMAT(request_datetime, '%Y-%m-01') AS activity_month,
        rider_id
    FROM trips
    WHERE trip_status = 'Completed'
),
cohort AS (
    SELECT
        a.activity_month AS base_month,
        a.rider_id,
        b.activity_month IS NOT NULL AS retained_next_month
    FROM monthly_activity a
    LEFT JOIN monthly_activity b
        ON b.rider_id = a.rider_id
        AND b.activity_month = DATE_ADD(a.activity_month, INTERVAL 1 MONTH)
)
SELECT
    base_month,
    COUNT(*) AS riders_in_month,
    SUM(retained_next_month) AS retained_next_month,
    ROUND(100 * SUM(retained_next_month) / COUNT(*), 2) AS retention_rate_pct
FROM cohort
GROUP BY base_month
ORDER BY base_month;

-- ---------------------------------------------------------------------
-- Historical customer value (proxy CLV): total completed-trip spend to date
-- ---------------------------------------------------------------------
SELECT
    r.rider_id,
    r.city,
    r.signup_date,
    COUNT(t.trip_id) AS completed_trips,
    ROUND(SUM(t.fare_amount), 2) AS historical_value,
    ROUND(SUM(t.fare_amount) / COUNT(t.trip_id), 2) AS avg_value_per_trip
FROM riders r
JOIN trips t ON t.rider_id = r.rider_id AND t.trip_status = 'Completed'
GROUP BY r.rider_id, r.city, r.signup_date
ORDER BY historical_value DESC;
