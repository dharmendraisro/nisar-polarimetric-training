# SPDX-License-Identifier: Apache-2.0

"""Generic NISAR product identification and validation engine."""
from dataclasses import dataclass, asdict
from pathlib import Path
import re
import h5py


POL_MAP = {
    "SH": {"class": "single-pol", "channels": ["HH"]},
    "SV": {"class": "single-pol", "channels": ["VV"]},
    "DH": {"class": "dual-pol", "channels": ["HH", "HV"]},
    "DV": {"class": "dual-pol", "channels": ["VV", "VH"]},
    "CL": {"class": "compact-pol", "channels": ["LH", "LV"]},
    "CR": {"class": "compact-pol", "channels": ["RH", "RV"]},
    "QP": {"class": "quad-pol", "channels": ["HH", "HV", "VH", "VV"]},
    "NA": {"class": "absent", "channels": []},
}

@dataclass
class ProductProfile:
    filename: str
    mission: str = "NISAR"
    instrument: str | None = None
    band: str | None = None
    sar_family: str | None = None
    product_level: str | None = None
    processing_type: str | None = None
    product_type: str | None = None
    cycle: str | None = None
    relative_orbit: str | None = None
    orbit_direction: str | None = None
    frame: str | None = None
    mode_code: str | None = None
    primary_mode: str | None = None
    secondary_mode: str | None = None
    polarization_code: str | None = None
    primary_polarization: str | None = None
    secondary_polarization: str | None = None
    primary_channels: list | None = None
    secondary_channels: list | None = None
    polarization_class: str | None = None
    polarization_channels: list | None = None
    source: str | None = None
    start_datetime: str | None = None
    end_datetime: str | None = None
    crid: str | None = None
    accuracy: str | None = None
    coverage: str | None = None
    location: str | None = None
    counter: str | None = None
    gcov_root: str | None = None
    frequencies: list | None = None
    covariance_terms: dict | None = None
    diagonal_terms: dict | None = None
    off_diagonal_terms: dict | None = None
    epsg: int | None = None
    x_spacing: float | None = None
    y_spacing: float | None = None
    filename_fields: dict | None = None
    warnings: list | None = None
    confidence: str = "low"

    def to_dict(self):
        return asdict(self)


def _parse_il(il):
    """Parse combined instrument/level field, e.g. L2 or S1."""
    if not re.fullmatch(r"[LS][123]", il.upper()):
        return None, None
    instrument = il[0].upper()
    level = f"L{il[1]}"
    return instrument, level


def parse_filename(filename):
    name = Path(filename).name
    stem = Path(name).stem
    tokens = stem.split("_")

    result = {"filename": name, "mission": "NISAR"}
    if len(tokens) < 6 or tokens[0].upper() != "NISAR":
        result["parse_error"] = "Filename does not match the expected NISAR convention."
        return result

    # NISAR_IL_PT_PROD_CYL_REL_P_FRM_MODE_POLE_S_Start_End_CRID_A_C_LOC_CTR
    keys = [
        "mission", "il", "processing_type", "product_type", "cycle",
        "relative_orbit", "orbit_direction", "frame", "mode_code",
        "polarization_code", "source", "start_datetime", "end_datetime",
        "crid", "accuracy", "coverage", "location", "counter"
    ]
    fields = dict(zip(keys, tokens[:len(keys)]))
    # IL is the combined instrument + level field (e.g. L2, S2).
    # The parser deliberately retains the raw IL token for training/audit.
    result["filename_fields"] = fields

    il = fields.get("il", "")
    instrument, level = _parse_il(il)
    result["instrument"] = instrument
    result["band"] = instrument
    result["sar_family"] = {"L": "LSAR", "S": "SSAR"}.get(instrument)
    result["product_level"] = level
    result["processing_type"] = fields.get("processing_type")
    result["product_type"] = fields.get("product_type")
    if result["product_type"] == "GCOV" and result["product_level"] is None:
        result["product_level"] = "L2"

    for k in [
        "cycle", "relative_orbit", "orbit_direction", "frame",
        "mode_code", "source", "start_datetime", "end_datetime",
        "crid", "accuracy", "coverage", "location", "counter"
    ]:
        result[k] = fields.get(k)

    mode = fields.get("mode_code", "")
    if len(mode) == 4:
        result["primary_mode"] = mode[:2]
        result["secondary_mode"] = mode[2:]

    pole = fields.get("polarization_code", "")
    if len(pole) == 4:
        p1, p2 = pole[:2].upper(), pole[2:].upper()
        result["polarization_code"] = pole.upper()
        result["primary_polarization"] = p1
        result["secondary_polarization"] = p2
        p1i, p2i = POL_MAP.get(p1), POL_MAP.get(p2)
        result["primary_channels"] = (p1i or {}).get("channels", [])
        result["secondary_channels"] = (p2i or {}).get("channels", [])

        classes = [x["class"] for x in (p1i, p2i) if x]
        if "quad-pol" in classes:
            result["polarization_class"] = "quad-pol"
        elif "compact-pol" in classes:
            result["polarization_class"] = "compact-pol"
        elif "dual-pol" in classes:
            result["polarization_class"] = "dual-pol"
        elif "single-pol" in classes:
            result["polarization_class"] = "single-pol"
        else:
            result["polarization_class"] = "unknown"

        channels = []
        for ch in result["primary_channels"] + result["secondary_channels"]:
            if ch not in channels:
                channels.append(ch)
        result["polarization_channels"] = channels

    return result


def discover_gcov_root(h5):
    from .hdf5 import safe_visititems
    candidates = []
    def visitor(name, obj):
        if isinstance(obj, h5py.Group) and name.upper().endswith("/GCOV"):
            candidates.append("/" + name)
    safe_visititems(h5, visitor)
    preferred = [
        p for p in candidates
        if re.fullmatch(r"/science/(LSAR|SSAR)/GCOV", p, re.I)
    ]
    return preferred[0] if preferred else (candidates[0] if candidates else None)


