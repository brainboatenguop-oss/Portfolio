# Sistema Profesional de Gestion de Inventario y Analisis de Ventas

Proyecto de portafolio en Python que demuestra modularidad, POO, estructuras de datos eficientes y manejo seguro de entradas de usuario.

## Estructura

```
mi-portafolio-inventario/
├── data/
│   ├── productos.json
│   └── transacciones.json
├── src/
│   ├── main.py
│   ├── logic.py
│   └── data_manager.py
├── README.md
└── .gitignore
```

## Como ejecutar

1. Abre la carpeta `mi-portafolio-inventario` en VS Code.
2. Ejecuta el programa:

```
python src/main.py
```

## Notas tecnicas

- Inventario en diccionario para busqueda O(1).
- Historial de transacciones en lista.
- Persistencia en JSON (con soporte opcional de TXT desde `data_manager.py`).
- Validacion de entradas con bloques `try-except`.