---------------------------------------------------------
----------------------- UNICONFIG -----------------------
---------------------------------------------------------

CREATE DATABASE "uniconfig";

---------------------------------------------------------
----------------------- INVENTORY -----------------------
---------------------------------------------------------

CREATE DATABASE "inventory";

\c "inventory";

CREATE TABLE IF NOT EXISTS uniconfig_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(250) NOT NULL UNIQUE,
    tenant_id VARCHAR(64)
);

CREATE INDEX idx_uniconfig_zones_tenant_id ON uniconfig_zones(tenant_id);

CREATE TABLE IF NOT EXISTS device_inventory (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50),
    management_ip inet,
    config json,
    location VARCHAR(255),
    model VARCHAR(255),
    sw VARCHAR(50),
    sw_version VARCHAR(50),
    mac_address macaddr,
    serial_number VARCHAR(50),
    vendor VARCHAR(50),
    uniconfig_zone INTEGER,
    mount_parameters jsonb,
    username VARCHAR(50),
    password VARCHAR(50),
    FOREIGN KEY (uniconfig_zone) REFERENCES uniconfig_zones(id) ON DELETE CASCADE
);
