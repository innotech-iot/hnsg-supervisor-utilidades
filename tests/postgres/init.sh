#!/bin/sh
set -eu
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=ON_ERROR_STOP=1 <<'SQL'
\getenv fixture_password HNSG_PGTEST_PASSWORD
\getenv isolation_token HNSG_PGTEST_TOKEN
CREATE ROLE hnsg_fixture LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'fixture_password';
CREATE TABLE hnsg_test_isolation (token TEXT PRIMARY KEY);
INSERT INTO hnsg_test_isolation VALUES (:'isolation_token');
SQL
