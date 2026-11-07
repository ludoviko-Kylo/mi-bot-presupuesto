import sqlite3
import threading
from contextlib import contextmanager
from typing import Generator, Any, Optional
import config

_lock = threading.Lock()

def is_postgres() -> bool:
    """Verifica si la base de datos configurada es PostgreSQL / Supabase en la nube."""
    url = (getattr(config, "DATABASE_URL", None) or "").strip().lower()
    return url.startswith("postgresql://") or url.startswith("postgres://")

def get_normalized_pg_url() -> str:
    """Convierte prefijos postgres:// a postgresql:// para compatibilidad con psycopg2."""
    url = (getattr(config, "DATABASE_URL", None) or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url

class PgCursorWrapper:
    """
    Wrapper para el cursor de psycopg2 que unifica la interfaz con la de sqlite3:
    1. Traduce marcadores de parámetros '?' a '%s'.
    2. Emula cursor.lastrowid en sentencias INSERT mediante RETURNING id.
    """
    def __init__(self, raw_cursor):
        self._cursor = raw_cursor
        self.lastrowid = None

    def execute(self, query: str, params: Any = None):
        # Convertir placeholders '?' a '%s' para PostgreSQL
        pg_query = query.replace("?", "%s")

        is_insert = pg_query.strip().upper().startswith("INSERT INTO")
        has_returning = "RETURNING" in pg_query.upper()

        if is_insert and not has_returning and "transactions" in pg_query:
            pg_query_with_returning = pg_query.rstrip(";\n ") + " RETURNING id;"
            try:
                if params is not None:
                    self._cursor.execute(pg_query_with_returning, params)
                else:
                    self._cursor.execute(pg_query_with_returning)
                row = self._cursor.fetchone()
                if row:
                    self.lastrowid = row["id"] if isinstance(row, dict) else row[0]
                return self
            except Exception:
                # Si fallara la cláusula RETURNING, reintentar la consulta original
                pass

        if params is not None:
            self._cursor.execute(pg_query, params)
        else:
            self._cursor.execute(pg_query)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        return self._cursor.fetchmany(size)

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def __getattr__(self, name):
        return getattr(self._cursor, name)

def get_connection():
    """Establece conexión a PostgreSQL (si DATABASE_URL está definida) o SQLite local."""
    if is_postgres():
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError:
            raise ImportError(
                "La variable DATABASE_URL está configurada para PostgreSQL, pero falta la librería psycopg2.\n"
                "Instálala con: pip install psycopg2-binary"
            )
        dsn = get_normalized_pg_url()
        # Agregar sslmode=require si nos conectamos a proveedores cloud como Supabase o Neon
        conn_kwargs = {"cursor_factory": RealDictCursor}
        if "sslmode" not in dsn and any(host in dsn for host in ("supabase", "render", "railway", "neon")):
            conn_kwargs["sslmode"] = "require"
        return psycopg2.connect(dsn, **conn_kwargs)
    else:
        conn = sqlite3.connect(getattr(config, "DATABASE_PATH", "presupuesto.db"), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

@contextmanager
def get_db_cursor() -> Generator[Any, None, None]:
    """Context manager seguro para ejecutar transacciones en SQLite o PostgreSQL."""
    with _lock:
        conn = get_connection()
        raw_cursor = conn.cursor()
        cursor = PgCursorWrapper(raw_cursor) if is_postgres() else raw_cursor
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                raw_cursor.close()
            except Exception:
                pass
            conn.close()

def init_db() -> None:
    """Crea las tablas e índices si no existen tanto en PostgreSQL como en SQLite."""
    with get_db_cursor() as cursor:
        if is_postgres():
            # Esquema optimizado para PostgreSQL / Supabase
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    currency TEXT DEFAULT '$',
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    type VARCHAR(10) NOT NULL CHECK(type IN ('gasto', 'ingreso')),
                    amount NUMERIC(12, 2) NOT NULL CHECK(amount > 0),
                    category TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
                ON transactions(user_id, created_at);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_user_type 
                ON transactions(user_id, type);
            """)
        else:
            # Esquema estándar para SQLite local
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    currency TEXT DEFAULT '$',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('gasto', 'ingreso')),
                    amount REAL NOT NULL CHECK(amount > 0),
                    category TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_user_date 
                ON transactions(user_id, created_at);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_user_type 
                ON transactions(user_id, type);
            """)

def get_or_create_user(user_id: int, username: str = "", first_name: str = "") -> dict:
    """Obtiene un usuario o lo registra si es nuevo (compatible con PostgreSQL y SQLite)."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            # Actualizar datos de usuario si cambiaron
            cursor.execute(
                "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                (username or "", first_name or "", user_id)
            )
            return dict(row)

        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, currency) VALUES (?, ?, ?, ?)",
            (user_id, username or "", first_name or "", getattr(config, "DEFAULT_CURRENCY", "$"))
        )
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return dict(cursor.fetchone())
