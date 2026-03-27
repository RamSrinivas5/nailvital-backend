import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Use DATABASE_URL from environment (Supabase/PostgreSQL) or fallback to local XAMPP MySQL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    if os.getenv("RENDER"):
        # We are on Render but no DB is connected
        print("CRITICAL ERROR: No DATABASE_URL found on Render. Please connect a database in the Render dashboard.")
        # Provide a dummy URL to prevent crash during build, but it will fail on request
        SQLALCHEMY_DATABASE_URL = "postgresql://user:pass@localhost/dummy"
    else:
        # Local development fallback
        SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://root:@localhost/nailvital"

# Fix for Heroku/Render/HuggingFace style postgres:// vs postgresql://
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine_args = {}
if "postgresql" in SQLALCHEMY_DATABASE_URL:
    # Recommended settings for cloud databases like Supabase/Aiven
    engine_args = {"pool_pre_ping": True, "pool_recycle": 3600}

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
