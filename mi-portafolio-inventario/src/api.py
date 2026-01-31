from pathlib import Path
import sys
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from data_manager import DatabaseManager


class ProductoResponse(BaseModel):
    """Schema for product responses."""

    id: int
    nombre: str
    precio: float
    stock: int


class VentaRequest(BaseModel):
    """Schema for sales requests."""

    producto_id: int
    cantidad: int


base_dir = Path(__file__).resolve().parents[1]
db_path = base_dir / "data" / "inventario.db"
db = DatabaseManager(db_path)

app = FastAPI(
    title="Inventario API",
    version="1.0.0",
    description="API REST para gestionar inventario y ventas.",
)


@app.get(
    "/productos",
    response_model=List[ProductoResponse],
    summary="Listar productos",
    description="Retorna todos los productos del inventario.",
)
def get_productos() -> List[ProductoResponse]:
    """Return the full list of products."""
    try:
        rows = db.obtener_productos()
        return [
            ProductoResponse(id=row[0], nombre=row[1], precio=row[2], stock=row[3])
            for row in rows
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Error interno al obtener productos.",
        ) from exc


@app.get(
    "/productos/alertas",
    response_model=List[ProductoResponse],
    summary="Alertas de stock",
    description="Retorna productos con stock menor o igual al umbral.",
)
def get_alertas(umbral: int = 5) -> List[ProductoResponse]:
    """Return products with stock lower than or equal to threshold."""
    try:
        rows = db.obtener_alertas_stock(umbral)
        return [
            ProductoResponse(id=row[0], nombre=row[1], precio=row[2], stock=row[3])
            for row in rows
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Error interno al obtener alertas.",
        ) from exc


@app.post(
    "/ventas",
    summary="Registrar venta",
    description="Registra una venta y descuenta stock si hay disponibilidad.",
)
def post_venta(payload: VentaRequest) -> dict:
    """Register a sale transaction."""
    try:
        resultado = db.registrar_venta_transaccional(
            producto_id=payload.producto_id,
            cantidad=payload.cantidad,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Error interno al registrar la venta.",
        ) from exc

    if resultado == "not_found":
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    if resultado == "insufficient":
        raise HTTPException(status_code=400, detail="Stock insuficiente.")
    if resultado == "invalid":
        raise HTTPException(status_code=400, detail="Cantidad invalida.")
    if resultado != "ok":
        raise HTTPException(status_code=500, detail="No se pudo registrar la venta.")

    return {"status": "ok", "message": "Venta registrada correctamente."}