import sqlite3

connection = sqlite3.connect("bloxpulse.db")
cursor = connection.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS notifications (universeId text, key text, notificationId text, time real, message text, api_key text)")

def insert(universeId: str, data: dict):
    if not type(data) is dict: 
        return False

    cursor.execute("INSERT OR IGNORE INTO notifications VALUES (?, ?, ?, ?, ?, ?)", (universeId, data.get("key"),data.get("notificationId"), data.get("time"), data.get("message"), data.get("api_key")))
    connection.commit()

    return True

def remove(universeId: str, data: dict):
    if not type(data) is dict: 
        return False

    cursor.execute(
        "DELETE FROM notifications WHERE universeId = ? AND key = ? AND time = ?",
        (universeId, data.get("key"), data.get("time"))
    )
    connection.commit()
    return True