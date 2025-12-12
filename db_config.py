# db_config.py
# Complete database configuration for Streamlit with secrets management

import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

def get_db_config():
    """
    Get database configuration from Streamlit secrets
    """
    try:
        if "mysql" in st.secrets:
            return {
                'host': st.secrets["mysql"]["host"],
                'port': int(st.secrets["mysql"]["port"]),
                'database': st.secrets["mysql"]["database"],
                'user': st.secrets["mysql"]["user"],
                'password': st.secrets["mysql"]["password"]
            }
        else:
            st.error("⚠️ Database configuration not found in secrets!")
            st.info("Please add database credentials to .streamlit/secrets.toml")
            st.stop()
    except Exception as e:
        st.error(f"Error reading database configuration: {e}")
        st.stop()

def get_db_connection_string():
    """Generate MySQL connection string"""
    config = get_db_config()
    
    connection_string = (
        f"mysql+pymysql://{config['user']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['database']}"
    )
    return connection_string

@st.cache_resource
def get_db_engine():
    """Create and cache database engine with connection pooling"""
    try:
        connection_string = get_db_connection_string()
        
        engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
            connect_args={
                'connect_timeout': 10,
                'charset': 'utf8mb4'
            }
        )
        return engine
    except Exception as e:
        st.error(f"Failed to create database engine: {e}")
        st.stop()

def test_connection():
    """Test database connection and return boolean"""
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.error("Please check your database credentials and network connection")
        return False

def get_connection_info():
    """Get connection info for display (without password)"""
    try:
        config = get_db_config()
        return {
            "host": config["host"],
            "port": config["port"],
            "database": config["database"],
            "user": config["user"]
        }
    except:
        return None
