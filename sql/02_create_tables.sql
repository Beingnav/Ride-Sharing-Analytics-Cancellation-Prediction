-- =====================================================================
-- 02_create_tables.sql
-- Ride-Sharing Analytics & Cancellation Prediction
-- Core relational schema: Riders, Drivers, Vehicles, Locations, Trips,
-- Payments, Ratings — with PKs, FKs, validation constraints, indexes
-- and a handful of analytical views.
-- =====================================================================

USE ride_sharing_analytics;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS drivers;
DROP TABLE IF EXISTS riders;
DROP TABLE IF EXISTS locations;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- Riders
-- ---------------------------------------------------------------------
CREATE TABLE riders (
    rider_id            INT PRIMARY KEY,
    first_name          VARCHAR(50)  NOT NULL,
    last_name           VARCHAR(50)  NOT NULL,
    email               VARCHAR(100) NOT NULL UNIQUE,
    phone               VARCHAR(20)  NOT NULL,
    gender              ENUM('Male', 'Female', 'Other') NOT NULL,
    age                 TINYINT UNSIGNED NOT NULL CHECK (age BETWEEN 16 AND 90),
    city                VARCHAR(50)  NOT NULL,
    signup_date         DATE NOT NULL,
    preferred_payment   ENUM('Card', 'Cash', 'Wallet', 'UPI') NOT NULL,
    CONSTRAINT chk_riders_signup CHECK (signup_date <= CURDATE())
) ENGINE = InnoDB;

CREATE INDEX idx_riders_city        ON riders (city);
CREATE INDEX idx_riders_signup_date ON riders (signup_date);

-- ---------------------------------------------------------------------
-- Drivers
-- ---------------------------------------------------------------------
CREATE TABLE drivers (
    driver_id           INT PRIMARY KEY,
    first_name          VARCHAR(50)  NOT NULL,
    last_name           VARCHAR(50)  NOT NULL,
    email               VARCHAR(100) NOT NULL UNIQUE,
    phone               VARCHAR(20)  NOT NULL,
    gender              ENUM('Male', 'Female', 'Other') NOT NULL,
    city                VARCHAR(50)  NOT NULL,
    license_number      VARCHAR(30)  NOT NULL UNIQUE,
    signup_date         DATE NOT NULL,
    driver_status       ENUM('Active', 'Inactive', 'Suspended') NOT NULL DEFAULT 'Active',
    avg_rating          DECIMAL(3, 2) NOT NULL DEFAULT 5.00 CHECK (avg_rating BETWEEN 1.00 AND 5.00),
    CONSTRAINT chk_drivers_signup CHECK (signup_date <= CURDATE())
) ENGINE = InnoDB;

CREATE INDEX idx_drivers_city   ON drivers (city);
CREATE INDEX idx_drivers_status ON drivers (driver_status);

-- ---------------------------------------------------------------------
-- Vehicles (1-1 with Drivers)
-- ---------------------------------------------------------------------
CREATE TABLE vehicles (
    vehicle_id          INT PRIMARY KEY,
    driver_id           INT NOT NULL UNIQUE,
    vehicle_type        ENUM('Bike', 'Auto', 'Economy', 'Premium', 'XL') NOT NULL,
    make                VARCHAR(50) NOT NULL,
    model               VARCHAR(50) NOT NULL,
    year                SMALLINT NOT NULL CHECK (year BETWEEN 2005 AND 2026),
    plate_number         VARCHAR(20) NOT NULL UNIQUE,
    seating_capacity    TINYINT NOT NULL CHECK (seating_capacity BETWEEN 1 AND 8),
    CONSTRAINT fk_vehicles_driver FOREIGN KEY (driver_id)
        REFERENCES drivers (driver_id) ON DELETE CASCADE
) ENGINE = InnoDB;

CREATE INDEX idx_vehicles_type ON vehicles (vehicle_type);

-- ---------------------------------------------------------------------
-- Locations
-- ---------------------------------------------------------------------
CREATE TABLE locations (
    location_id         INT PRIMARY KEY,
    city                VARCHAR(50) NOT NULL,
    area_name           VARCHAR(100) NOT NULL,
    latitude            DECIMAL(9, 6) NOT NULL,
    longitude           DECIMAL(9, 6) NOT NULL
) ENGINE = InnoDB;

CREATE INDEX idx_locations_city ON locations (city);

-- ---------------------------------------------------------------------
-- Trips (fact table)
-- ---------------------------------------------------------------------
CREATE TABLE trips (
    trip_id              BIGINT PRIMARY KEY,
    rider_id             INT NOT NULL,
    driver_id            INT NOT NULL,
    vehicle_id           INT NOT NULL,
    pickup_location_id   INT NOT NULL,
    drop_location_id     INT NOT NULL,
    request_datetime      DATETIME NOT NULL,
    pickup_datetime       DATETIME NULL,
    drop_datetime         DATETIME NULL,
    distance_km           DECIMAL(6, 2) NOT NULL CHECK (distance_km >= 0),
    duration_min           DECIMAL(6, 2) NULL CHECK (duration_min IS NULL OR duration_min >= 0),
    base_fare             DECIMAL(8, 2) NOT NULL CHECK (base_fare >= 0),
    surge_multiplier       DECIMAL(3, 2) NOT NULL DEFAULT 1.00 CHECK (surge_multiplier >= 1.00),
    fare_amount            DECIMAL(8, 2) NULL CHECK (fare_amount IS NULL OR fare_amount >= 0),
    trip_status            ENUM('Completed', 'Cancelled_by_Rider', 'Cancelled_by_Driver', 'No_Driver_Found') NOT NULL,
    cancellation_reason     VARCHAR(100) NULL,
    payment_method          ENUM('Card', 'Cash', 'Wallet', 'UPI') NOT NULL,
    CONSTRAINT fk_trips_rider   FOREIGN KEY (rider_id)  REFERENCES riders (rider_id),
    CONSTRAINT fk_trips_driver  FOREIGN KEY (driver_id) REFERENCES drivers (driver_id),
    CONSTRAINT fk_trips_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles (vehicle_id),
    CONSTRAINT fk_trips_pickup  FOREIGN KEY (pickup_location_id) REFERENCES locations (location_id),
    CONSTRAINT fk_trips_drop    FOREIGN KEY (drop_location_id)   REFERENCES locations (location_id)
) ENGINE = InnoDB;

