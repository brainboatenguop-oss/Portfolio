from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Producto:
    """Representa un producto dentro del inventario.

    Attributes:
        id: Identificador unico del producto.
        nombre: Nombre del producto.
        precio: Precio unitario del producto.
        stock: Unidades disponibles.
    """

    id: str
    nombre: str
    precio: float
    stock: int

    def __post_init__(self) -> None:
        """Validate product data after initialization.

        Raises:
            ValueError: If any attribute is invalid.
        """
        if not self.id.strip():
            raise ValueError("El ID no puede estar vacio.")
        if not self.nombre.strip():
            raise ValueError("El nombre no puede estar vacio.")
        if self.precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        if self.stock < 0:
            raise ValueError("El stock no puede ser negativo.")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the product to a JSON-friendly dictionary.

        Returns:
            Dictionary representation of the product.
        """
        return {
            "id": self.id,
            "nombre": self.nombre,
            "precio": self.precio,
            "stock": self.stock,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Producto":
        """Create a Producto instance from a dictionary.

        Args:
            data: Dictionary with keys id, nombre, precio, stock.

        Returns:
            Producto instance.
        """
        return Producto(
            id=str(data.get("id", "")).strip(),
            nombre=str(data.get("nombre", "")).strip(),
            precio=float(data.get("precio", 0)),
            stock=int(data.get("stock", 0)),
        )


class InventarioManager:
    """Gestiona el inventario de productos con operaciones basicas.

    Attributes:
        productos: Diccionario de productos indexado por ID.
    """

    def __init__(self, productos: Dict[str, Producto] | None = None) -> None:
        """Initialize the inventory manager.

        Args:
            productos: Optional dictionary of products.
        """
        self.productos: Dict[str, Producto] = productos or {}

    def anadir_producto(self, producto: Producto) -> bool:
        """Add a product to the inventory.

        Args:
            producto: Producto instance to add.

        Returns:
            True if added, False if the ID already exists.
        """
        if producto.id in self.productos:
            return False
        self.productos[producto.id] = producto
        return True

    def actualizar_stock(self, producto_id: str, cantidad: int) -> bool:
        """Update stock for a product by a delta value.

        Args:
            producto_id: ID of the product to update.
            cantidad: Units to add (positive) or remove (negative).

        Returns:
            True if updated, False if invalid or not found.
        """
        producto = self.productos.get(producto_id)
        if producto is None:
            return False
        nuevo_stock = producto.stock + cantidad
        if nuevo_stock < 0:
            return False
        producto.stock = nuevo_stock
        return True

    def obtener_lista(self) -> List[Producto]:
        """Return a sorted list of products.

        Returns:
            List of Producto instances sorted by name and ID.
        """
        return sorted(
            self.productos.values(),
            key=lambda item: (item.nombre.lower(), item.id),
        )

    def generar_recibo(self, id_p: str, cantidad: int, precio_total: float) -> str:
        """Generate a formatted purchase receipt for a product.

        Args:
            id_p: Product ID.
            cantidad: Units sold.
            precio_total: Total price for the transaction.

        Returns:
            Formatted receipt as a string.
        """
        producto = self.productos.get(id_p)
        nombre = producto.nombre if producto else "Producto desconocido"
        precio_unitario = producto.precio if producto else 0.0

        return (
            "==============================\n"
            "     TICKET DE COMPRA\n"
            "==============================\n"
            f"ID Producto : {id_p}\n"
            f"Nombre      : {nombre}\n"
            f"Cantidad    : {cantidad}\n"
            f"Precio Unit : {precio_unitario:.2f}\n"
            "------------------------------\n"
            f"TOTAL       : {precio_total:.2f}\n"
            "==============================\n"
            "Gracias por su compra.\n"
        )

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert inventory to a serializable dictionary.

        Returns:
            Dictionary of product data keyed by ID.
        """
        return {pid: producto.to_dict() for pid, producto in self.productos.items()}

    @staticmethod
    def from_dict(data: Dict[str, Dict[str, Any]]) -> "InventarioManager":
        """Create an inventory manager from raw dictionary data.

        Args:
            data: Dictionary of product data keyed by ID.

        Returns:
            InventarioManager instance.
        """
        productos: Dict[str, Producto] = {}
        for pid, raw in data.items():
            if not isinstance(raw, dict):
                continue
            raw = dict(raw)
            raw.setdefault("id", pid)
            try:
                producto = Producto.from_dict(raw)
            except ValueError:
                continue
            productos[producto.id] = producto
        return InventarioManager(productos)
