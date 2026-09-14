# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parents[1]
U = ROOT / "nisar_utils"
REQUIRED_MODULES = [
    "bootstrap.py", "config.py", "product.py", "product_identification.py",
    "hdf5.py", "gcov.py", "spatial.py", "statistics.py", "visualization.py",
    "raster.py", "performance.py", "polarimetry.py", "polarimetric_io.py"
]
EXPECTED_NOTEBOOKS = 19
CORE_NOTEBOOKS = [f"{i:02d}_" for i in range(1,13)]
POL_NOTEBOOKS = [f"{i:02d}_" for i in range(13,20)]
CANONICAL_NOTEBOOKS = sorted((ROOT / "notebooks").glob("*.ipynb"))
errors=[]
missing=[x for x in REQUIRED_MODULES if not (U/x).exists()]
if missing: errors.append("Missing modules: "+", ".join(missing))
for p in U.glob("*.py"):
    try: ast.parse(p.read_text(encoding="utf-8"))
    except Exception as exc: errors.append(f"{p.name}: Python syntax error: {exc}")
for p in CANONICAL_NOTEBOOKS:
    try: data=json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc: errors.append(f"{p.name}: invalid notebook JSON: {exc}"); continue
    ks=data.get("metadata",{}).get("kernelspec",{})
    if ks.get("name")!="nisar-training" or ks.get("display_name")!="NISAR Training": errors.append(f"{p.name}: incorrect kernelspec")
    for cell in data.get("cells",[]):
        if cell.get("cell_type")!="code": continue
        source="".join(cell.get("source",[]))
        if "/science/LSAR/" in source: errors.append(f"{p.name}: hard-coded LSAR path in code")
        if 'cfg["level"]' in source or 'cfg["product"]' in source: errors.append(f"{p.name}: legacy config key")
if len(CANONICAL_NOTEBOOKS)!=EXPECTED_NOTEBOOKS: errors.append(f"Expected {EXPECTED_NOTEBOOKS} training notebooks under notebooks/; found {len(CANONICAL_NOTEBOOKS)}")
for prefixes,label in [(CORE_NOTEBOOKS,"core"),(POL_NOTEBOOKS,"polarimetric")]:
    for prefix in prefixes:
        if not any(p.name.startswith(prefix) for p in CANONICAL_NOTEBOOKS): errors.append(f"Missing {label} notebook {prefix}")
if (ROOT/".pytest_cache").exists(): errors.append(".pytest_cache/ directory exists")
session=ROOT/"config"/"user_session.json"
if session.exists():
    try:
        if json.loads(session.read_text(encoding="utf-8")): errors.append("config/user_session.json is not clean")
    except Exception as exc: errors.append(f"config/user_session.json: invalid JSON: {exc}")
manifest=ROOT/"PACKAGE_MANIFEST.json"
if manifest.exists():
    try:
        m=json.loads(manifest.read_text(encoding="utf-8"))
        tests=m.get("tests",[])
        for t in tests:
            if not (ROOT/t).exists(): errors.append(f"Manifest references missing file: {t}")
    except Exception as exc: errors.append(f"PACKAGE_MANIFEST.json invalid: {exc}")
else: errors.append("Missing PACKAGE_MANIFEST.json")
if errors:
    print("STATIC INTEGRATION AUDIT: FAIL")
    for e in errors: print(" -",e)
    raise SystemExit(1)
print("STATIC INTEGRATION AUDIT: PASS")
print("Package version : v1.0.0")
print("Python modules  :",len(list(U.glob("*.py"))))
print("Notebooks found :",len(CANONICAL_NOTEBOOKS))
print("Core notebooks  : 12")
print("Polar notebooks : 7")
print("Kernelspec       : NISAR Training / nisar-training")
print("Polarimetry modules: PASS")
print("Manifest references: PASS")
