-- Step 1: Run this first on the 'postgres' database
-- This creates the database and user

-- Create the database
CREATE DATABASE certify_studio;

-- Create user for the application
CREATE USER certify_user WITH PASSWORD 'CertifyStudio2024!';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE certify_studio TO certify_user;
