# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import json

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PACKAGE_ROOT / "config"
SESSION_FILE = CONFIG_DIR / "user_session.json"

def save_session(session):
    """Merge the given keys into the persisted session, rather than
    replacing it outright.

    Several modules only ever have a handful of new keys to record (Module
    13's polarimetric-mode detection, for instance, only knows about
    ``polarimetric_mode``/``polarimetric_family``/etc.) and were never meant
    to know about — let alone repeat — everything Module 01/02/06 already
    saved. A plain overwrite here silently drops `nisar_file`,
    `default_frequency`, `spatial_subset`, and anything else already on
    disk the moment any later module calls this with a partial dict —
    which is exactly what used to happen after Module 13 ran, breaking
    `load_config()` for every module after it.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing = {}
    if SESSION_FILE.exists():
        try:
            existing = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}
    payload = {**existing, **dict(session)}
    if "nisar_file" in payload:
        payload["nisar_file"] = str(Path(payload["nisar_file"]).resolve())
    with SESSION_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return SESSION_FILE

def load_config(require_file=True):
    if not SESSION_FILE.exists():
        raise RuntimeError("Session not initialized. Run Module 01 first.")
    defaults_file = CONFIG_DIR / "workshop_defaults.json"
    defaults = json.loads(defaults_file.read_text(encoding="utf-8")) if defaults_file.exists() else {}
    session = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    cfg = {**defaults, **session}
    if require_file:
        p = Path(cfg["nisar_file"])
        if not p.exists():
            raise FileNotFoundError(f"Configured NISAR file does not exist: {p}")
    return cfg

def clear_session():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
