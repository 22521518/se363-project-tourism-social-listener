
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to python path to allow imports
# Go up 5 levels: location_extraction -> tasks -> processing -> services -> projects -> airflow
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from projects.services.processing.tasks.location_extraction.config.settings import DatabaseConfig
from projects.services.processing.tasks.location_extraction.orm.models import create_location_tables, Base
from sqlalchemy import create_engine

def main():
    """Initialize database tables."""
    logger.info("Starting database initialization...")
    
    # Load environment variables
    # We look for .env in the task directory first
    current_dir = Path(__file__).resolve().parent
    env_path = current_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded .env from {env_path}")
    else:
        # Fallback to loading from where the script is run or let system envs take over
        load_dotenv()
        logger.info("Loaded default .env")

    try:
        config = DatabaseConfig.from_env()
        logger.info(f"Connecting to database at {config.host}:{config.port}/{config.database}")
        
        engine = create_engine(config.connection_string)
        
        # Create tables
        create_location_tables(engine)
        logger.info("Successfully created location extraction database tables.")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
