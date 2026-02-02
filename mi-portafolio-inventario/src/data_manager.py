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

    def obtener_siguiente_id(self) -> int:
        """Return the next available product ID.

        Returns:
            Next integer ID starting from 1.
        """
        query = "SELECT MAX(id) FROM productos"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                try:
                    cursor.execute(query)
                    row = cursor.fetchone()
                    max_id = int(row[0]) if row and row[0] is not None else 0
                    return max_id + 1
                finally:
                    cursor.close()
        except sqlite3.Error:
            return 1

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

    def insertar_producto(self, producto_id: int, nombre: str, precio: float, stock: int) -> Literal[
        "ok", "exists", "invalid", "error"
    ]:
        """Insert a new product if the ID does not exist.

        Args:
            producto_id: Product ID.
            nombre: Product name.
            precio: Unit price.
            stock: Initial stock.

        Returns:
            Status string describing the result.
        """
        if producto_id <= 0 or not nombre or precio < 0 or stock < 0:
            return "invalid"

        check_sql = "SELECT 1 FROM productos WHERE id = ?"
        insert_sql = (
            "INSERT INTO productos (id, nombre, precio, stock) "
            "VALUES (?, ?, ?, ?)"
        )
        try:
            with self.conn:
                cursor = self.conn.cursor()
                try:
                    cursor.execute(check_sql, (producto_id,))
                    if cursor.fetchone() is not None:
                        return "exists"
                    cursor.execute(insert_sql, (producto_id, nombre, precio, stock))
                    return "ok"
                finally:
                    cursor.close()
        except sqlite3.Error:
            return "error"

    def eliminar_producto(self, producto_id: int) -> Literal["ok", "not_found", "error"]:
        """Delete a product by ID.

        Args:
            producto_id: Product ID.

        Returns:
            Status string describing the result.
        """
        delete_sql = "DELETE FROM productos WHERE id = ?"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                try:
                    cursor.execute(delete_sql, (producto_id,))
                    if cursor.rowcount == 0:
                        return "not_found"
                    return "ok"
                finally:
                    cursor.close()
        except sqlite3.Error:
            return "error"

    def eliminar_producto_por_nombre(self, nombre: str) -> Literal["ok", "not_found", "error"]:
        """Delete a product by name.

        Args:
            nombre: Product name.

        Returns:
            Status string describing the result.
        """
        if not nombre:
            return "not_found"
        delete_sql = "DELETE FROM productos WHERE LOWER(nombre) = LOWER(?)"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                try:
                    cursor.execute(delete_sql, (nombre,))
                    if cursor.rowcount == 0:
                        return "not_found"
                    return "ok"
                finally:
                    cursor.close()
        except sqlite3.Error:
            return "error"

    def seed_from_json(self, json_path: Path) -> bool:
        """Seed database from a JSON file if data is available.

        Args:
            json_path: Path to the JSON inventory file.

        Returns:
            True if any rows were inserted, False otherwise.
        """
        if not json_path.exists():
            return False

        try:
            raw = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, JSONDecodeError):
            return False

        if not isinstance(raw, dict) or not raw:
            return False

        rows = []
        for pid, item in raw.items():
            if not isinstance(item, dict):
                continue
            try:
                id_val = int(item.get("id", pid))
                nombre = str(item.get("nombre", "")).strip()
                precio = float(item.get("precio", 0))
                stock = int(item.get("stock", 0))
            except (TypeError, ValueError):
                continue
            if not nombre:
                continue
            rows.append((id_val, nombre, precio, stock))

        if not rows:
            return False

        insert_sql = (
            "INSERT OR REPLACE INTO productos (id, nombre, precio, stock) "
            "VALUES (?, ?, ?, ?)"
        )
        try:
            with self.conn:
                self.conn.executemany(insert_sql, rows)
            return True
        except sqlite3.Error:
            return False

    def close(self) -> None:
        """Close the database connection."""
        try:
            self.conn.close()
        except sqlite3.Error:
            pass