#!/bin/sh
set -eu

# The official postgres entrypoint runs this only when the data volume is new.
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres \
  -v owner_password="$INFRAARCH_OWNER_PASSWORD" \
  -v app_password="$INFRAARCH_APP_PASSWORD" <<'SQL'
CREATE ROLE infraarch_owner LOGIN PASSWORD :'owner_password';
CREATE ROLE infraarch_app LOGIN PASSWORD :'app_password';
CREATE DATABASE infraarch OWNER infraarch_owner;
CREATE DATABASE infraarch_test OWNER infraarch_owner;
REVOKE ALL ON DATABASE infraarch FROM PUBLIC;
REVOKE ALL ON DATABASE infraarch_test FROM PUBLIC;
GRANT CONNECT ON DATABASE infraarch TO infraarch_owner, infraarch_app;
GRANT CONNECT ON DATABASE infraarch_test TO infraarch_owner, infraarch_app;
SQL
