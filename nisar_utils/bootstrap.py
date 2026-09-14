# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import sys

def find_workshop_root(start=None):
    start = Path(start or Path.cwd()).resolve()
    candidates = [start, *start.parents]
    for candidate in candidates:
        if (candidate / "nisar_utils").is_dir() and (candidate / "environment.yml").is_file() and ((candidate / "notebooks").is_dir() and any((candidate / "notebooks").glob("*.ipynb")) or any(candidate.glob("*.ipynb"))):
            return candidate
    raise RuntimeError(
        "Could not locate the NISAR GCOV Training package root. "
        "Launch Jupyter from the repository root or add its root to sys.path."
    )

def setup_workshop(start=None):
    root = find_workshop_root(start)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root
