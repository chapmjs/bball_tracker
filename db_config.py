# db_config.py
# Updated to use Streamlit secrets management

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

def get_db_connection_string():
    """Generate MySQL connection string from Streamlit secrets"""
    try:
        # Access secrets from st.secrets
        db_config = st.secrets["mysql"]
        
        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        return connection_string
    
    except KeyError as e:
        st.error(f"Missing required database configuration: {e}")
        st.error("Please check your .streamlit/secrets.toml file")
        raise
    except Exception as e:
        st.error(f"Error reading database configuration: {e}")
        raise

@st.cache_resource
def get_db_engine():
    """Create and cache database engine with connection pooling"""
    connection_string = get_db_connection_string()
    
    engine = create_engine(
        connection_string,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,      # Verify connections before using
        pool_recycle=3600,       # Recycle connections after 1 hour
        echo=False,              # Set to True for SQL debugging
        connect_args={
            'connect_timeout': 10,
            'charset': 'utf8mb4'
        }
    )
    return engine

def test_connection():
    """Test database connection"""
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return True
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return False

def get_connection_info():
    """Get connection info for display (without password)"""
    try:
        db_config = st.secrets["mysql"]
        return {
            "host": db_config["host"],
            "port": db_config["port"],
            "database": db_config["database"],
            "user": db_config["user"]
        }
    except:
        return None
