import json
import sqlite3
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple

DATA_FILE = "inventario.json"


def _get_data_path(base_dir: Path | None = None) -> Path:
    """Return the path to the inventory JSON file.

    Args:
        base_dir: Optional base directory for the project.

    Returns:
        Full path to the inventory JSON file.
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / DATA_FILE


def cargar_datos(base_dir: Path | None = None) -> Dict[str, Dict[str, Any]]:
    """Load inventory data from JSON storage.

    Args:
        base_dir: Optional base directory for the project.

    Returns:
        Dictionary of products keyed by ID, or empty on failure.
    """
    path = _get_data_path(base_dir)
    try:
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except FileNotFoundError:
        return {}
    except JSONDecodeError:
        return {}
    except OSError:
        return {}

    return raw if isinstance(raw, dict) else {}


def guardar_datos(datos: Dict[str, Dict[str, Any]], base_dir: Path | None = None) -> None:
    """Persist inventory data to JSON storage.

    Args:
        datos: Dictionary of products keyed by ID.
        base_dir: Optional base directory for the project.

    Returns:
        None.
    """
    path = _get_data_path(base_dir)
    try:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(datos, handle, indent=2, ensure_ascii=False)
    except OSError:
        pass


def guardar_ticket(contenido_ticket: str, base_dir: Path | None = None) -> Path:
    """Save a ticket to a unique file under the tickets folder.

    Args:
        contenido_ticket: Ticket content to save.
        base_dir: Optional base directory for the project.

    Returns:
        Path to the created ticket file.
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[1]
    tickets_dir = base_dir / "tickets"
    tickets_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    ticket_path = tickets_dir / f"ticket_{timestamp}.txt"
    try:
        ticket_path.write_text(contenido_ticket, encoding="utf-8")
    except OSError:
        pass
    return ticket_path


class DatabaseManager:
    """Manage SQLite persistence for inventory data."""

    def __init__(self, db_path: str | Path) -> None:
        """Initialize the database connection and ensure tables exist.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self) -> None:
        """Create base tables if they do not exist."""
        create_table_sql = (
            "CREATE TABLE IF NOT EXISTS productos ("
            "id INTEGER PRIMARY KEY, "
            "nombre TEXT NOT NULL, "
            "precio REAL NOT NULL, "
            "stock INTEGER NOT NULL"
            ");"
        )
        try:
            with self.conn:
                self.conn.execute(create_table_sql)
        except sqlite3.Error:
            pass

    def obtener_alertas_stock(self, umbral: int) -> List[Tuple[Any, ...]]:
        """Return products with stock less than or equal to the threshold.

        Args:
            umbral: Stock threshold for alerts.

        Returns:
            List of tuples with product records.
        """
        query = "SELECT id, nombre, precio, stock FROM productos WHERE stock <= ?"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                try:
                    cursor.execute(query, (umbral,))
                    return cursor.fetchall()
                finally:
                    cursor.close()
        except sqlite3.Error:
            return []

    def obtener_productos(self) -> List[Tuple[Any, ...]]:
        """Return all products from the database.

        Returns:
            List of tuples with product records.
        """
        query = "SELECT id, nombre, precio, stock FROM productos"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                try:
                    cursor.execute(query)
                    return cursor.fetchall()
                finally:
                    cursor.close()
        except sqlite3.Error:
            return []

    def registrar_venta_transaccional(self, producto_id: int, cantidad: int) -> Literal[
        "ok", "not_found", "insufficient", "invalid", "error"
    ]:
        """Register a sale and update stock atomically.

        Args:
            producto_id: Product ID.
            cantidad: Units sold.

        Returns:
            Status string describing the result.
        """
        if cantidad <= 0:
            return "invalid"

        select_sql = "SELECT stock FROM productos WHERE id = ?"
        update_sql = "UPDATE productos SET stock = ? WHERE id = ?"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                try:
                    cursor.execute(select_sql, (producto_id,))
                    row = cursor.fetchone()
                    if row is None:
                        return "not_found"
                    stock = int(row[0])
                    if stock < cantidad:
                        return "insufficient"
                    nuevo_stock = stock - cantidad
                    cursor.execute(update_sql, (nuevo_stock, producto_id))
                    return "ok"
                finally:
                    cursor.close()
        except sqlite3.Error:
            return "error"

    def close(self) -> None:
        """Close the database connection."""
        try:
            self.conn.close()
        except sqlite3.Error:
            pass