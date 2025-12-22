"""PostgreSQL connection manager for Supabase."""

from __future__ import annotations
import psycopg2
from psycopg2 import pool
from app.core.config import Settings


class PostgresManager:
    """Manages PostgreSQL connection pool for read operations."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._pool: pool.SimpleConnectionPool | None = None

    def init_pool(self, min_conn: int = 1, max_conn: int = 10) -> None:
        """Initialize the connection pool."""
        if self._pool is None:
            self._pool = pool.SimpleConnectionPool(
                min_conn,
                max_conn,
                host=self._settings.pg_host,
                database=self._settings.pg_database,
                user=self._settings.pg_user,
                password=self._settings.pg_password,
                port=self._settings.pg_port,
                sslmode=self._settings.pg_sslmode,
            )

    def get_connection(self):
        """Get a connection from the pool."""
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized. Call init_pool() first.")
        return self._pool.getconn()

    def release_connection(self, conn) -> None:
        """Return a connection to the pool."""
        if self._pool is not None:
            self._pool.putconn(conn)

    def close_all(self) -> None:
        """Close all connections in the pool."""
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None
