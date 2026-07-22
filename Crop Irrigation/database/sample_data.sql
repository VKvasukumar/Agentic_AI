-- Seed data for AI-Based Crop Irrigation System
-- For SQLite database

-- Clear existing data (optional, but good for reset)
DELETE FROM irrigation_history;
DELETE FROM predictions;
DELETE FROM weather_readings;
DELETE FROM soil_readings;
DELETE FROM farms;
DELETE FROM users;

-- Insert a test user
-- Password is 'password123', hashed using pbkdf2:sha256:600000
INSERT INTO users (id, username, email, password_hash)
VALUES (1, 'farmer_john', 'john@farm.com', 'pbkdf2:sha256:600000$sYvL7U1v03nO8m7H$66782dbf2d2426305a46cfefcc93740263f350325d3fa7bfb3dfd3c5bf4f48b1');

-- Insert a farm
INSERT INTO farms (id, user_id, farm_name, location, crop_type, farm_size)
VALUES (1, 1, 'Green Valley Organic Fields', 'California Valley, CA', 'Tomato', 15.5);

-- Insert soil readings for the past 24 hours (simulating decline, then irrigation, then decline)
-- Timestamp is format YYYY-MM-DD HH:MM:SS
-- We will write timestamps relative to current time in Python, but here we provide standard static ones
INSERT INTO soil_readings (farm_id, moisture, temperature, ph, nitrogen, phosphorus, potassium, recorded_at) VALUES
(1, 48.2, 24.1, 6.2, 85.0, 42.0, 145.0, datetime('now', '-24 hours')),
(1, 46.5, 24.8, 6.2, 85.0, 42.0, 145.0, datetime('now', '-22 hours')),
(1, 44.1, 25.5, 6.2, 84.0, 41.0, 144.0, datetime('now', '-20 hours')),
(1, 41.8, 26.2, 6.2, 84.0, 41.0, 144.0, datetime('now', '-18 hours')),
(1, 38.9, 27.0, 6.3, 83.0, 41.0, 143.0, datetime('now', '-16 hours')),
(1, 35.2, 27.5, 6.3, 83.0, 40.0, 143.0, datetime('now', '-14 hours')),
(1, 32.1, 28.1, 6.3, 82.0, 40.0, 142.0, datetime('now', '-12 hours')), -- Critical threshold reached
(1, 78.5, 23.5, 6.3, 82.0, 40.0, 142.0, datetime('now', '-11 hours')), -- Just after irrigation
(1, 75.2, 23.8, 6.3, 81.0, 39.0, 141.0, datetime('now', '-9 hours')),
(1, 71.8, 24.2, 6.3, 81.0, 39.0, 141.0, datetime('now', '-7 hours')),
(1, 68.4, 24.9, 6.3, 80.0, 39.0, 140.0, datetime('now', '-5 hours')),
(1, 64.9, 25.4, 6.3, 80.0, 39.0, 140.0, datetime('now', '-3 hours')),
(1, 61.2, 25.8, 6.3, 80.0, 39.0, 140.0, datetime('now', '-1 hours'));

-- Insert weather readings for the past 24 hours
INSERT INTO weather_readings (farm_id, temperature, humidity, rainfall, forecast, recorded_at) VALUES
(1, 26.5, 55.0, 0.0, 'sunny', datetime('now', '-24 hours')),
(1, 27.8, 52.0, 0.0, 'sunny', datetime('now', '-20 hours')),
(1, 29.1, 48.0, 0.0, 'sunny', datetime('now', '-16 hours')),
(1, 29.5, 45.0, 0.0, 'sunny', datetime('now', '-12 hours')),
(1, 24.2, 65.0, 0.0, 'cloudy', datetime('now', '-8 hours')),
(1, 23.0, 70.0, 0.0, 'cloudy', datetime('now', '-4 hours')),
(1, 25.5, 60.0, 0.0, 'sunny', datetime('now', '-1 hours'));

-- Insert past predictions
INSERT INTO predictions (farm_id, prediction_type, inputs, results, confidence, created_at) VALUES
(1, 'irrigation', '{"moisture": 32.1, "temperature": 28.1, "forecast": "sunny", "crop_type": "Tomato"}', '{"status": "Irrigation Recommended", "water_volume_liters": 1500, "duration_minutes": 30, "reason": "Soil moisture drop below 35% with sunny outlook"}', 94.5, datetime('now', '-12 hours')),
(1, 'disease', '{"crop": "Tomato", "image_name": "tomato_leaf_blight.jpg"}', '{"crop": "Tomato", "health_status": "Diseased", "disease": "Late Blight", "confidence": 88.2, "treatment": "Apply copper fungicides immediately and remove infected leaves."}', 88.2, datetime('now', '-10 hours'));

-- Insert irrigation history
INSERT INTO irrigation_history (farm_id, action, water_volume_liters, duration_minutes, triggered_by, timestamp) VALUES
(1, 'pump_on', 1500, 30, 'AI', datetime('now', '-12 hours')),
(1, 'pump_off', 1500, 30, 'AI', datetime('now', '-11.5 hours'));
