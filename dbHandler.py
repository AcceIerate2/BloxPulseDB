import sqlite3
import time

DB_PATH = "bloxpulse.db"

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
    conn = sqlite3.connect(DB_PATH, timeout=10)  # waits up to 10s if busy
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout=10000;")  # extra safety
    except Exception:
        pass
    return conn

def getDue(now_ts: float | None = None) -> list[dict]:
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
    if not type(data) is dict: 
        return False

    try:
        with get_conn() as connection:
            connection.execute("INSERT OR IGNORE INTO notifications VALUES (?, ?, ?, ?, ?, ?)", (universeId, data.get("key"),data.get("notificationId"), data.get("time"), data.get("message"), data.get("api_key")))
        return True
    except sqlite3.Error:
        return False

def remove(universeId: str, data: dict):
    if not type(data) is dict: 
        return False

    try:
        with get_conn() as connection:
            connection.execute(
                "DELETE FROM notifications WHERE universeId = ? AND key = ? AND time = ?",
                (universeId, data.get("key"), data.get("time"))
            )
        return True
    except sqlite3.Error:
        return False

def getAll() -> list[dict]:
    try:
        with get_conn() as conn:
            # Iterate the cursor directly to avoid keeping a second copy in memory
            cur = conn.execute("SELECT * FROM notifications WHERE time <= ? ORDER BY time ASC", (time.time(),))
            return [dict(row) for row in cur]
    except sqlite3.Error:
        return []
