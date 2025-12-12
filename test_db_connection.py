# test_db_connection.py

import streamlit as st
from db_config import test_connection, get_connection_info

st.title("🔌 Database Connection Test")

if st.button("Test Connection"):
    with st.spinner("Testing connection..."):
        success, message = test_connection()
        
        if success:
            st.success(message)
            
            info = get_connection_info()
            st.subheader("Connection Details:")
            st.json(info)
        else:
            st.error(message)
            st.info("Check your .streamlit/secrets.toml file")

st.divider()

st.subheader("Expected secrets.toml format:")
