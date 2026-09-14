# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

def build_profile(cfg):
    from .product import identify_nisar_product
    return identify_nisar_product(Path(cfg["nisar_file"]), verify_hdf5=True)

def resolve_frequency(cfg, profile):
    frequencies = list(profile.frequencies or [])
    if not frequencies:
        raise ValueError("No GCOV frequency was discovered in the selected product.")
    requested = cfg.get("default_frequency")
    # ``auto`` (and legacy null) means: use the sole available frequency.
    # Multi-frequency products are intentionally selected in Module 02 and persisted.
    if requested in (None, "", "auto", "AUTO") and len(frequencies) == 1:
        return frequencies[0]
    if requested in frequencies:
        return requested
    if len(frequencies) == 1:
        return frequencies[0]
    raise ValueError(
        f"Multiple frequencies are available: {frequencies}. "
        "Run Module 02 to select and persist the training frequency."
    )

def resolve_terms(profile, frequency):
    terms = list(profile.covariance_terms.get(frequency, []) or [])
    if not terms:
        raise ValueError(f"No covariance terms discovered for {frequency}.")
    diagonal = list(profile.diagonal_terms.get(frequency, []) or [])
    off_diagonal = list(profile.off_diagonal_terms.get(frequency, []) or [])
    return terms, diagonal, off_diagonal

def resolve_aoi(cfg):
    aoi = cfg.get("default_aoi")
    if not aoi:
        return None
    required = {"xmin", "xmax", "ymin", "ymax"}
    missing = required - set(aoi)
    if missing:
        raise ValueError(f"AOI is missing keys: {sorted(missing)}")
    return aoi

def default_window(x, y, size=1024):
    """Return a safe central-ish window for training when no AOI is configured."""
    rows = len(y)
    cols = len(x)
    h = min(size, rows)
    w = min(size, cols)
    r0 = max(0, (rows - h) // 2)
    c0 = max(0, (cols - w) // 2)
    return r0, r0 + h, c0, c0 + w

def resolve_window(x, y, cfg, coordinate_to_index_func=None, size=1024):
    """Resolve a native row/column window for downstream processing.

    Module 06 is authoritative for spatial subsetting.  When it has saved a
    validated native ``spatial_subset``, reuse those indices directly rather
    than interpreting the WGS84 ``default_aoi`` as native projected metres.
    """
    subset = cfg.get("spatial_subset")
    if subset:
        required = {"r0", "r1", "c0", "c1"}
        missing = required - set(subset)
        if missing:
            raise ValueError(f"spatial_subset is missing keys: {sorted(missing)}")
        r0, r1 = int(subset["r0"]), int(subset["r1"])
        c0, c1 = int(subset["c0"]), int(subset["c1"])
        if not (0 <= r0 < r1 <= len(y) and 0 <= c0 < c1 <= len(x)):
            raise ValueError(
                f"Saved spatial_subset is outside the current grid: "
                f"r0={r0}, r1={r1}, c0={c0}, c1={c1}; "
                f"grid={len(y)}x{len(x)}"
            )
        return (r0, r1, c0, c1), cfg.get("default_aoi") or cfg.get("aoi")

    aoi = resolve_aoi(cfg)
    if aoi is None:
        return default_window(x, y, size=size), None
    if coordinate_to_index_func is None:
        raise ValueError("coordinate_to_index function is required when AOI is configured.")
    return coordinate_to_index_func(
        x, y, aoi["xmin"], aoi["xmax"], aoi["ymin"], aoi["ymax"]
    ), aoi
