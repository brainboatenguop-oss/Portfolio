from pathlib import Path

from data_manager import cargar_datos, guardar_datos, guardar_ticket
from logic import InventarioManager, Producto


def prompt_text(message: str) -> str:
    """Prompt the user for non-empty text input.

    Args:
        message: Prompt message.

    Returns:
        Non-empty string provided by the user.
    """
    while True:
        try:
            value = input(message).strip()
        except EOFError:
            raise SystemExit
        if value:
            return value
        print("El texto no puede estar vacio.")


def prompt_int(message: str, min_value: int | None = None) -> int:
    """Prompt the user for an integer input.

    Args:
        message: Prompt message.
        min_value: Optional minimum accepted value.

    Returns:
        Integer provided by the user.
    """
    while True:
        try:
            value = int(input(message).strip())
        except EOFError:
            raise SystemExit
        except ValueError:
            print("Entrada invalida. Debe ser un numero entero.")
            continue
        if min_value is not None and value < min_value:
            print(f"El valor debe ser mayor o igual a {min_value}.")
            continue
        return value


def prompt_float(message: str, min_value: float | None = None) -> float:
    """Prompt the user for a float input.

    Args:
        message: Prompt message.
        min_value: Optional minimum accepted value.

    Returns:
        Float provided by the user.
    """
    while True:
        try:
            value = float(input(message).strip())
        except EOFError:
            raise SystemExit
        except ValueError:
            print("Entrada invalida. Debe ser un numero.")
            continue
        if min_value is not None and value < min_value:
            print(f"El valor debe ser mayor o igual a {min_value}.")
            continue
        return value


def mostrar_inventario(manager: InventarioManager) -> None:
    """Display the inventory in a simple table.

    Args:
        manager: InventarioManager instance.

    Returns:
        None.
    """
    productos = manager.obtener_lista()
    if not productos:
        print("No hay productos en el inventario.")
        return

    print("\nInventario:\n")
    print(f"{'ID':<10} {'Nombre':<25} {'Precio':>10} {'Stock':>8}")
    print("-" * 60)
    for producto in productos:
        print(
            f"{producto.id:<10} {producto.nombre:<25} "
            f"{producto.precio:>10.2f} {producto.stock:>8}"
        )


def main() -> None:
    """Run the inventory management console application.

    Returns:
        None.
    """
    base_dir = Path(__file__).resolve().parents[1]
    datos = cargar_datos(base_dir)
    manager = InventarioManager.from_dict(datos)

    try:
        while True:
            print("\nGestion de Inventario Modular")
            print("1. Ver inventario")
            print("2. Anadir producto")
            print("3. Vender/Comprar (ajuste de stock)")
            print("4. Salir")

            try:
                opcion = input("Selecciona una opcion: ").strip()
            except EOFError:
                raise SystemExit

            if opcion == "1":
                mostrar_inventario(manager)

            elif opcion == "2":
                try:
                    producto = Producto(
                        id=prompt_text("ID del producto: "),
                        nombre=prompt_text("Nombre del producto: "),
                        precio=prompt_float("Precio: ", min_value=0),
                        stock=prompt_int("Stock inicial: ", min_value=0),
                    )
                except ValueError as exc:
                    print(f"Error: {exc}")
                    continue

                if manager.anadir_producto(producto):
                    print("Producto agregado correctamente.")
                else:
                    print("El ID ya existe. Usa otro ID.")

            elif opcion == "3":
                producto_id = prompt_text("ID del producto: ")
                tipo = prompt_text("Escribe V para vender o C para comprar: ").upper()
                cantidad = prompt_int("Cantidad: ", min_value=1)

                if tipo == "V":
                    producto = manager.productos.get(producto_id)
                    if producto is None:
                        print("No se encontro el producto.")
                        continue
                    if producto.stock < cantidad:
                        print(
                            f"Stock insuficiente. Disponible: {producto.stock}. "
                            f"Solicitado: {cantidad}."
                        )
                        continue
                    cantidad = -cantidad
                elif tipo != "C":
                    print("Opcion invalida. Usa V o C.")
                    continue

                if manager.actualizar_stock(producto_id, cantidad):
                    print("Stock actualizado.")
                    if tipo == "V":
                        producto = manager.productos.get(producto_id)
                        if producto is None:
                            print("No se encontro el producto para generar el ticket.")
                            continue
                        unidades = abs(cantidad)
                        total = round(producto.precio * unidades, 2)
                        imprimir = prompt_text("Desea imprimir el ticket? (S/N): ").upper()
                        if imprimir == "S":
                            ticket = manager.generar_recibo(producto_id, unidades, total)
                            ruta = guardar_ticket(ticket, base_dir)
                            print("\n" + ticket)
                            print(f"Ticket guardado en: {ruta}")
                else:
                    print("No se pudo actualizar el stock. Verifica el ID o el valor.")

            elif opcion == "4":
                guardar_datos(manager.to_dict(), base_dir)
                print("Cambios guardados. Hasta luego.")
                break

            else:
                print("Opcion invalida. Intenta nuevamente.")
    except (KeyboardInterrupt, SystemExit, EOFError):
        guardar_datos(manager.to_dict(), base_dir)
        print("\nSalida segura. Cambios guardados.")


if __name__ == "__main__":
    main()
