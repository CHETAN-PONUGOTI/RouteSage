import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.domain.services.synthetic_data import SyntheticDataGenerator, export_dataset


def main():
    print("Generating synthetic dataset...")
    generator = SyntheticDataGenerator(seed=42)
    shipments, routes = generator.generate_dataset()

    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    out_file = data_dir / "synthetic_dataset.json"
    export_dataset(shipments, routes, str(out_file))
    print(f"Generated {len(shipments)} shipments and {len(routes)} routes.")
    print(f"Saved to {out_file}")


if __name__ == "__main__":
    main()
