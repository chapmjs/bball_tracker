# test_connection.py
# Comprehensive connection testing

import streamlit as st
from db_config import test_connection, get_connection_info, show_connection_status

st.set_page_config(page_title="DB Connection Test", layout="wide")

st.title("🔌 Database Connection Test")

# Show connection info in sidebar
show_connection_status()

st.header("Step-by-Step Connection Test")

# Step 1: Check secrets
with st.expander("📋 Step 1: Check Secrets Configuration", expanded=True):
    try:
        if "mysql" in st.secrets:
            st.success("✓ Secrets file found and loaded")
            st.json({
                "host": st.secrets["mysql"]["host"],
                "port": st.secrets["mysql"]["port"],
                "database": st.secrets["mysql"]["database"],
                "user": st.secrets["mysql"]["user"],
                "password": "***hidden***"
            })
        else:
            st.error("✗ No [mysql] section found in secrets")
            st.info("Create .streamlit/secrets.toml with the format shown below")
    except Exception as e:
        st.error(f"✗ Error reading secrets: {e}")

# Step 2: Test imports
with st.expander("📦 Step 2: Test Module Imports"):
    try:
        from db_config import get_connection, query_db, execute_db
        st.success("✓ db_config imported successfully")
        
        from db_helpers import get_teams, get_players
        st.success("✓ db_helpers imported successfully")
    except Exception as e:
        st.error(f"✗ Import failed: {e}")
        st.stop()

# Step 3: Test connection
with st.expander("🔗 Step 3: Test Database Connection", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧪 Test Connection", type="primary", use_container_width=True):
            with st.spinner("Testing connection..."):
                if test_connection():
                    st.success("✓ Connection successful!")
                else:
                    st.error("✗ Connection failed")
    
    with col2:
        if st.button("ℹ️ Show Connection Info", use_container_width=True):
            info = get_connection_info()
            if "error" in info:
                st.error(f"Error: {info['error']}")
            else:
                st.json(info)

# Step 4: Test basic query
with st.expander("📊 Step 4: Test Database Query"):
    if st.button("Run Test Query"):
        try:
            from db_config import query_db
            df = query_db("SELECT VERSION() as mysql_version, DATABASE() as current_db", ttl=0)
            if not df.empty:
                st.success("✓ Query executed successfully!")
                st.dataframe(df)
            else:
                st.warning("Query returned no results")
        except Exception as e:
            st.error(f"✗ Query failed: {e}")

# Step 5: Test table access
with st.expander("🗄️ Step 5: Test Table Access"):
    if st.button("List Tables"):
        try:
            from db_config import query_db
            df = query_db("SHOW TABLES", ttl=0)
            if not df.empty:
                st.success(f"✓ Found {len(df)} tables")
                st.dataframe(df)
            else:
                st.warning("No tables found - database may be empty")
                st.info("Run the basketball_tracker_schema.sql to create tables")
        except Exception as e:
            st.error(f"✗ Failed to list tables: {e}")

# Reference information
st.divider()
st.subheader("📚 Configuration Reference")

col1, col2 = st.columns(2)

with col1:
    st.write("**Required secrets.toml format:**")
    st.code("""
[mysql]
host = "mexico.bbfarm.org"
port = 3306
database = "basketball_tracker"
user = "your_username"
password = "your_password"
    """, language="toml")

with col2:
    st.write("**File location:**")
    st.code(".streamlit/secrets.toml")
    st.write("**Remember to:**")
    st.markdown("""
    - Add to `.gitignore`
    - Restart Streamlit after changes
    - Verify database credentials
    - Check firewall rules for port 3306
    """)
