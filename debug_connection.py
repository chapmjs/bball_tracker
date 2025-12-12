# debug_connection.py
# Comprehensive connection debugging

import streamlit as st

st.set_page_config(page_title="Connection Debug", layout="wide")
st.title("🔍 Database Connection Debugger")

# Test 1: Check if secrets exist
st.header("Test 1: Secrets Configuration")
try:
    if hasattr(st, 'secrets'):
        st.success("✓ st.secrets is available")
        
        if "mysql" in st.secrets:
            st.success("✓ [mysql] section found in secrets")
            
            # Show what we have (safely)
            st.write("**Found configuration:**")
            col1, col2 = st.columns(2)
            with col1:
                st.code(f"""
host: {st.secrets['mysql'].get('host', 'MISSING')}
port: {st.secrets['mysql'].get('port', 'MISSING')}
database: {st.secrets['mysql'].get('database', 'MISSING')}
user: {st.secrets['mysql'].get('user', 'MISSING')}
password: {'***' if 'password' in st.secrets['mysql'] else 'MISSING'}
                """)
            
            with col2:
                st.write("**Expected format:**")
                st.code("""
[mysql]
host = "mexico.bbfarm.org"
port = 3306
database = "basketball_tracker"
user = "your_username"
password = "your_password"
                """)
        else:
            st.error("✗ No [mysql] section in secrets")
            st.info("Add database configuration to .streamlit/secrets.toml")
            st.stop()
    else:
        st.error("✗ st.secrets not available")
        st.stop()
except Exception as e:
    st.error(f"✗ Error reading secrets: {e}")
    st.stop()

st.divider()

# Test 2: Check required packages
st.header("Test 2: Required Packages")
packages_ok = True

try:
    import sqlalchemy
    st.success(f"✓ sqlalchemy installed (version {sqlalchemy.__version__})")
except ImportError:
    st.error("✗ sqlalchemy not installed")
    st.code("pip install sqlalchemy")
    packages_ok = False

try:
    import pymysql
    st.success(f"✓ pymysql installed (version {pymysql.__version__})")
except ImportError:
    st.error("✗ pymysql not installed")
    st.code("pip install pymysql")
    packages_ok = False

if not packages_ok:
    st.stop()

st.divider()

# Test 3: Test connection string formation
st.header("Test 3: Connection String")
try:
    config = st.secrets["mysql"]
    conn_str = (
        f"mysql+pymysql://{config['user']}:***@"
        f"{config['host']}:{config['port']}/{config['database']}"
    )
    st.success("✓ Connection string formed successfully")
    st.code(conn_str)
except Exception as e:
    st.error(f"✗ Error forming connection string: {e}")
    st.stop()

st.divider()

# Test 4: Try basic connection
st.header("Test 4: Database Connection")

