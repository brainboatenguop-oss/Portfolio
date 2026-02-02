from pathlib import Path
import sys
from typing import List, Optional
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

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

    producto_id: int = Field(..., gt=0, description="ID del producto")
    cantidad: int = Field(..., gt=0, description="Unidades a vender")


class ProductoCreateRequest(BaseModel):
    """Schema for product creation."""

    id: int = Field(..., gt=0, description="ID del producto")
    nombre: str = Field(..., min_length=1, description="Nombre del producto")
    precio: float = Field(..., ge=0, description="Precio unitario")
    stock: int = Field(..., ge=0, description="Stock inicial")


class AIRequest(BaseModel):
    """Schema for AI requests."""

    pregunta: str = Field(..., min_length=1, description="Pregunta para la IA")


class AIResponse(BaseModel):
    """Schema for AI responses."""

    respuesta: str
    accion: Optional[str] = None
    resultados: Optional[List[str]] = None


base_dir = Path(__file__).resolve().parents[1]
db_path = base_dir / "data" / "inventario.db"
json_path = base_dir / "data" / "inventario.json"
db = DatabaseManager(db_path)

app = FastAPI(
    title="Inventario API",
    version="1.0.0",
    description="API REST para gestionar inventario y ventas.",
)


@app.on_event("startup")
def startup() -> None:
    """Ensure database has initial data if available."""
    try:
        if not db.obtener_productos():
            db.seed_from_json(json_path)
    except Exception:
        pass


@app.on_event("shutdown")
def shutdown() -> None:
    """Close database connection on shutdown."""
    db.close()


def _build_inventory_context(limit: int = 50) -> str:
    """Build a short inventory context for AI prompts."""
    rows = db.obtener_productos()
    rows = rows[:limit]
    if not rows:
        return "Inventario vacio."
    lines = ["Inventario (id, nombre, precio, stock):"]
    for row in rows:
        lines.append(f"- {row[0]} | {row[1]} | {row[2]:.2f} | {row[3]}")
    return "\n".join(lines)


def _ask_ollama(prompt: str, model: str = "llama3") -> str:
    """Send a prompt to Ollama and return the response."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        "http://127.0.0.1:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            return str(parsed.get("response", "")).strip()
    except (HTTPError, URLError, json.JSONDecodeError):
        return "No se pudo contactar con Ollama. Verifica que este ejecutandose."


def _parse_ai_action(text: str) -> Optional[dict]:
    """Parse a JSON action object from AI response."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if "action" not in data or "payload" not in data:
        return None
    return data


def _execute_ai_action(action_obj: dict) -> List[str]:
    """Execute AI action against the database and return result messages."""
    action = str(action_obj.get("action", "")).upper()
    payload = action_obj.get("payload", {})
    items = payload.get("items", []) if isinstance(payload, dict) else []
    results: List[str] = []

    if action == "ADD_PRODUCT":
        for item in items:
            if not isinstance(item, dict):
                continue
            nombre = str(item.get("name", "")).strip()
            precio = float(item.get("price", 0) or 0)
            stock = int(item.get("stock", 0) or 0)
            nuevo_id = db.obtener_siguiente_id()
            estado = db.insertar_producto(nuevo_id, nombre, precio, stock)
            results.append(f"ADD {nombre}: {estado}")
        return results

    if action == "DELETE_PRODUCT":
        for item in items:
            if not isinstance(item, dict):
                continue
            if "id" in item and str(item.get("id")).isdigit():
                estado = db.eliminar_producto(int(item.get("id")))
                results.append(f"DEL {item.get('id')}: {estado}")
            else:
                nombre = str(item.get("name", "")).strip()
                estado = db.eliminar_producto_por_nombre(nombre)
                results.append(f"DEL {nombre}: {estado}")
        return results

    return ["Accion no soportada"]


