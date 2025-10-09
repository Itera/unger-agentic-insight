-- Initialize the insight database with sensor data tables

-- Table for HMI sensor data (from sample_data.csv)
CREATE TABLE hmi_sensor_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    name VARCHAR(255) NOT NULL,
    value DECIMAL(10,2),
    unit VARCHAR(50),
    quality VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for Experion tag configuration (from TagConfigFormTo_Itera.csv)
CREATE TABLE tag_configuration (
    id SERIAL PRIMARY KEY,
    record_id INTEGER,
    name VARCHAR(255) NOT NULL,
    phd_entity_type VARCHAR(10),
    tag_no INTEGER,
    active BOOLEAN,
    description TEXT,
    parent_tag VARCHAR(255),
    class_tag BOOLEAN,
    tag_units VARCHAR(50),
    tolerance DECIMAL(5,2),
    tolerance_type VARCHAR(10),
    collection BOOLEAN,
    scan_frequency INTEGER,
    high_extreme DECIMAL(10,2),
    low_extreme DECIMAL(10,2),
    asset VARCHAR(255),
    item VARCHAR(255),
    function_name VARCHAR(255),
    source_system VARCHAR(50),
    source_tag_type VARCHAR(50),
    source_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for Itera sensor measurements (from itera_data.csv)
CREATE TABLE itera_measurements (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    time_string VARCHAR(50),
    li_329_value DECIMAL(15,12),
    li_331_value DECIMAL(15,12),
    li_440_value DECIMAL(15,12),
    li_038_value DECIMAL(15,12),
    li_001_value DECIMAL(15,12),
    li_002_value DECIMAL(15,12),
    li_003_value DECIMAL(15,12),
    li_327_value DECIMAL(15,12),
    li_329_daca_value DECIMAL(15,12),
    li_331_daca_value DECIMAL(15,12),
    li_351_value DECIMAL(15,12),
    li_353_value DECIMAL(15,12),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for CSV import tracking
CREATE TABLE csv_imports (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    rows_imported INTEGER,
    import_status VARCHAR(50) DEFAULT 'success',
    imported_at TIMESTAMPTZ DEFAULT NOW(),
    error_message TEXT
);

-- Create indexes for better query performance
CREATE INDEX idx_hmi_sensor_timestamp ON hmi_sensor_data(timestamp);
CREATE INDEX idx_hmi_sensor_name ON hmi_sensor_data(name);
CREATE INDEX idx_tag_config_name ON tag_configuration(name);
CREATE INDEX idx_itera_timestamp ON itera_measurements(timestamp);

-- Insert some sample data to verify the setup
INSERT INTO csv_imports (filename, file_type, rows_imported) 
VALUES 
  ('sample_data.csv', 'hmi_sensor', 0),
  ('TagConfigFormTo_Itera.csv', 'tag_config', 0),
  ('itera_data.csv', 'itera_measurements', 0);