-- Certify Studio PostgreSQL Setup Script
-- Run this in pgAdmin Query Tool

-- Create the database
CREATE DATABASE certify_studio
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'English_United States.1252'
    LC_CTYPE = 'English_United States.1252'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Create user for the application
CREATE USER certify_user WITH
    PASSWORD 'CertifyStudio2024!'
    CREATEDB
    NOCREATEROLE
    NOINHERIT
    LOGIN;

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE certify_studio TO certify_user;

-- Connect to the certify_studio database to set up permissions
\c certify_studio

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO certify_user;
GRANT CREATE ON SCHEMA public TO certify_user;

-- Make certify_user the owner of the public schema
ALTER SCHEMA public OWNER TO certify_user;

-- Ensure certify_user can create tables
ALTER DATABASE certify_studio OWNER TO certify_user;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Verification queries
SELECT current_database();
SELECT current_user;
SELECT version();

-- List all databases
SELECT datname FROM pg_database WHERE datistemplate = false;

-- Show user privileges
SELECT grantee, privilege_type 
FROM information_schema.role_table_grants 
WHERE table_schema='public';
