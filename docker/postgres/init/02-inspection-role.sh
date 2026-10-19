#!/bin/sh
set -eu
# Cluster-role provisioning is deliberately separate from owner migrations.
psql -v ON_ERROR_STOP=1 -U "${POSTGRES_USER:-postgres}" -d postgres <<'SQL'
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='infraarch_readonly') THEN
    CREATE ROLE infraarch_readonly NOLOGIN;
  END IF;
END $$;
SQL
if [ -n "${INFRAARCH_READONLY_PASSWORD:-}" ]; then
  psql -v ON_ERROR_STOP=1 -U "${POSTGRES_USER:-postgres}" -d postgres \
    -v inspection_password="$INFRAARCH_READONLY_PASSWORD" <<'SQL'
ALTER ROLE infraarch_readonly LOGIN PASSWORD :'inspection_password';
SQL
fi
