-- Step 2: Run this on the 'certify_studio' database after it's created
-- This sets up permissions and extensions

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO certify_user;
GRANT CREATE ON SCHEMA public TO certify_user;

-- Make certify_user the owner
ALTER SCHEMA public OWNER TO certify_user;
ALTER DATABASE certify_studio OWNER TO certify_user;

-- Create useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Verify setup
SELECT current_database(), current_user, version();
