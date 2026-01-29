# Sistema de Gestion de Inventario Modular (Python)

Proyecto de portafolio orientado a reclutadores que demuestra disenio modular, POO y buenas practicas de desarrollo en Python. El sistema permite administrar productos, ajustar stock (compra/venta) y generar tickets de compra, con persistencia en JSON.

## Arquitectura (Multicapa)

El proyecto separa responsabilidades en tres capas para mantener el codigo limpio, escalable y facil de mantener:

- `main.py` (Presentacion / UI): Orquesta el flujo, muestra el menu interactivo y valida entradas.
- `logic.py` (Dominio): Define la logica de negocio con POO (clases `Producto` e `InventarioManager`).
- `data_manager.py` (Persistencia): Carga y guarda datos en JSON con manejo de excepciones.

Esta separacion permite modificar la interfaz o la persistencia sin afectar el nucleo del sistema.

## Estructura del proyecto

```
Portfolio/
└── mi-portafolio-inventario/
    ├── data/
    │   └── inventario.json
    ├── tickets/
    │   └── ticket_YYYYMMDD_HHMMSS_micro.txt
    ├── src/
    │   ├── main.py
    │   ├── logic.py
    │   └── data_manager.py
    └── README.md
```

## Logica tecnica

### Programacion Orientada a Objetos (POO)
- **Producto**: entidad principal con `id`, `nombre`, `precio` y `stock`.
- **InventarioManager**: gestiona un diccionario de productos, encapsula validaciones y operaciones clave (anadir, actualizar stock, listado, recibos).

### Persistencia en JSON
- Los datos se guardan en `data/inventario.json`.
- La capa de persistencia maneja errores (`FileNotFoundError`, `JSONDecodeError`) para evitar fallos al iniciar.

### Manejo de excepciones y validaciones
- Se valida que precio y stock no sean negativos.
- Se evita vender mas unidades de las disponibles.
- Entradas del usuario protegidas con `try/except`.

## Funcionalidades destacadas

- Alta de productos con validaciones.
- Ajuste de stock (compra/venta).
- Generacion de tickets con timestamp y guardado automatico en `tickets/`.
- Persistencia y recuperacion de inventario en JSON.

## Stack tecnologico

- **Python 3.x**
- **JSON** para persistencia ligera
- **Clean Code** y principios de separacion de responsabilidades

## Guia de instalacion

### 1) Clonar el repositorio

```
git clone https://github.com/brainboatenguop-oss/Portfolio.git
cd Portfolio
```

### 2) Crear y activar entorno virtual

**Windows (PowerShell):**
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Ejecutar la aplicacion

```
cd .\mi-portafolio-inventario
python .\src\main.py
```

## Impacto para reclutadores

Este proyecto demuestra capacidad para:

- Disenar arquitectura modular y escalable.
- Aplicar POO con entidades claras y cohesionadas.
- Mantener persistencia y robustez ante errores comunes.
- Construir una base solida para futuras extensiones (UI grafica, base de datos, APIs).

---

Si deseas extenderlo (reportes, filtros avanzados, integracion con SQLite o API REST), el codigo esta preparado para crecer sin reescrituras agresivas.