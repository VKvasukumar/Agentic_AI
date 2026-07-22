-- AI-Based Crop Irrigation System Schema
-- For SQLite database

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS farms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    farm_name TEXT NOT NULL,
    location TEXT,
    crop_type TEXT,
    farm_size REAL, -- in acres
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS soil_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER NOT NULL,
    moisture REAL NOT NULL, -- percentage (0-100)
    temperature REAL NOT NULL, -- in Celsius
    ph REAL, -- pH level (0-14)
    nitrogen REAL, -- N in mg/kg
    phosphorus REAL, -- P in mg/kg
    potassium REAL, -- K in mg/kg
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farm_id) REFERENCES farms(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS weather_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER NOT NULL,
    temperature REAL NOT NULL, -- in Celsius
    humidity REAL NOT NULL, -- percentage (0-100)
    rainfall REAL NOT NULL, -- rainfall in mm
    forecast TEXT, -- e.g., 'sunny', 'cloudy', 'rainy', 'windy'
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farm_id) REFERENCES farms(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER NOT NULL,
    prediction_type TEXT NOT NULL, -- 'irrigation' or 'disease'
    inputs TEXT NOT NULL, -- JSON formatted input metrics
    results TEXT NOT NULL, -- JSON formatted prediction outcome (e.g., status, confidence)
    confidence REAL, -- confidence percentage (0-100)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farm_id) REFERENCES farms(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS irrigation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER NOT NULL,
    action TEXT NOT NULL, -- 'pump_on', 'pump_off'
    water_volume_liters REAL,
    duration_minutes INTEGER,
    triggered_by TEXT DEFAULT 'AI', -- 'AI' or 'Manual'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farm_id) REFERENCES farms(id) ON DELETE CASCADE
);
