import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, text
from .models import Setting, LogEntry


# Database file path - handle both local and Docker environments
if os.getenv('DOCKER_ENV') or Path('/app').exists():
    # Docker environment: use /app/db
    DB_DIR = Path("/app/db")
else:
    # Local development environment: use manager/db
    DB_DIR = Path(__file__).parent.parent / "db"

DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "manager.db"

# Create database engine, configure WAL mode and related optimizations
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={
        "check_same_thread": False,  # Allow multi-thread access
    }
)


def create_db_and_tables():
    """Create database and tables"""
    SQLModel.metadata.create_all(engine)

    # Configure WAL mode and related optimizations
    with engine.connect() as connection:
        # Enable WAL mode
        connection.execute(text("PRAGMA journal_mode = WAL;"))
        # Set synchronous mode to NORMAL for better performance
        connection.execute(text("PRAGMA synchronous = NORMAL;"))
        # Set WAL auto-checkpoint size (in pages)
        connection.execute(text("PRAGMA wal_autocheckpoint = 500;"))
        # Set cache size (in pages, negative means KB)
        connection.execute(text("PRAGMA cache_size = -32000;"))  # 32MB
        # Enable foreign key constraints
        connection.execute(text("PRAGMA foreign_keys = ON;"))
        connection.commit()


def configure_connection_pragmas(connection):
    """Configure connection PRAGMA settings"""
    connection.execute(text("PRAGMA journal_mode = WAL;"))
    connection.execute(text("PRAGMA synchronous = NORMAL;"))
    connection.execute(text("PRAGMA foreign_keys = ON;"))


def get_session():
    """Get database session"""
    with Session(engine) as session:
        # Ensure each session is configured with correct PRAGMA
        session.exec(text("PRAGMA journal_mode = WAL;"))
        session.exec(text("PRAGMA synchronous = NORMAL;"))
        session.exec(text("PRAGMA foreign_keys = ON;"))
        yield session


async def init_database():
    """Initialize database"""
    create_db_and_tables()

    # Check if setting record exists, create default if not
    with Session(engine) as session:
        from sqlmodel import select
        existing_setting = session.exec(select(Setting)).first()
        if not existing_setting:
            try:
                # Import configuration modules
                from config import get_all_config_keys, get_sensitive_config_keys
                from config.manager import ConfigManager
                from config.sources import EnvironmentConfigSource, DefaultValueConfigSource

                # Create a temporary config manager without ManagerBackendSource to avoid circular dependency
                temp_config_manager = ConfigManager()
                temp_config_manager._sources = [
                    EnvironmentConfigSource(),
                    DefaultValueConfigSource()
                ]

                default_config = await temp_config_manager.get_config(get_all_config_keys())
                print(f"Default config: {default_config}")

                from .crypto import crypto_manager

                sensitive_config_keys = get_sensitive_config_keys()

                for key in sensitive_config_keys:
                    if key in default_config:
                        encrypted_key = f"{key}_encrypted"
                        default_config[encrypted_key] = crypto_manager.encrypt(default_config[key])

                default_setting = Setting.model_validate(default_config)

                session.add(default_setting)
                session.commit()
            except Exception as e:
                print(f"Error creating default setting: {e}")


def get_setting():
    """Get settings (only one record)"""
    with Session(engine) as session:
        from sqlmodel import select
        setting = session.exec(select(Setting)).first()
        if not setting:
            raise ValueError("No setting found. Please initialize the database first.")
        return setting
        

def update_setting(setting_data: dict):
    """Update settings"""
    with Session(engine) as session:
        from sqlmodel import select
        setting = session.exec(select(Setting)).first()
        if not setting:
            raise ValueError("No setting found. Please initialize the database first.")

        # Update fields, special handling for encrypted fields
        from .crypto import crypto_manager
        from config import get_sensitive_config_keys

        sensitive_config_keys = get_sensitive_config_keys()

        # Update field values
        for key, value in setting_data.items():
            if hasattr(setting, key):
                # Encrypt sensitive fields
                if key in sensitive_config_keys:
                    # Encrypted fields need to be set to corresponding _encrypted field
                    encrypted_key = f"{key}_encrypted"
                    if hasattr(setting, encrypted_key):
                        setattr(setting, encrypted_key, crypto_manager.encrypt(value))
                else:
                    # Regular fields are set directly
                    setattr(setting, key, value)

        session.add(setting)
        session.commit()
        session.refresh(setting)
        return setting

def cleanup_old_logs():
    try:
        from sqlmodel import select
        from datetime import datetime, timedelta
        
        setting = get_setting()
        
        days = setting.log_save_days
        
        cutoff_time = datetime.now() - timedelta(days=days)

        # Delete expired logs
        with Session(engine) as session:
            delete_query = select(LogEntry).where(LogEntry.timestamp < cutoff_time)
            old_logs = session.exec(delete_query).all()

            deleted_count = len(old_logs)
            for log in old_logs:
                session.delete(log)

            session.commit()

            print(f"Cleaned up {deleted_count} old log entries (older than {days} days)")
    
    except Exception as e:
            print(f"Error during log cleanup: {e}")
