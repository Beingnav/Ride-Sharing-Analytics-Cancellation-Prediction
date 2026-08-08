-- =====================================================================
-- 04_basic_analysis.sql
-- Ride-Sharing Analytics & Cancellation Prediction
-- Foundational SQL: data quality checks + first-pass business analysis.
-- =====================================================================

USE ride_sharing_analytics;

-- ---------------------------------------------------------------------
-- DATA QUALITY CHECKS
-- ---------------------------------------------------------------------

-- Missing values on key columns
SELECT
    SUM(fare_amount IS NULL)      AS missing_fare,
    SUM(duration_min IS NULL)     AS missing_duration,
    SUM(pickup_datetime IS NULL)  AS missing_pickup_dt,
    SUM(drop_datetime IS NULL)    AS missing_drop_dt
FROM trips;

-- Duplicate trip_ids (should be zero — trip_id is PK, this checks source data before load)
SELECT trip_id, COUNT(*) AS occurrences
FROM trips
GROUP BY trip_id
HAVING COUNT(*) > 1;

-- Referential integrity: trips pointing at riders/drivers/vehicles that don't exist
SELECT t.trip_id
FROM trips t
LEFT JOIN riders r ON r.rider_id = t.rider_id
WHERE r.rider_id IS NULL;

-- Invalid values: fare should never be negative, distance should be > 0 for completed trips
SELECT trip_id, distance_km, fare_amount
FROM trips
WHERE trip_status = 'Completed' AND (distance_km <= 0 OR fare_amount <= 0);

-- Outlier detection: trips with distance more than 3 standard deviations from the mean
SELECT trip_id, distance_km
FROM trips t
CROSS JOIN (
    SELECT AVG(distance_km) AS mean_dist, STDDEV(distance_km) AS sd_dist
    FROM trips WHERE trip_status = 'Completed'
) stats
WHERE t.trip_status = 'Completed'
  AND ABS(t.distance_km - stats.mean_dist) > 3 * stats.sd_dist;

-- ---------------------------------------------------------------------
-- BASIC BUSINESS ANALYSIS
-- ---------------------------------------------------------------------

-- Total trips and status breakdown
SELECT trip_status, COUNT(*) AS trips, ROUND(100 * COUNT(*) / (SELECT COUNT(*) FROM trips), 2) AS pct
FROM trips
GROUP BY trip_status
ORDER BY trips DESC;

-- Trips by hour of day
SELECT HOUR(request_datetime) AS hour_of_day, COUNT(*) AS trips
FROM trips
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- Trips by day of week
SELECT DAYNAME(request_datetime) AS day_of_week, COUNT(*) AS trips
FROM trips
GROUP BY day_of_week, DAYOFWEEK(request_datetime)
ORDER BY DAYOFWEEK(request_datetime);

-- Trips and revenue by city (pickup city)
SELECT
    l.city,
    COUNT(*) AS total_trips,
    ROUND(SUM(CASE WHEN t.trip_status = 'Completed' THEN t.fare_amount ELSE 0 END), 2) AS total_revenue
FROM trips t
JOIN locations l ON l.location_id = t.pickup_location_id
GROUP BY l.city
ORDER BY total_revenue DESC;

-- Average fare, distance, duration for completed trips
SELECT
    ROUND(AVG(fare_amount), 2)   AS avg_fare,
    ROUND(AVG(distance_km), 2)   AS avg_distance_km,
    ROUND(AVG(duration_min), 2)  AS avg_duration_min,
    ROUND(AVG(fare_amount / NULLIF(distance_km, 0)), 2) AS avg_fare_per_km
FROM trips
WHERE trip_status = 'Completed';

-- Revenue by vehicle type
SELECT
    v.vehicle_type,
    COUNT(*) AS completed_trips,
    ROUND(SUM(t.fare_amount), 2) AS total_revenue,
    ROUND(AVG(t.fare_amount), 2) AS avg_fare
FROM trips t
JOIN vehicles v ON v.vehicle_id = t.vehicle_id
WHERE t.trip_status = 'Completed'
GROUP BY v.vehicle_type
ORDER BY total_revenue DESC;
