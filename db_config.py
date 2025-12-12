# db_config.py
# Streamlit-native database configuration using st.connection

import streamlit as st
from sqlalchemy import text
import pandas as pd

@st.cache_resource
def get_connection():
    """
    Get database connection using Streamlit's native connection API
    This automatically handles connection pooling and caching
    """
    try:
        # Streamlit's connection API automatically reads from secrets.toml
        conn = st.connection(
            "mysql",
            type="sql",
            url=f"mysql+pymysql://{st.secrets['mysql']['user']}:{st.secrets['mysql']['password']}"
               f"@{st.secrets['mysql']['host']}:{st.secrets['mysql']['port']}"
               f"/{st.secrets['mysql']['database']}?charset=utf8mb4"
        )
        return conn
    except Exception as e:
        st.error(f"Failed to create database connection: {e}")
        st.info("Please check your .streamlit/secrets.toml file")
        st.stop()

def test_connection():
    """Test database connection and return boolean"""
    try:
        conn = get_connection()
        # Simple query to test connection
        result = conn.query("SELECT 1 as test", ttl=0)
        return True
    except Exception as e:
        st.error(f"Database connection test failed: {e}")
        with st.expander("Connection Details"):
            st.write("**Error details:**")
            st.code(str(e))
            st.write("**Expected secrets format:**")
            st.code("""
[mysql]
host = "mexico.bbfarm.org"
port = 3306
database = "basketball_tracker"
user = "your_username"
password = "your_password"
            """)
        return False

def query_db(query, params=None, ttl=600):
    """
    Execute a SELECT query and return results as DataFrame
    
    Args:
        query: SQL query string
        params: Dictionary of parameters for parameterized queries
        ttl: Time to live for cache in seconds (default 600 = 10 minutes)
    
    Returns:
        pandas DataFrame with query results
    """
    try:
        conn = get_connection()
        if params:
            df = conn.query(query, params=params, ttl=ttl)
        else:
            df = conn.query(query, ttl=ttl)
        return df
    except Exception as e:
        st.error(f"Query execution error: {e}")
        st.code(query)
        return pd.DataFrame()

def execute_db(query, params=None):
    """
    Execute a non-SELECT query (INSERT, UPDATE, DELETE)
    
    Args:
        query: SQL query string
        params: Dictionary of parameters for parameterized queries
    
    Returns:
        Result object from SQLAlchemy
    """
    try:
        conn = get_connection()
        with conn.session as session:
            result = session.execute(text(query), params or {})
            session.commit()
            return result
    except Exception as e:
        st.error(f"Execute error: {e}")
        st.code(query)
        raise

def insert_and_get_id(query, params):
    """
    Execute an INSERT query and return the last inserted ID
    
    Args:
        query: SQL INSERT query string
        params: Dictionary of parameters
    
    Returns:
        Last inserted row ID
    """
    try:
        conn = get_connection()
        with conn.session as session:
            result = session.execute(text(query), params)
            session.commit()
            return result.lastrowid
    except Exception as e:
        st.error(f"Insert error: {e}")
        st.code(query)
        raise

def get_connection_info():
    """Get connection info for display (without password)"""
    try:
        return {
            "host": st.secrets["mysql"]["host"],
            "port": st.secrets["mysql"]["port"],
            "database": st.secrets["mysql"]["database"],
            "user": st.secrets["mysql"]["user"],
            "status": "✓ Connected" if test_connection() else "✗ Disconnected"
        }
    except Exception as e:
        return {"error": str(e)}

def show_connection_status():
    """Display connection status in sidebar (helpful for debugging)"""
    with st.sidebar:
        st.divider()
        st.subheader("🔌 Database Status")
        info = get_connection_info()
        
        if "error" in info:
            st.error(f"Error: {info['error']}")
        else:
            if "✓" in info['status']:
                st.success(info['status'])
            else:
                st.error(info['status'])
            
            with st.expander("Connection Details"):
                st.write(f"**Host:** {info['host']}")
                st.write(f"**Port:** {info['port']}")
                st.write(f"**Database:** {info['database']}")
                st.write(f"**User:** {info['user']}")

# Optional: Reset connection cache (useful for debugging)
def reset_connection():
    """Reset the cached database connection"""
    st.cache_resource.clear()
    st.rerun()