CREATE INDEX idx_trips_rider          ON trips (rider_id);
CREATE INDEX idx_trips_driver         ON trips (driver_id);
CREATE INDEX idx_trips_status         ON trips (trip_status);
CREATE INDEX idx_trips_request_dt     ON trips (request_datetime);
CREATE INDEX idx_trips_pickup_loc     ON trips (pickup_location_id);
CREATE INDEX idx_trips_drop_loc       ON trips (drop_location_id);

-- ---------------------------------------------------------------------
-- Payments
-- ---------------------------------------------------------------------
CREATE TABLE payments (
    payment_id           BIGINT PRIMARY KEY,
    trip_id              BIGINT NOT NULL,
    amount               DECIMAL(8, 2) NOT NULL CHECK (amount >= 0),
    payment_method        ENUM('Card', 'Cash', 'Wallet', 'UPI') NOT NULL,
    payment_status         ENUM('Success', 'Failed', 'Refunded', 'Not_Applicable') NOT NULL,
    payment_datetime       DATETIME NULL,
    CONSTRAINT fk_payments_trip FOREIGN KEY (trip_id) REFERENCES trips (trip_id) ON DELETE CASCADE
) ENGINE = InnoDB;

CREATE INDEX idx_payments_trip   ON payments (trip_id);
CREATE INDEX idx_payments_status ON payments (payment_status);

-- ---------------------------------------------------------------------
-- Ratings
-- ---------------------------------------------------------------------
CREATE TABLE ratings (
    rating_id                  BIGINT PRIMARY KEY,
    trip_id                    BIGINT NOT NULL UNIQUE,
    rider_rating_for_driver     TINYINT NULL CHECK (rider_rating_for_driver BETWEEN 1 AND 5),
    driver_rating_for_rider     TINYINT NULL CHECK (driver_rating_for_rider BETWEEN 1 AND 5),
    feedback_text                VARCHAR(255) NULL,
    CONSTRAINT fk_ratings_trip FOREIGN KEY (trip_id) REFERENCES trips (trip_id) ON DELETE CASCADE
) ENGINE = InnoDB;

-- =====================================================================
-- Analytical views
-- =====================================================================

CREATE OR REPLACE VIEW vw_trip_details AS
SELECT
    t.trip_id,
    t.rider_id,
    t.driver_id,
    t.vehicle_id,
    v.vehicle_type,
    pl.city  AS pickup_city,
    dl.city  AS drop_city,
    t.request_datetime,
    t.pickup_datetime,
    t.drop_datetime,
    t.distance_km,
    t.duration_min,
    t.base_fare,
    t.surge_multiplier,
    t.fare_amount,
    t.trip_status,
    t.cancellation_reason,
    t.payment_method,
    HOUR(t.request_datetime)      AS request_hour,
    DAYNAME(t.request_datetime)   AS request_day,
    MONTH(t.request_datetime)     AS request_month,
    CASE WHEN DAYOFWEEK(t.request_datetime) IN (1, 7) THEN 1 ELSE 0 END AS is_weekend
FROM trips t
JOIN vehicles  v  ON v.vehicle_id = t.vehicle_id
JOIN locations pl ON pl.location_id = t.pickup_location_id
JOIN locations dl ON dl.location_id = t.drop_location_id;

CREATE OR REPLACE VIEW vw_completed_trips AS
SELECT * FROM vw_trip_details WHERE trip_status = 'Completed';

CREATE OR REPLACE VIEW vw_driver_performance AS
SELECT
    d.driver_id,
    d.first_name,
    d.last_name,
    d.city,
    d.avg_rating,
    COUNT(t.trip_id)                                                       AS total_trips,
    SUM(CASE WHEN t.trip_status = 'Completed' THEN 1 ELSE 0 END)           AS completed_trips,
    SUM(CASE WHEN t.trip_status LIKE 'Cancelled%' THEN 1 ELSE 0 END)       AS cancelled_trips,
    ROUND(SUM(CASE WHEN t.trip_status = 'Completed' THEN t.fare_amount ELSE 0 END), 2) AS total_revenue
FROM drivers d
LEFT JOIN trips t ON t.driver_id = d.driver_id
GROUP BY d.driver_id, d.first_name, d.last_name, d.city, d.avg_rating;

CREATE OR REPLACE VIEW vw_rider_activity AS
SELECT
    r.rider_id,
    r.city,
    r.signup_date,
    COUNT(t.trip_id)                                                 AS total_trips,
    SUM(CASE WHEN t.trip_status = 'Completed' THEN 1 ELSE 0 END)     AS completed_trips,
    SUM(CASE WHEN t.trip_status = 'Completed' THEN t.fare_amount ELSE 0 END) AS total_spend,
    MAX(t.request_datetime)                                          AS last_trip_datetime
FROM riders r
LEFT JOIN trips t ON t.rider_id = r.rider_id
GROUP BY r.rider_id, r.city, r.signup_date;
