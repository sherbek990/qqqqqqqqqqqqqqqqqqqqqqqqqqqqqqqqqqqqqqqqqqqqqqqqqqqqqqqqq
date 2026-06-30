import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT DEFAULT '',
                    full_name TEXT DEFAULT '',
                    joined_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT UNIQUE NOT NULL,
                    channel_name TEXT NOT NULL,
                    channel_link TEXT NOT NULL,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_user(self, user_id: int, username: str, full_name: str):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO users (user_id, username, full_name)
                VALUES (?, ?, ?)
            """, (user_id, username, full_name))
            conn.commit()

    def get_all_users(self) -> list:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT user_id FROM users").fetchall()
        return [{"user_id": row[0]} for row in rows]

    def add_channel(self, channel_id: str, channel_name: str, channel_link: str):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO channels (channel_id, channel_name, channel_link)
                VALUES (?, ?, ?)
            """, (channel_id, channel_name, channel_link))
            conn.commit()

    def remove_channel(self, db_id: int):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM channels WHERE id = ?", (db_id,))
            conn.commit()

    def get_channels(self) -> list:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, channel_id, channel_name, channel_link FROM channels"
            ).fetchall()
        return [
            {"id": r[0], "channel_id": r[1], "channel_name": r[2], "channel_link": r[3]}
            for r in rows
        ]

    def get_stats(self) -> dict:
        with self._get_conn() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            total_channels = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
        return {"total_users": total_users, "total_channels": total_channels}
