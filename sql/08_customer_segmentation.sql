-- =====================================================================
-- 08_customer_segmentation.sql
-- Ride-Sharing Analytics & Cancellation Prediction
-- RFM (Recency, Frequency, Monetary) segmentation into business-friendly
-- rider tiers. Mirrors the segmentation done in Python for the ML
-- pipeline (python/05_feature_engineering.ipynb) so SQL and Python agree.
-- =====================================================================

USE ride_sharing_analytics;

WITH rfm_base AS (
    SELECT
        r.rider_id,
        DATEDIFF(
            (SELECT MAX(request_datetime) FROM trips),
            MAX(t.request_datetime)
        ) AS recency_days,
        COUNT(t.trip_id) AS frequency,
        SUM(t.fare_amount) AS monetary
    FROM riders r
    JOIN trips t ON t.rider_id = r.rider_id AND t.trip_status = 'Completed'
    GROUP BY r.rider_id
),
rfm_scored AS (
    SELECT
        rider_id,
        recency_days,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,  -- more recent = higher score
        NTILE(5) OVER (ORDER BY frequency ASC)     AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)      AS m_score
    FROM rfm_base
)
SELECT
    rider_id,
    recency_days,
    frequency,
    monetary,
    r_score, f_score, m_score,
    (r_score + f_score + m_score) AS rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'VIP'
        WHEN f_score >= 4 AND m_score >= 3                  THEN 'Loyal'
        WHEN r_score <= 2 AND f_score <= 2                  THEN 'At-Risk'
        WHEN f_score <= 2 AND r_score >= 4                  THEN 'New'
        ELSE 'Regular'
    END AS customer_segment
FROM rfm_scored
ORDER BY rfm_total DESC;

-- Segment summary: size and average monetary value per segment
WITH rfm_base AS (
    SELECT
        r.rider_id,
        DATEDIFF((SELECT MAX(request_datetime) FROM trips), MAX(t.request_datetime)) AS recency_days,
        COUNT(t.trip_id) AS frequency,
        SUM(t.fare_amount) AS monetary
    FROM riders r
    JOIN trips t ON t.rider_id = r.rider_id AND t.trip_status = 'Completed'
    GROUP BY r.rider_id
),
rfm_scored AS (
    SELECT
        rider_id, recency_days, frequency, monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)     AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)      AS m_score
    FROM rfm_base
),
segmented AS (
    SELECT *,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'VIP'
            WHEN f_score >= 4 AND m_score >= 3                  THEN 'Loyal'
            WHEN r_score <= 2 AND f_score <= 2                  THEN 'At-Risk'
            WHEN f_score <= 2 AND r_score >= 4                  THEN 'New'
            ELSE 'Regular'
        END AS customer_segment
    FROM rfm_scored
)
SELECT
    customer_segment,
    COUNT(*) AS riders,
    ROUND(AVG(monetary), 2) AS avg_monetary_value,
    ROUND(AVG(frequency), 2) AS avg_trip_frequency
FROM segmented
GROUP BY customer_segment
ORDER BY avg_monetary_value DESC;
