"""Compatibility entry point for full model-memory validation."""
from validate_memory import main, validate_assets


def verify_mif_precision(mif_dir="hardware/mif"):
    return validate_assets(mif_dir)["valid"]


if __name__ == "__main__":
    raise SystemExit(main())
