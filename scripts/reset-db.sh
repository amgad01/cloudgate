#!/usr/bin/env bash
set -euo pipefail

# Reset PostgreSQL database used by CloudGate.
# Requirements: Docker Compose running with a 'db' service and POSTGRES_DB/USER.

COMPOSE_DIR="$(dirname "$0")/.."
pushd "$COMPOSE_DIR" >/dev/null

DB_SERVICE=${DB_SERVICE:-postgres}
DB_NAME=${POSTGRES_DB:-cloudgate}
DB_USER=${POSTGRES_USER:-postgres}

echo "Resetting database on service: $DB_SERVICE, db: $DB_NAME, user: $DB_USER"

# Drop and recreate schema (safe reset of all tables)
docker compose exec -T "$DB_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
DO $$ DECLARE
    r RECORD;
BEGIN
    -- Disable constraints
    EXECUTE 'ALTER SCHEMA public OWNER TO ' || current_user || ';';
    -- Drop all tables in public schema
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;
SQL

echo "Applying init schema from scripts/init-db.sql..."
docker compose exec -T "$DB_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -f scripts/init-db.sql

echo "Database reset complete."

popd >/dev/null
