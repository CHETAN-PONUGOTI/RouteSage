"""Seed the database with the pre-generated synthetic dataset."""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.domain.services.synthetic_data import import_dataset
from app.infrastructure.database import SessionLocal
from app.infrastructure.repositories import RouteRepository, ShipmentRepository


def get_default_dataset_path() -> Path:
    repo_root = backend_dir.parent
    candidate_paths = [
        repo_root / "data" / "synthetic_dataset.json",
        Path.cwd() / "data" / "synthetic_dataset.json",
        Path.cwd().parent / "data" / "synthetic_dataset.json",
    ]
    for p in candidate_paths:
        if p.exists():
            return p
    return candidate_paths[0]


def seed_database(
    session=None,
    force: bool = False,
    dataset_path: Path | str | None = None,
) -> tuple[int, int]:
    """Load synthetic dataset into the database.

    Returns a tuple of (shipments_seeded_count, routes_seeded_count).
    """
    path = Path(dataset_path) if dataset_path else get_default_dataset_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Synthetic dataset file not found at: {path}. "
            "Run 'python scripts/generate_dataset.py' first."
        )

    shipments, routes = import_dataset(str(path))

    close_session_at_end = False
    if session is None:
        try:
            session = SessionLocal()
            close_session_at_end = True
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to the database: {e}. "
                "Ensure database migrations have been executed."
            ) from e

    try:
        shipment_repo = ShipmentRepository(session)
        route_repo = RouteRepository(session)

        existing_shipments = shipment_repo.list()
        if existing_shipments and not force:
            print(
                f"Database already contains {len(existing_shipments)} shipments. "
                "Skipping seeding. Use --force to re-seed."
            )
            return 0, 0

        for shipment in shipments:
            shipment_repo.save(shipment)

        route_repo.save_all(routes)

        return len(shipments), len(routes)
    finally:
        if close_session_at_end:
            session.close()


def main():
    force = "--force" in sys.argv
    path_arg = None
    for arg in sys.argv[1:]:
        if arg != "--force" and not arg.startswith("-"):
            path_arg = Path(arg)
            break

    try:
        s_count, r_count = seed_database(force=force, dataset_path=path_arg)
        if s_count > 0:
            print(
                f"Successfully seeded {s_count} shipments and {r_count} candidate routes into the database."
            )
    except Exception as exc:  # noqa: BLE001
        print(f"Error seeding database: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