def discover_hdf5(filename):
    out = {
        "gcov_root": None, "sar_family": None, "band": None,
        "product_type": None, "frequencies": [],
        "covariance_terms": {}, "diagonal_terms": {},
        "off_diagonal_terms": {}, "epsg": None,
        "x_spacing": None, "y_spacing": None,
    }
    with h5py.File(filename, "r") as f:
        root = discover_gcov_root(f)
        out["gcov_root"] = root
        if root:
            m = re.fullmatch(r"/science/(LSAR|SSAR)/GCOV", root, re.I)
            if m:
                out["sar_family"] = m.group(1).upper()
                out["band"] = "L" if out["sar_family"] == "LSAR" else "S"
            out["product_type"] = "GCOV"
            grids = f[f"{root}/grids"] if f"{root}/grids" in f else None
            if grids is not None:
                for freq, obj in grids.items():
                    if not isinstance(obj, h5py.Group):
                        continue
                    out["frequencies"].append(freq)
                    terms = sorted([
                        n for n, child in obj.items()
                        if isinstance(child, h5py.Dataset)
                        # Real GCOV covariance terms are always a 4-letter
                        # combination of polarization codes (H, V, R, or L),
                        # always uppercase -- e.g. HHHH, HVHV, RHRV. A loose
                        # "any 4 letters" pattern also matches the "mask"
                        # auxiliary dataset, silently listing it as a
                        # covariance term (and, since "ma" != "sk", as an
                        # off-diagonal one) in every downstream module that
                        # iterates over discovered terms.
                        and re.fullmatch(r"[HVRL]{4}", n)
                    ])
                    out["covariance_terms"][freq] = terms
                    out["diagonal_terms"][freq] = sorted(
                        [t for t in terms if t[:2] == t[2:]]
                    )
                    out["off_diagonal_terms"][freq] = sorted(
                        [t for t in terms if t[:2] != t[2:]]
                    )
                    if "projection" in obj:
                        attrs = obj["projection"].attrs
                        if out["epsg"] is None and "epsg_code" in attrs:
                            out["epsg"] = int(attrs["epsg_code"])
                    if "xCoordinateSpacing" in obj:
                        out["x_spacing"] = float(obj["xCoordinateSpacing"][()])
                    if "yCoordinateSpacing" in obj:
                        out["y_spacing"] = float(obj["yCoordinateSpacing"][()])
    return out


def identify_nisar_product(filename, verify_hdf5=True):
    parsed = parse_filename(filename)
    hdf = discover_hdf5(filename) if verify_hdf5 and Path(filename).exists() else {}

    warnings = []
    for field in ("band", "sar_family", "product_type"):
        pv = parsed.get(field)
        hv = hdf.get(field)
        if pv and hv and pv != hv:
            warnings.append(f"{field}: filename={pv}, HDF5={hv}")

    # GCOV is specified as Level 2; use that as a product-level fallback
    # when the filename follows the GCOV naming convention.
    level = parsed.get("product_level")
    if level is None and (parsed.get("product_type") == "GCOV" or hdf.get("product_type") == "GCOV"):
        level = "L2"

    evidence = sum(bool(x) for x in [
        parsed.get("instrument"), level, parsed.get("processing_type"),
        parsed.get("product_type"), hdf.get("gcov_root"),
        hdf.get("frequencies")
    ])
    confidence = "conflict" if warnings else ("high" if evidence >= 5 else "medium" if evidence >= 3 else "low")

    data = dict(
        filename=parsed.get("filename", Path(filename).name),
        mission=parsed.get("mission", "NISAR"),
        instrument=parsed.get("instrument") or hdf.get("band"),
        band=parsed.get("band") or hdf.get("band"),
        sar_family=parsed.get("sar_family") or hdf.get("sar_family"),
        product_level=level,
        processing_type=parsed.get("processing_type"),
        product_type=parsed.get("product_type") or hdf.get("product_type"),
        cycle=parsed.get("cycle"), relative_orbit=parsed.get("relative_orbit"),
        orbit_direction=parsed.get("orbit_direction"), frame=parsed.get("frame"),
        mode_code=parsed.get("mode_code"), primary_mode=parsed.get("primary_mode"),
        secondary_mode=parsed.get("secondary_mode"),
        polarization_code=parsed.get("polarization_code"),
        primary_polarization=parsed.get("primary_polarization"),
        secondary_polarization=parsed.get("secondary_polarization"),
        primary_channels=parsed.get("primary_channels"),
        secondary_channels=parsed.get("secondary_channels"),
        polarization_class=parsed.get("polarization_class"),
        polarization_channels=parsed.get("polarization_channels"),
        source=parsed.get("source"), start_datetime=parsed.get("start_datetime"),
        end_datetime=parsed.get("end_datetime"), crid=parsed.get("crid"),
        accuracy=parsed.get("accuracy"), coverage=parsed.get("coverage"),
        location=parsed.get("location"), counter=parsed.get("counter"),
        gcov_root=hdf.get("gcov_root"),
        frequencies=hdf.get("frequencies", []),
        covariance_terms=hdf.get("covariance_terms", {}),
        diagonal_terms=hdf.get("diagonal_terms", {}),
        off_diagonal_terms=hdf.get("off_diagonal_terms", {}),
        epsg=hdf.get("epsg"), x_spacing=hdf.get("x_spacing"),
        y_spacing=hdf.get("y_spacing"),
        filename_fields=parsed.get("filename_fields", {}),
        warnings=warnings, confidence=confidence
    )
    return ProductProfile(**data)
