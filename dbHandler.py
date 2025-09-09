import sqlite3
import time
import logging
from threading import Lock
from collections import deque

DB_PATH = "bloxpulse.db"

# Configure logging
logging.basicConfig(
    filename='bloxpulse.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Connection pool
MAX_POOL_SIZE = 10
connection_pool = deque(maxlen=MAX_POOL_SIZE)
pool_lock = Lock()

# Simple cache for getDue results
CACHE_TTL = 1  # 1 second cache
last_cache_time = 0
cached_due = []
cache_lock = Lock()

def init_db():
    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        connection.execute("PRAGMA journal_mode=WAL;")
        connection.execute("PRAGMA synchronous=NORMAL;")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS notifications ("
            "universeId TEXT, key TEXT, notificationId TEXT, "
            "time REAL, message TEXT, api_key TEXT)"
        )

def get_conn():
    retries = 3
    while retries > 0:
        try:
            # Try to get a connection from the pool
            with pool_lock:
                if connection_pool:
                    conn = connection_pool.popleft()
                    try:
                        # Test if connection is still good
                        conn.execute("SELECT 1")
                        return conn
                    except sqlite3.Error:
                        # Connection is bad, create new one
                        conn.close()
                
                # Create new connection
                conn = sqlite3.connect(DB_PATH, timeout=20)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA busy_timeout=20000;")
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                return conn
                
        except sqlite3.OperationalError as e:
            retries -= 1
            if retries == 0:
                logging.error(f"Failed to get database connection: {str(e)}")
                raise e
            time.sleep(1)  # Wait before retrying
    return None

def return_conn(conn):
    """Return a connection to the pool"""
    try:
        if conn is not None:
            with pool_lock:
                if len(connection_pool) < MAX_POOL_SIZE:
                    connection_pool.append(conn)
                    return
        # If pool is full or conn is None, close it
        if conn is not None:
            conn.close()
    except Exception as e:
        logging.error(f"Error returning connection to pool: {str(e)}")
        if conn is not None:
            conn.close()

def getDue(now_ts):
    if now_ts is None:
        now_ts = time.time()  # current UTC seconds
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "SELECT * FROM notifications WHERE time <= ? ORDER BY time ASC",
                (now_ts,),
            )
            return [dict(row) for row in cur]
    except sqlite3.Error:
        return []

def insert(universeId: str, data: dict):
    if not isinstance(data, dict): 
        return False

    retries = 3
    conn = None
    while retries > 0:
        try:
            conn = get_conn()
            if conn is None:
                return False
            
            conn.execute(
                "INSERT OR IGNORE INTO notifications VALUES (?, ?, ?, ?, ?, ?)", 
                (
                    universeId, 
                    data.get("key"),
                    data.get("notificationId"), 
                    data.get("time"), 
                    data.get("message"), 
                    data.get("api_key")
                )
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            retries -= 1
            if retries == 0:
                logging.error(f"Database insert error after 3 retries: {str(e)}")
                return False
            time.sleep(1)  # Wait before retrying
        finally:
            if conn:
                return_conn(conn)
    return False

def remove(universeId: str, data: dict):
    if not isinstance(data, dict): 
        return False

    retries = 3
    conn = None
    while retries > 0:
        try:
            conn = get_conn()
            if conn is None:
                return False
                
            conn.execute(
                "DELETE FROM notifications WHERE universeId = ? AND key = ? AND time = ?",
                (universeId, data.get("key"), data.get("time"))
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            retries -= 1
            if retries == 0:
                logging.error(f"Database remove error after 3 retries: {str(e)}")
                return False
            time.sleep(1)  # Wait before retrying
        finally:
            if conn:
                return_conn(conn)
    return False

def getAll() -> list[dict]:
    global last_cache_time, cached_due
    current_time = time.time()
    
    # Check if we can use cached results
    with cache_lock:
        if current_time - last_cache_time <= CACHE_TTL:
            return cached_due

    retries = 3
    conn = None
    while retries > 0:
        try:
            conn = get_conn()
            if conn is None:
                return []
            
            # Iterate the cursor directly to avoid keeping a second copy in memory
            cur = conn.execute(
                "SELECT * FROM notifications WHERE time <= ? ORDER BY time ASC", 
                (current_time,)
            )
            result = [dict(row) for row in cur]
            
            # Update cache
            with cache_lock:
                cached_due = result
                last_cache_time = current_time
            
            return result
        except sqlite3.Error as e:
            retries -= 1
            if retries == 0:
                logging.error(f"Database getAll error after 3 retries: {str(e)}")
                return []
            time.sleep(1)  # Wait before retrying
        finally:
            if conn:
                return_conn(conn)
    return []
