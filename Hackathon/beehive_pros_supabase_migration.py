"""
=============================================================================
BEEHIVE PRO'S TIME CARD - Supabase Database Migration Script
=============================================================================
Ferris Development Group - Trades Time Tracking System

Run this script to generate the complete SQL migration for your Supabase
project. You can either:
  1. Copy the printed SQL and paste it into the Supabase SQL Editor
  2. Run it directly against your Supabase DB using the connection string

Usage:
  python beehive_pros_supabase_migration.py              # Print SQL to console
  python beehive_pros_supabase_migration.py --execute     # Execute against DB

If executing directly, set your environment variable first:
  export SUPABASE_DB_URL="postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"
=============================================================================
"""

import sys
import os

# ───────────────────────────────────────────────────────────────────────────
# SCHEMA DEFINITION
# ───────────────────────────────────────────────────────────────────────────

MIGRATION_SQL = """
-- ==========================================================================
-- BEEHIVE PRO'S TIME CARD - Complete Database Schema
-- Ferris Development Group
-- ==========================================================================
-- Run this entire script in the Supabase SQL Editor (supabase.com/dashboard)
-- ==========================================================================

-- ──────────────────────────────────────────────────────────────────────────
-- 1. EXTENSIONS
-- ──────────────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";  -- for advanced geo queries later


-- ──────────────────────────────────────────────────────────────────────────
-- 2. EMPLOYEES TABLE
--    Phone number is the primary identifier (E.164 format: +1XXXXXXXXXX)
-- ──────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS employees (
    phone           TEXT PRIMARY KEY,               -- E.164 format, e.g. +16175551234
    full_name       TEXT NOT NULL,
    trade           TEXT NOT NULL DEFAULT 'general', -- electrician, plumber, hvac, general
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for lookups by trade
CREATE INDEX idx_employees_trade ON employees (trade);
CREATE INDEX idx_employees_active ON employees (is_active) WHERE is_active = true;

COMMENT ON TABLE employees IS 'Registered trades workers identified by phone number';
COMMENT ON COLUMN employees.phone IS 'Primary key - E.164 phone format (+1XXXXXXXXXX)';
COMMENT ON COLUMN employees.trade IS 'Trade type: electrician, plumber, hvac, general';


-- ──────────────────────────────────────────────────────────────────────────
-- 3. JOB SITES TABLE
--    Each site has a GPS center point and an acceptable radius (geofence)
-- ──────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS job_sites (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_name       TEXT NOT NULL,
    address         TEXT,
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    radius_meters   INTEGER NOT NULL DEFAULT 150,   -- geofence radius in meters
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_job_sites_active ON job_sites (is_active) WHERE is_active = true;

COMMENT ON TABLE job_sites IS 'Ferris Development Group job site locations with geofence radius';
COMMENT ON COLUMN job_sites.radius_meters IS 'Acceptable clock-in radius from site center (default 150m / ~500ft)';


-- ──────────────────────────────────────────────────────────────────────────
-- 4. TIME ENTRIES TABLE
--    Each row = one shift. Clock-in creates the row, clock-out completes it.
-- ──────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS time_entries (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Employee reference
    employee_phone              TEXT NOT NULL REFERENCES employees(phone),

    -- Job site reference
    job_site_id                 UUID NOT NULL REFERENCES job_sites(id),

    -- Clock-in data
    clock_in_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    clock_in_latitude           DOUBLE PRECISION,
    clock_in_longitude          DOUBLE PRECISION,
    clock_in_ip                 TEXT,
    clock_in_distance_meters    NUMERIC(10,2),       -- calculated distance from site center
    clock_in_within_geofence    BOOLEAN NOT NULL DEFAULT false,

    -- Clock-out data (null until worker clocks out)
    clock_out_at                TIMESTAMPTZ,
    clock_out_latitude          DOUBLE PRECISION,
    clock_out_longitude         DOUBLE PRECISION,
    clock_out_ip                TEXT,
    clock_out_distance_meters   NUMERIC(10,2),
    clock_out_within_geofence   BOOLEAN,

    -- Calculated / metadata
    total_hours                 NUMERIC(6,2),         -- auto-calculated on clock-out
    is_flagged                  BOOLEAN NOT NULL DEFAULT false,  -- flagged for review
    flag_reason                 TEXT,                  -- why it was flagged
    notes                       TEXT,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Performance indexes
CREATE INDEX idx_time_entries_employee ON time_entries (employee_phone);
CREATE INDEX idx_time_entries_site ON time_entries (job_site_id);
CREATE INDEX idx_time_entries_clock_in ON time_entries (clock_in_at DESC);
CREATE INDEX idx_time_entries_open ON time_entries (employee_phone, clock_out_at)
    WHERE clock_out_at IS NULL;
CREATE INDEX idx_time_entries_flagged ON time_entries (is_flagged)
    WHERE is_flagged = true;

COMMENT ON TABLE time_entries IS 'Individual shift records with GPS verification data';
COMMENT ON COLUMN time_entries.is_flagged IS 'True if clock-in/out was outside geofence or otherwise suspicious';


-- ──────────────────────────────────────────────────────────────────────────
-- 5. HAVERSINE DISTANCE FUNCTION
--    Calculates meters between two GPS coordinates
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION calculate_distance_meters(
    lat1 DOUBLE PRECISION,
    lon1 DOUBLE PRECISION,
    lat2 DOUBLE PRECISION,
    lon2 DOUBLE PRECISION
)
RETURNS NUMERIC AS $$
DECLARE
    R CONSTANT DOUBLE PRECISION := 6371000;  -- Earth radius in meters
    phi1 DOUBLE PRECISION;
    phi2 DOUBLE PRECISION;
    delta_phi DOUBLE PRECISION;
    delta_lambda DOUBLE PRECISION;
    a DOUBLE PRECISION;
    c DOUBLE PRECISION;
BEGIN
    phi1 := radians(lat1);
    phi2 := radians(lat2);
    delta_phi := radians(lat2 - lat1);
    delta_lambda := radians(lon2 - lon1);

    a := sin(delta_phi / 2) * sin(delta_phi / 2) +
         cos(phi1) * cos(phi2) *
         sin(delta_lambda / 2) * sin(delta_lambda / 2);
    c := 2 * atan2(sqrt(a), sqrt(1 - a));

    RETURN ROUND((R * c)::NUMERIC, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_distance_meters IS 'Haversine formula: returns distance in meters between two lat/lng points';


-- ──────────────────────────────────────────────────────────────────────────
-- 6. CLOCK-IN FUNCTION (RPC)
--    Called from the frontend. Handles employee upsert, distance calc,
--    geofence check, and flagging in one atomic transaction.
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION clock_in(
    p_phone TEXT,
    p_name TEXT,
    p_trade TEXT DEFAULT 'general',
    p_job_site_id UUID DEFAULT NULL,
    p_latitude DOUBLE PRECISION DEFAULT NULL,
    p_longitude DOUBLE PRECISION DEFAULT NULL,
    p_ip TEXT DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_site job_sites%ROWTYPE;
    v_distance NUMERIC(10,2);
    v_within_geofence BOOLEAN := false;
    v_is_flagged BOOLEAN := false;
    v_flag_reason TEXT := NULL;
    v_entry_id UUID;
    v_open_entry UUID;
BEGIN
    -- Upsert employee (register on first use, update name if changed)
    INSERT INTO employees (phone, full_name, trade)
    VALUES (p_phone, p_name, p_trade)
    ON CONFLICT (phone) DO UPDATE SET
        full_name = EXCLUDED.full_name,
        updated_at = now();

    -- Check for already open shift
    SELECT id INTO v_open_entry
    FROM time_entries
    WHERE employee_phone = p_phone AND clock_out_at IS NULL
    LIMIT 1;

    IF v_open_entry IS NOT NULL THEN
        RETURN json_build_object(
            'success', false,
            'error', 'ALREADY_CLOCKED_IN',
            'message', 'You already have an open shift. Please clock out first.',
            'open_entry_id', v_open_entry
        );
    END IF;

    -- Get job site and calculate distance
    IF p_job_site_id IS NOT NULL AND p_latitude IS NOT NULL AND p_longitude IS NOT NULL THEN
        SELECT * INTO v_site FROM job_sites WHERE id = p_job_site_id;

        IF v_site.id IS NOT NULL THEN
            v_distance := calculate_distance_meters(
                p_latitude, p_longitude,
                v_site.latitude, v_site.longitude
            );
            v_within_geofence := (v_distance <= v_site.radius_meters);

            IF NOT v_within_geofence THEN
                v_is_flagged := true;
                v_flag_reason := format(
                    'Clock-in %.0fm from site (limit: %sm)',
                    v_distance, v_site.radius_meters
                );
            END IF;
        END IF;
    ELSIF p_latitude IS NULL OR p_longitude IS NULL THEN
        v_is_flagged := true;
        v_flag_reason := 'GPS location not provided at clock-in';
    END IF;

    -- Insert the time entry
    INSERT INTO time_entries (
        employee_phone, job_site_id,
        clock_in_at, clock_in_latitude, clock_in_longitude, clock_in_ip,
        clock_in_distance_meters, clock_in_within_geofence,
        is_flagged, flag_reason
    ) VALUES (
        p_phone, p_job_site_id,
        now(), p_latitude, p_longitude, p_ip,
        v_distance, v_within_geofence,
        v_is_flagged, v_flag_reason
    )
    RETURNING id INTO v_entry_id;

    RETURN json_build_object(
        'success', true,
        'entry_id', v_entry_id,
        'within_geofence', v_within_geofence,
        'distance_meters', v_distance,
        'is_flagged', v_is_flagged,
        'flag_reason', v_flag_reason,
        'clock_in_at', now()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ──────────────────────────────────────────────────────────────────────────
-- 7. CLOCK-OUT FUNCTION (RPC)
--    Completes the open shift, calculates total hours, checks geofence.
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION clock_out(
    p_phone TEXT,
    p_latitude DOUBLE PRECISION DEFAULT NULL,
    p_longitude DOUBLE PRECISION DEFAULT NULL,
    p_ip TEXT DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_entry time_entries%ROWTYPE;
    v_site job_sites%ROWTYPE;
    v_distance NUMERIC(10,2);
    v_within_geofence BOOLEAN := false;
    v_total_hours NUMERIC(6,2);
    v_flag_reason TEXT;
BEGIN
    -- Find the open shift
    SELECT * INTO v_entry
    FROM time_entries
    WHERE employee_phone = p_phone AND clock_out_at IS NULL
    ORDER BY clock_in_at DESC
    LIMIT 1;

    IF v_entry.id IS NULL THEN
        RETURN json_build_object(
            'success', false,
            'error', 'NO_OPEN_SHIFT',
            'message', 'No open shift found. Please clock in first.'
        );
    END IF;

    -- Calculate distance from job site
    IF v_entry.job_site_id IS NOT NULL AND p_latitude IS NOT NULL AND p_longitude IS NOT NULL THEN
        SELECT * INTO v_site FROM job_sites WHERE id = v_entry.job_site_id;

        IF v_site.id IS NOT NULL THEN
            v_distance := calculate_distance_meters(
                p_latitude, p_longitude,
                v_site.latitude, v_site.longitude
            );
            v_within_geofence := (v_distance <= v_site.radius_meters);
        END IF;
    END IF;

    -- Calculate total hours
    v_total_hours := ROUND(
        EXTRACT(EPOCH FROM (now() - v_entry.clock_in_at)) / 3600.0, 2
    );

    -- Build flag reason if needed
    v_flag_reason := v_entry.flag_reason;
    IF p_latitude IS NULL OR p_longitude IS NULL THEN
        v_flag_reason := COALESCE(v_flag_reason || '; ', '') || 'GPS not provided at clock-out';
    ELSIF NOT v_within_geofence AND v_distance IS NOT NULL THEN
        v_flag_reason := COALESCE(v_flag_reason || '; ', '') ||
            format('Clock-out %.0fm from site (limit: %sm)', v_distance, v_site.radius_meters);
    END IF;

    -- Update the entry
    UPDATE time_entries SET
        clock_out_at = now(),
        clock_out_latitude = p_latitude,
        clock_out_longitude = p_longitude,
        clock_out_ip = p_ip,
        clock_out_distance_meters = v_distance,
        clock_out_within_geofence = v_within_geofence,
        total_hours = v_total_hours,
        is_flagged = COALESCE(v_entry.is_flagged, false) OR
                     (p_latitude IS NULL) OR
                     (NOT v_within_geofence AND v_distance IS NOT NULL),
        flag_reason = v_flag_reason,
        updated_at = now()
    WHERE id = v_entry.id;

    RETURN json_build_object(
        'success', true,
        'entry_id', v_entry.id,
        'clock_in_at', v_entry.clock_in_at,
        'clock_out_at', now(),
        'total_hours', v_total_hours,
        'within_geofence', v_within_geofence,
        'distance_meters', v_distance,
        'is_flagged', (COALESCE(v_entry.is_flagged, false) OR
                       (p_latitude IS NULL) OR
                       (NOT v_within_geofence AND v_distance IS NOT NULL))
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ──────────────────────────────────────────────────────────────────────────
-- 8. USEFUL VIEWS
-- ──────────────────────────────────────────────────────────────────────────

-- Active shifts (who is currently clocked in)
CREATE OR REPLACE VIEW active_shifts AS
SELECT
    te.id AS entry_id,
    e.full_name,
    e.phone,
    e.trade,
    js.site_name,
    te.clock_in_at,
    te.clock_in_within_geofence,
    te.clock_in_distance_meters,
    te.is_flagged,
    te.flag_reason,
    ROUND(EXTRACT(EPOCH FROM (now() - te.clock_in_at)) / 3600.0, 2) AS hours_so_far
FROM time_entries te
JOIN employees e ON e.phone = te.employee_phone
LEFT JOIN job_sites js ON js.id = te.job_site_id
WHERE te.clock_out_at IS NULL
ORDER BY te.clock_in_at DESC;

-- Daily summary
CREATE OR REPLACE VIEW daily_summary AS
SELECT
    te.clock_in_at::DATE AS work_date,
    e.full_name,
    e.phone,
    e.trade,
    js.site_name,
    te.clock_in_at,
    te.clock_out_at,
    te.total_hours,
    te.clock_in_within_geofence,
    te.clock_out_within_geofence,
    te.clock_in_distance_meters,
    te.clock_out_distance_meters,
    te.is_flagged,
    te.flag_reason
FROM time_entries te
JOIN employees e ON e.phone = te.employee_phone
LEFT JOIN job_sites js ON js.id = te.job_site_id
ORDER BY te.clock_in_at DESC;

-- Weekly hours by employee
CREATE OR REPLACE VIEW weekly_hours AS
SELECT
    e.full_name,
    e.phone,
    e.trade,
    DATE_TRUNC('week', te.clock_in_at)::DATE AS week_starting,
    COUNT(*) AS total_shifts,
    ROUND(SUM(COALESCE(te.total_hours, 0)), 2) AS total_hours,
    COUNT(*) FILTER (WHERE te.is_flagged) AS flagged_shifts
FROM time_entries te
JOIN employees e ON e.phone = te.employee_phone
WHERE te.clock_out_at IS NOT NULL
GROUP BY e.full_name, e.phone, e.trade, DATE_TRUNC('week', te.clock_in_at)
ORDER BY week_starting DESC, e.full_name;


-- ──────────────────────────────────────────────────────────────────────────
-- 9. ROW LEVEL SECURITY (RLS)
--    Using anon key for this MVP. Lock down for production later.
-- ──────────────────────────────────────────────────────────────────────────

-- Enable RLS on all tables
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE time_entries ENABLE ROW LEVEL SECURITY;

-- Allow anon read/insert for MVP (tighten in production with auth)
CREATE POLICY "Allow anon read employees"
    ON employees FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon insert employees"
    ON employees FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon update employees"
    ON employees FOR UPDATE TO anon USING (true);

CREATE POLICY "Allow anon read job_sites"
    ON job_sites FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon read time_entries"
    ON time_entries FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon insert time_entries"
    ON time_entries FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon update time_entries"
    ON time_entries FOR UPDATE TO anon USING (true);


-- ──────────────────────────────────────────────────────────────────────────
-- 10. SEED DATA - Ferris Development Group Job Sites
--     Update these with actual site coordinates before deployment
-- ──────────────────────────────────────────────────────────────────────────

INSERT INTO job_sites (site_name, address, latitude, longitude, radius_meters) VALUES
    ('One Research Drive', '1 Research Dr, Westborough, MA 01581', 42.2668, -71.6162, 200),
    ('Westborough Data Center', 'Westborough, MA 01581', 42.2695, -71.6168, 250),
    ('Saratoga Multifamily', 'Saratoga, CA 95070', 37.2636, -122.0230, 200),
    ('Boston Seaport Office', 'Seaport Blvd, Boston, MA 02210', 42.3519, -71.0447, 150)
ON CONFLICT DO NOTHING;


-- ──────────────────────────────────────────────────────────────────────────
-- 11. UPDATED_AT TRIGGER
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER job_sites_updated_at
    BEFORE UPDATE ON job_sites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER time_entries_updated_at
    BEFORE UPDATE ON time_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ==========================================================================
-- MIGRATION COMPLETE
-- ==========================================================================
-- Tables created: employees, job_sites, time_entries
-- Functions: calculate_distance_meters, clock_in, clock_out
-- Views: active_shifts, daily_summary, weekly_hours
-- RLS: Enabled with anon policies for MVP
-- ==========================================================================
""".strip()


def main():
    if "--execute" in sys.argv:
        try:
            import psycopg2
        except ImportError:
            print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
            sys.exit(1)

        db_url = os.environ.get("SUPABASE_DB_URL")
        if not db_url:
            print("ERROR: Set SUPABASE_DB_URL environment variable")
            print("  export SUPABASE_DB_URL='postgresql://postgres.[ref]:[pw]@aws-0-[region].pooler.supabase.com:6543/postgres'")
            sys.exit(1)

        print("Connecting to Supabase...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()

        print("Running migration...")
        cur.execute(MIGRATION_SQL)
        print("Migration complete.")

        cur.close()
        conn.close()
    else:
        print("-- Copy everything below into the Supabase SQL Editor and click 'Run'")
        print("-- Or run with --execute flag to apply directly")
        print()
        print(MIGRATION_SQL)


if __name__ == "__main__":
    main()
