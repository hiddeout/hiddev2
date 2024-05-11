import aiosqlite

class DatabaseManager:
    def __init__(self, *, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    async def setup_database(self):
        # Ensure the 'afk' table is created with the necessary columns
        await self.connection.execute("""
        CREATE TABLE IF NOT EXISTS afk (
            guild_id INTEGER,
            user_id INTEGER,
            reason TEXT,
            afk_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  # Ensure this column is included
            PRIMARY KEY (guild_id, user_id)
        )
        """)
        await self.connection.commit()

    async def add_warn(self, user_id: int, server_id: int, moderator_id: int, reason: str) -> int:
        """
        This function will add a warn to the database.
        """
        warn_id = await self.connection.execute_fetchval(
            "INSERT INTO warns(user_id, server_id, moderator_id, reason) VALUES (?, ?, ?, ?) RETURNING id",
            (user_id, server_id, moderator_id, reason)
        )
        await self.connection.commit()
        return warn_id

    async def remove_warn(self, warn_id: int, user_id: int, server_id: int) -> int:
        """
        This function will remove a warn from the database.
        """
        await self.connection.execute(
            "DELETE FROM warns WHERE id=? AND user_id=? AND server_id=?",
            (warn_id, user_id, server_id)
        )
        await self.connection.commit()
        remaining_warnings = await self.connection.execute_fetchval(
            "SELECT COUNT(*) FROM warns WHERE user_id=? AND server_id=?",
            (user_id, server_id)
        )
        return remaining_warnings

    async def get_warnings(self, user_id: int, server_id: int) -> list:
        """
        This function will get all the warnings of a user.
        """
        result = await self.connection.execute_fetchall(
            "SELECT id, moderator_id, reason, strftime('%Y-%m-%d %H:%M:%S', created_at) as created_at FROM warns WHERE user_id=? AND server_id=?",
            (user_id, server_id)
        )
        return result
