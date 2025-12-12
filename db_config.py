# db_config_v2.py
# Using Streamlit's built-in connection management

import streamlit as st
from sqlalchemy import text

@st.cache_resource
def get_connection():
    """Get database connection using Streamlit's connection API"""
    return st.connection(
        "mysql",
        type="sql",
        url=f"mysql+pymysql://{st.secrets['mysql']['user']}:{st.secrets['mysql']['password']}"
           f"@{st.secrets['mysql']['host']}:{st.secrets['mysql']['port']}"
           f"/{st.secrets['mysql']['database']}"
    )

def query_db(query, params=None):
    """Execute query and return DataFrame"""
    conn = get_connection()
    return conn.query(query, params=params, ttl=0)

def execute_db(query, params=None):
    """Execute non-query statement"""
    conn = get_connection()
    with conn.session as session:
        session.execute(text(query), params or {})
        session.commit()
