import json
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict

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