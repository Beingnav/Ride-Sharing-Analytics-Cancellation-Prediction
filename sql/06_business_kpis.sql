-- =====================================================================
-- 06_business_kpis.sql
-- Ride-Sharing Analytics & Cancellation Prediction
-- Single source-of-truth KPI queries — mirrors the KPI list in README.md
-- and the Power BI DAX measures.
-- =====================================================================

USE ride_sharing_analytics;

-- One-row executive KPI summary
SELECT
    COUNT(*)                                                                 AS total_trips,
    SUM(CASE WHEN trip_status = 'Completed' THEN 1 ELSE 0 END)               AS completed_trips,
    SUM(CASE WHEN trip_status LIKE 'Cancelled%' THEN 1 ELSE 0 END)           AS cancelled_trips,
    ROUND(100 * SUM(CASE WHEN trip_status LIKE 'Cancelled%' THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancellation_rate_pct,
    ROUND(SUM(CASE WHEN trip_status = 'Completed' THEN fare_amount ELSE 0 END), 2)            AS total_revenue,
    ROUND(AVG(CASE WHEN trip_status = 'Completed' THEN fare_amount END), 2)                   AS avg_fare,
    ROUND(AVG(CASE WHEN trip_status = 'Completed' THEN distance_km END), 2)                   AS avg_distance_km,
    ROUND(AVG(CASE WHEN trip_status = 'Completed' THEN duration_min END), 2)                  AS avg_duration_min,
    ROUND(AVG(CASE WHEN trip_status = 'Completed' THEN fare_amount / NULLIF(distance_km, 0) END), 2) AS fare_per_km,
    COUNT(DISTINCT rider_id)                                                 AS active_riders,
    COUNT(DISTINCT driver_id)                                                AS active_drivers,
    ROUND(COUNT(*) / COUNT(DISTINCT rider_id), 2)                            AS trips_per_rider,
    ROUND(COUNT(*) / COUNT(DISTINCT driver_id), 2)                           AS trips_per_driver
FROM trips;

-- Revenue per driver
SELECT
    driver_id,
    ROUND(SUM(fare_amount), 2) AS revenue_per_driver,
    COUNT(*) AS completed_trips
FROM trips
WHERE trip_status = 'Completed'
GROUP BY driver_id
ORDER BY revenue_per_driver DESC;

-- Revenue by city / vehicle / route (see also 04, 05)
SELECT l.city, ROUND(SUM(t.fare_amount), 2) AS revenue_by_city
FROM trips t JOIN locations l ON l.location_id = t.pickup_location_id
WHERE t.trip_status = 'Completed'
GROUP BY l.city ORDER BY revenue_by_city DESC;

-- Peak booking hour and peak booking day
SELECT HOUR(request_datetime) AS peak_hour, COUNT(*) AS trips
FROM trips GROUP BY peak_hour ORDER BY trips DESC LIMIT 1;

SELECT DAYNAME(request_datetime) AS peak_day, COUNT(*) AS trips
FROM trips GROUP BY peak_day, DAYOFWEEK(request_datetime)
ORDER BY trips DESC LIMIT 1;

-- Repeat customer rate: % of riders with more than 1 completed trip
SELECT
    ROUND(100 * SUM(CASE WHEN completed_trips > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_customer_rate_pct
FROM (
    SELECT rider_id, SUM(CASE WHEN trip_status = 'Completed' THEN 1 ELSE 0 END) AS completed_trips
    FROM trips
    GROUP BY rider_id
) rider_summary;

-- High-risk cancellation trips: cancelled trips under surge pricing (proxy KPI
-- for "high-risk cancellation trips" ahead of the ML risk score in Power BI)
SELECT COUNT(*) AS high_risk_cancelled_trips
FROM trips
WHERE trip_status LIKE 'Cancelled%' AND surge_multiplier > 1.5;
