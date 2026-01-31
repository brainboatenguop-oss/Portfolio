# Sistema de Gestion de Inventario Modular (Python + Java)

Proyecto de portafolio orientado a reclutadores que demuestra disenio modular, POO y buenas practicas de desarrollo. Incluye un sistema de inventario en Python con persistencia en JSON y un auditor de stock en Java que consulta SQLite y genera reportes.

## Arquitectura (Multicapa)

El proyecto separa responsabilidades en tres capas para mantener el codigo limpio, escalable y facil de mantener:

- `main.py` (Presentacion / UI): Orquesta el flujo, muestra el menu interactivo y valida entradas.
- `logic.py` (Dominio): Define la logica de negocio con POO (clases `Producto` e `InventarioManager`).
- `data_manager.py` (Persistencia): Carga/guarda datos en JSON y utilidades de almacenamiento. Incluye `DatabaseManager` para SQLite y alertas de stock.

Esta separacion permite modificar la interfaz o la persistencia sin afectar el nucleo del sistema.

## Estructura del proyecto

```
Portfolio/
├── mi-portafolio-inventario/
│   ├── data/
│   │   ├── inventario.json
│   │   └── inventario.db
│   ├── tickets/
│   │   └── ticket_YYYYMMDD_HHMMSS_micro.txt
│   ├── src/
│   │   ├── main.py
│   │   ├── logic.py
│   │   └── data_manager.py
│   └── README.md
├── logs/
│   └── auditoria_stock.txt
└── src/
    └── StockAuditor.java
```

## Logica tecnica

### Programacion Orientada a Objetos (POO)
- **Producto**: entidad principal con `id`, `nombre`, `precio` y `stock`.
- **InventarioManager**: gestiona un diccionario de productos, encapsula validaciones y operaciones clave (anadir, actualizar stock, listado, recibos).
- **DatabaseManager**: capa SQLite para alertas de stock con consultas parametrizadas y manejo de errores.

### Persistencia
- **JSON**: `mi-portafolio-inventario/data/inventario.json` para datos del sistema Python.
- **SQLite**: `mi-portafolio-inventario/data/inventario.db` para auditoria en Java.

### Manejo de excepciones y validaciones
- Se valida que precio y stock no sean negativos.
- Se evita vender mas unidades de las disponibles.
- Entradas del usuario protegidas con `try/except`.
- Acceso SQLite protegido con `sqlite3.Error` y consultas parametrizadas.

## Funcionalidades destacadas

- Alta de productos con validaciones.
- Ajuste de stock (compra/venta).
- Generacion de tickets con timestamp y guardado automatico en `tickets/`.
- Persistencia y recuperacion de inventario en JSON.
- Auditoria de stock en Java con log persistente en `logs/auditoria_stock.txt`.

## Stack tecnologico

- **Python 3.x**
- **Java 17+** (para el auditor)
- **SQLite** y **JSON** para persistencia
- **Clean Code** y separacion de responsabilidades

## Guia de instalacion (Python)

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

### 3) Ejecutar la aplicacion Python

```
cd .\mi-portafolio-inventario
python .\src\main.py
```

## Auditor de Stock (Java)

El archivo `src/StockAuditor.java` genera un reporte con productos cuyo stock es menor o igual al umbral indicado.

### Dependencias
Se requiere el driver JDBC de SQLite y SLF4J (solo para runtime):

- `sqlite-jdbc.jar`
- `slf4j-api.jar`
- `slf4j-nop.jar`

### Compilar y ejecutar
Desde la raiz del repo:

```
javac -cp .;sqlite-jdbc.jar src\StockAuditor.java
java -cp ".;sqlite-jdbc.jar;slf4j-api.jar;slf4j-nop.jar;src" StockAuditor
```

Para definir un umbral custom:

```
java -cp ".;sqlite-jdbc.jar;slf4j-api.jar;slf4j-nop.jar;src" StockAuditor 3
```

## Impacto para reclutadores

Este proyecto demuestra capacidad para:

- Disenar arquitectura modular y escalable.
- Aplicar POO con entidades claras y cohesionadas.
- Mantener persistencia y robustez ante errores comunes.
- Construir una base solida para futuras extensiones (UI grafica, base de datos, APIs).

---

Si deseas extenderlo (reportes, filtros avanzados, integracion con API REST o UI grafica), el codigo esta preparado para crecer sin reescrituras agresivas.