if st.button("🧪 Test Connection", type="primary"):
    with st.spinner("Testing connection..."):
        try:
            from sqlalchemy import create_engine, text
            
            config = st.secrets["mysql"]
            connection_string = (
                f"mysql+pymysql://{config['user']}:{config['password']}"
                f"@{config['host']}:{config['port']}/{config['database']}"
            )
            
            st.write("**Step 1:** Creating engine...")
            engine = create_engine(
                connection_string,
                connect_args={
                    'connect_timeout': 10,
                    'charset': 'utf8mb4'
                },
                echo=True  # Show SQL commands
            )
            st.success("✓ Engine created")
            
            st.write("**Step 2:** Attempting connection...")
            with engine.connect() as conn:
                st.success("✓ Connected to database!")
                
                st.write("**Step 3:** Running test query...")
                result = conn.execute(text("SELECT VERSION() as version, DATABASE() as db"))
                row = result.fetchone()
                
                st.success("✓ Query executed successfully!")
                st.json({
                    "MySQL Version": row[0],
                    "Current Database": row[1]
                })
                
                st.write("**Step 4:** Checking tables...")
                result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result.fetchall()]
                
                if tables:
                    st.success(f"✓ Found {len(tables)} tables")
                    st.write(tables)
                else:
                    st.warning("⚠️ No tables found - run schema creation script")
                
        except Exception as e:
            st.error(f"✗ Connection failed!")
            st.error(f"**Error:** {str(e)}")
            
            # Detailed error analysis
            error_str = str(e).lower()
            
            st.subheader("🔍 Error Analysis")
            
            if "access denied" in error_str:
                st.warning("**Issue: Access Denied**")
                st.write("- Check username and password")
                st.write("- Verify user has proper permissions")
                st.code("""
-- Run this on MySQL server:
GRANT ALL PRIVILEGES ON basketball_tracker.* TO 'your_user'@'%';
FLUSH PRIVILEGES;
                """)
            
            elif "unknown database" in error_str:
                st.warning("**Issue: Database doesn't exist**")
                st.write("- Database 'basketball_tracker' not found")
                st.write("- Run the schema creation script first")
                st.code("""
-- Run this on MySQL server:
CREATE DATABASE basketball_tracker;
                """)
            
            elif "can't connect" in error_str or "connection refused" in error_str:
                st.warning("**Issue: Cannot reach server**")
                st.write("Possible causes:")
                st.write("- MySQL server not running")
                st.write("- Firewall blocking port 3306")
                st.write("- Incorrect host address")
                st.write("- Server not accepting remote connections")
                
            elif "timeout" in error_str:
                st.warning("**Issue: Connection timeout**")
                st.write("- Server taking too long to respond")
                st.write("- Network issues")
                st.write("- Server overloaded")
            
            else:
                st.write("**Full error details:**")
                st.exception(e)

st.divider()

# Test 5: Network connectivity
st.header("Test 5: Network Test")
st.write("Test if the server is reachable (requires socket access)")

if st.button("🌐 Test Network"):
    try:
        import socket
        
        host = st.secrets["mysql"]["host"]
        port = int(st.secrets["mysql"]["port"])
        
        st.write(f"Attempting to reach {host}:{port}...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            st.success(f"✓ Port {port} is open on {host}")
        else:
            st.error(f"✗ Cannot reach {host}:{port}")
            st.write("This could mean:")
            st.write("- Firewall is blocking the connection")
            st.write("- MySQL server is not running")
            st.write("- Server is not accepting connections on this port")
    except Exception as e:
        st.error(f"Network test failed: {e}")

st.divider()

# Instructions
st.header("📚 Next Steps")

with st.expander("If connection is failing..."):
    st.markdown("""
    ### Check These Items:
    
    1. **Verify secrets file exists**
       - Location: `.streamlit/secrets.toml`
       - Format: See example above
       
    2. **Verify MySQL credentials**
       - Try connecting with MySQL Workbench or command line
       - Ensure user has proper permissions
       
    3. **Check MySQL server**
```bash
       # On server, check if MySQL is running
       sudo systemctl status mysql
       
       # Check if listening on port 3306
       sudo netstat -tlnp | grep 3306
```
       
    4. **Check firewall rules**
```bash
       # On server, allow port 3306
       sudo ufw allow 3306/tcp
```
       
    5. **Verify remote access is enabled**
```bash
       # Edit MySQL config
       sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
       
       # Change bind-address
       bind-address = 0.0.0.0
       
       # Restart MySQL
       sudo systemctl restart mysql
```
       
    6. **Create database and user**
```sql
       CREATE DATABASE IF NOT EXISTS basketball_tracker;
       CREATE USER 'bball_user'@'%' IDENTIFIED BY 'your_password';
       GRANT ALL PRIVILEGES ON basketball_tracker.* TO 'bball_user'@'%';
       FLUSH PRIVILEGES;
```
    """)

with st.expander("If deploying to Streamlit Cloud..."):
    st.markdown("""
    ### Streamlit Cloud Setup:
    
    1. **Add secrets in Streamlit Cloud dashboard**
       - Go to your app settings
       - Click "Secrets"
       - Paste your secrets.toml content
       
    2. **Whitelist Streamlit Cloud IPs**
       - Streamlit Cloud uses dynamic IPs
       - Your MySQL server must accept connections from any IP
       - Or use a service like PlanetScale that handles this
       
    3. **Check packages**
       - Ensure requirements.txt includes:
```
         streamlit>=1.28.0
         sqlalchemy>=2.0.0
         pymysql>=1.1.0
```
    """)
