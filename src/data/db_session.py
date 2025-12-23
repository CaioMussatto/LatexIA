import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

# Setup professional logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("DATABASE_URL not found in .env file.")
    raise ValueError("DATABASE_URL is missing.")

# Create the engine
engine = create_engine(DATABASE_URL)

# Create the SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the Base class ONLY ONCE here
Base = declarative_base()

def init_db():
    """
    Initializes the database.
    It imports the models effectively registering them with the Base metadata,
    and then creates the tables if they do not exist.
    """
    try:
        # Import models inside the function to avoid circular imports
        # This is crucial: Base knows about the models only after this import
        import src.data.models_db  # noqa: F401
        
        logger.info("Checking for database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully. Tables are ready.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e