@app.get(
    "/",
    summary="Panel unificado",
    description="Pagina unica con inventario, alertas y registro de ventas.",
    response_class=HTMLResponse,
)
def root() -> HTMLResponse:
    """Return a single-page dashboard for the API."""
    html = """
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Inventario - Panel Unificado</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 24px; background:#f6f7fb; color:#1f2937; }
        header { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px; }
        h1 { margin: 0 0 8px 0; }
        section { background:#fff; padding:16px; border-radius:10px; box-shadow:0 1px 6px rgba(0,0,0,0.08); margin:16px 0; }
        table { width:100%; border-collapse: collapse; }
        th, td { padding:8px; border-bottom:1px solid #e5e7eb; text-align:left; }
        .row { display:flex; gap:12px; flex-wrap:wrap; align-items:center; }
        input, textarea { padding:8px; border:1px solid #d1d5db; border-radius:6px; }
        textarea { width:100%; min-height:90px; }
        button { padding:8px 12px; border:none; border-radius:6px; background:#2563eb; color:#fff; cursor:pointer; }
        button:disabled { background:#93c5fd; cursor:not-allowed; }
        .muted { color:#6b7280; font-size: 12px; }
        .badge { display:inline-block; padding:2px 8px; border-radius:999px; background:#fee2e2; color:#991b1b; font-size:12px; }
        .ok { background:#dcfce7; color:#166534; }
        .msg { margin-top:8px; }
        .ai-box { background:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:8px; }
      </style>
    </head>
    <body>
      <header>
        <div>
          <h1>Panel Unificado - Inventario</h1>
          <div class="muted">API local activa en 127.0.0.1:8000</div>
        </div>
        <div id="status" class="badge ok">OK</div>
      </header>

      <section>
        <h2>Inventario</h2>
        <div class="muted">Listado completo de productos.</div>
        <table id="tabla-productos">
          <thead>
            <tr><th>ID</th><th>Nombre</th><th>Precio</th><th>Stock</th><th>Acciones</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </section>

      <section>
        <h2>Agregar producto</h2>
        <div class="row">
          <input id="nuevo-id" type="number" min="1" placeholder="ID" />
          <input id="nuevo-nombre" type="text" placeholder="Nombre" />
          <input id="nuevo-precio" type="number" min="0" step="0.01" placeholder="Precio" />
          <input id="nuevo-stock" type="number" min="0" placeholder="Stock" />
          <button onclick="crearProducto()">Agregar</button>
        </div>
        <div id="crear-msg" class="muted msg"></div>
      </section>

      <section>
        <h2>Alertas de stock</h2>
        <div class="row">
          <input id="umbral" type="number" min="0" value="5" />
          <button onclick="cargarAlertas()">Actualizar alertas</button>
        </div>
        <table id="tabla-alertas">
          <thead>
            <tr><th>ID</th><th>Nombre</th><th>Precio</th><th>Stock</th></tr>
          </thead>
          <tbody></tbody>
        </table>
      </section>

      <section>
        <h2>Registrar venta</h2>
        <div class="row">
          <input id="venta-id" type="number" min="1" placeholder="ID producto" />
          <input id="venta-cantidad" type="number" min="1" placeholder="Cantidad" />
          <button onclick="registrarVenta()">Vender</button>
        </div>
        <div id="venta-msg" class="muted msg"></div>
      </section>

      <section>
        <h2>Asistente IA (Ollama)</h2>
        <div class="ai-box">
          <div class="muted">Ejemplos: "Añade Fanta y Aquarius a 1.99" o "Elimina Coca Cola".</div>
          <textarea id="ai-pregunta" placeholder="Escribe tu pedido..."></textarea>
          <button onclick="preguntarIA()">Procesar con IA</button>
          <div id="ai-respuesta" class="msg"></div>
        </div>
      </section>

      <section>
        <h2>Documentacion</h2>
        <div class="row">
          <a href="/docs">Swagger UI</a>
          <a href="/openapi.json">OpenAPI JSON</a>
        </div>
      </section>

      <script>
        async function cargarProductos() {
          const res = await fetch('/productos');
          const data = await res.json();
          const body = document.querySelector('#tabla-productos tbody');
          body.innerHTML = '';
          data.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>${p.id}</td>
              <td>${p.nombre}</td>
              <td>${p.precio.toFixed(2)}</td>
              <td>${p.stock}</td>
              <td><button onclick="eliminarProducto(${p.id})">Eliminar</button></td>
            `;
            body.appendChild(tr);
          });
        }

        async function cargarAlertas() {
          const umbral = document.getElementById('umbral').value || 5;
          const res = await fetch(`/productos/alertas?umbral=${umbral}`);
          const data = await res.json();
          const body = document.querySelector('#tabla-alertas tbody');
          body.innerHTML = '';
          data.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${p.id}</td><td>${p.nombre}</td><td>${p.precio.toFixed(2)}</td><td>${p.stock}</td>`;
            body.appendChild(tr);
          });
        }

        async function registrarVenta() {
          const id = parseInt(document.getElementById('venta-id').value, 10);
          const cantidad = parseInt(document.getElementById('venta-cantidad').value, 10);
          const msg = document.getElementById('venta-msg');
          msg.textContent = 'Procesando...';
          const res = await fetch('/ventas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ producto_id: id, cantidad: cantidad })
          });
          const data = await res.json();
          if (!res.ok) {
            msg.textContent = data.detail || 'Error al registrar venta';
            return;
          }
          msg.textContent = data.message || 'Venta registrada';
          await cargarProductos();
          await cargarAlertas();
        }

        async function crearProducto() {
          const id = parseInt(document.getElementById('nuevo-id').value, 10);
          const nombre = document.getElementById('nuevo-nombre').value;
          const precio = parseFloat(document.getElementById('nuevo-precio').value);
          const stock = parseInt(document.getElementById('nuevo-stock').value, 10);
          const msg = document.getElementById('crear-msg');
          msg.textContent = 'Procesando...';
          const res = await fetch('/productos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, nombre, precio, stock })
          });
          const data = await res.json();
          if (!res.ok) {
            msg.textContent = data.detail || 'Error al crear producto';
            return;
          }
          msg.textContent = data.message || 'Producto creado';
          document.getElementById('nuevo-id').value = '';
          document.getElementById('nuevo-nombre').value = '';
          document.getElementById('nuevo-precio').value = '';
          document.getElementById('nuevo-stock').value = '';
          await cargarProductos();
          await cargarAlertas();
        }

        async function eliminarProducto(id) {
          if (!confirm('Deseas eliminar el producto ' + id + '?')) {
            return;
          }
          const res = await fetch(`/productos/${id}`, { method: 'DELETE' });
          const data = await res.json();
          if (!res.ok) {
            alert(data.detail || 'Error al eliminar');
            return;
          }
          await cargarProductos();
          await cargarAlertas();
        }

        async function preguntarIA() {
          const pregunta = document.getElementById('ai-pregunta').value;
          const box = document.getElementById('ai-respuesta');
          box.textContent = 'Pensando...';
          const res = await fetch('/ai/consulta', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pregunta })
          });
          const data = await res.json();
          if (!res.ok) {
            box.textContent = data.detail || 'Error al consultar IA';
            return;
          }
          if (data.resultados && data.resultados.length) {
            box.textContent = data.resultados.join(' | ');
          } else {
            box.textContent = data.respuesta || 'Sin respuesta';
          }
          await cargarProductos();
          await cargarAlertas();
        }

        cargarProductos();
        cargarAlertas();
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get(
    "/health",
    summary="Healthcheck",
    description="Verifica que la API este funcionando correctamente.",
)
def healthcheck() -> dict:
    """Return healthcheck status."""
    return {"status": "ok"}


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


@app.post(
    "/productos",
    summary="Crear producto",
    description="Crea un nuevo producto en el inventario.",
)
def post_producto(payload: ProductoCreateRequest) -> dict:
    """Create a new product."""
    try:
        resultado = db.insertar_producto(
            producto_id=payload.id,
            nombre=payload.nombre,
            precio=payload.precio,
            stock=payload.stock,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Error interno al crear producto.",
        ) from exc

    if resultado == "exists":
        raise HTTPException(status_code=409, detail="El ID ya existe.")
    if resultado == "invalid":
        raise HTTPException(status_code=400, detail="Datos invalidos.")
    if resultado != "ok":
        raise HTTPException(status_code=500, detail="No se pudo crear el producto.")

    return {"status": "ok", "message": "Producto creado correctamente."}


@app.delete(
    "/productos/{producto_id}",
    summary="Eliminar producto",
    description="Elimina un producto por ID.",
)
def delete_producto(producto_id: int) -> dict:
    """Delete a product by ID."""
    try:
        resultado = db.eliminar_producto(producto_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Error interno al eliminar producto.",
        ) from exc

    if resultado == "not_found":
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    if resultado != "ok":
        raise HTTPException(status_code=500, detail="No se pudo eliminar el producto.")

    return {"status": "ok", "message": "Producto eliminado correctamente."}


@app.get(
    "/productos/alertas",
    response_model=List[ProductoResponse],
    summary="Alertas de stock",
    description="Retorna productos con stock menor o igual al umbral.",
)
def get_alertas(umbral: int = Query(5, ge=0)) -> List[ProductoResponse]:
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


@app.post(
    "/ai/consulta",
    response_model=AIResponse,
    summary="Consulta IA",
    description="Consulta el inventario usando Ollama (modelo llama3).",
)
def ai_consulta(payload: AIRequest) -> AIResponse:
    """Process an AI query using Ollama."""
    try:
        contexto = _build_inventory_context()
        system_prompt = (
            "Eres un asistente de inventario. "
            "Si el usuario pide agregar o eliminar productos, responde SOLO con un JSON "
            "con este formato: {\"action\": \"ADD_PRODUCT|DELETE_PRODUCT\", "
            "\"payload\": {\"items\": [{\"name\": \"...\", \"price\": 0.0, \"stock\": 0}]}}. "
            "Si no hay accion, responde texto breve."
        )
        prompt = (
            f"{system_prompt}\n\n{contexto}\n\n"
            f"Pregunta: {payload.pregunta}\n"
            "Respuesta:"
        )
        respuesta = _ask_ollama(prompt)
        action_obj = _parse_ai_action(respuesta)
        if action_obj:
            resultados = _execute_ai_action(action_obj)
            return AIResponse(
                respuesta="Accion ejecutada.",
                accion=str(action_obj.get("action")),
                resultados=resultados,
            )
        return AIResponse(respuesta=respuesta)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Error interno al consultar la IA.",
        ) from exc