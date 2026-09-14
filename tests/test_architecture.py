# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
CORE=[f"{i:02d}_" for i in range(1,13)]
POL=[f"{i:02d}_" for i in range(13,20)]

def test_core_notebooks_present():
    for prefix in CORE:
        assert any(p.name.startswith(prefix) and p.suffix=='.ipynb' for p in (ROOT/'notebooks').iterdir())

def test_polarimetric_modules_present():
    for prefix in POL:
        assert any(p.name.startswith(prefix) and p.suffix=='.ipynb' for p in (ROOT/'notebooks').iterdir())

def test_subset_helper_uses_persisted_subset_keys_only():
    s=(ROOT/'nisar_utils'/'polarimetric_io.py').read_text()
    for k in ('r0','r1','c0','c1'): assert f'"{k}"' in s
    assert 'row_start' not in s and 'col_start' not in s

def test_polarimetric_notebooks_reuse_standard_t3_for_eigen_analysis():
    for name in ['15_LSAR_FullPol_Observables_and_Eigen_Analysis.ipynb','16_LSAR_FullPol_Cloude_Pottier_H_A_Alpha.ipynb','19_End_to_End_NISAR_Polarimetric_Analysis_Capstone.ipynb']:
        nb=json.loads((ROOT/'notebooks'/name).read_text())
        src='\n'.join(''.join(c.get('source',[])) for c in nb['cells'] if c.get('cell_type')=='code')
        assert 'nisar_c3_to_standard_c3' in src
        assert 'standard_c3_to_t3' in src

def test_manifest_test_references_exist():
    m=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text())
    for t in m['tests']:
        assert (ROOT/t).exists(), t
