-- Create separate database for Authentik
CREATE DATABASE authentik;

-- App tables are managed by SQLAlchemy (alembic),
-- but we seed some initial data here for convenience.

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE appdb TO postgres;
GRANT ALL PRIVILEGES ON DATABASE authentik TO postgres;
