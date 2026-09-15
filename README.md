# NISAR Polarimetric Analysis Training Toolkit

**Version 1.1.0 — Public Release**

Open-source Python/Jupyter training and research toolkit for hands-on analysis of **NISAR Level-2 GCOV** products, with workflows for both **LSAR full polarimetry** and **SSAR compact/hybrid polarimetry**.

[![Release](https://img.shields.io/badge/release-v1.1.0-blue.svg)](https://github.com/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](environment.yml)

> **Independent project:** This toolkit is developed and maintained by Dharmendra Kumar Pandey in a personal capacity. It is not an official software release, endorsement, or representation of any employer, government organization, space agency, mission team, or data provider.

## Overview

The toolkit provides a reproducible, notebook-based progression from NISAR GCOV product discovery through spatial subsetting, quality control, visualization, GIS export, and polarimetric analysis.

This public release is supported by automated regression tests, notebook/static audits, and end-to-end execution across the Full-Pol, Compact-Pol, and Dual-Pol training paths. Modules 07, 08, and 15–17 include corrections and robustness improvements identified during validation, including memory-conscious processing for large LSAR Full-Pol areas of interest.

## Scientific workflow

```text
NISAR L2 GCOV HDF5
        │
        ├── Product discovery and metadata
        │
        ├── AOI / spatial subset
        │
        ├── QC and GCOV mask
        │
        ├── Visualization / GIS export
        │
        └── Polarimetric analysis
             │
             ├── LSAR: HH, HV, VH, VV
             │      ├── Complex covariance reconstruction
             │      ├── Polarimetric observables
             │      ├── Eigen analysis
             │      ├── Cloude–Pottier H/A/alpha
             │      └── Pauli / Freeman–Durden / Yamaguchi
             │
             └── SSAR: RH, RV
                    ├── Stokes parameters
                    ├── Degree of polarization
                    └── m-chi / m-delta / m-alpha
```

## What is improved in v1.1.0

- Corrected the missing NumPy import in Module 07.
- Corrected VVVV/VHVH quality-control masking behavior in Module 08.
- Revised Modules 15–17 for memory-conscious processing of large LSAR Full-Pol AOIs.
- Added tile-wise Cloude–Pottier H/A/alpha processing for large scenes.
- Improved Pauli, Freeman–Durden and Yamaguchi-4 robustness and visualization.
- Preserved the underlying polarimetric mathematics and quantitative output products.

## Modules

| Modules | Purpose |
|---|---|
| 01–04 | Setup, session checks, product exploration and metadata |
| 05 | Large-product performance and windowed access |
| 06 | AOI selection and authoritative spatial subset |
| 07 | QC, statistics and masks |
| 08 | GCOV visualization and RGB composites |
| 09 | Advanced frequency/mask/metadata/batch workflows |
| 10 | GeoTIFF export and QGIS validation |
| 11 | End-to-end GCOV capstone |
| 12 | Trainer troubleshooting and session management |
| 13 | Polarimetric mode discovery and complex covariance inventory |
| 14 | LSAR full-pol covariance reconstruction and validation |
| 15 | Full-pol observables and eigen analysis |
| 16 | Cloude–Pottier H/A/alpha |
| 17 | Pauli, Freeman–Durden and Yamaguchi workflows |
| 18 | SSAR compact-pol Stokes, m-chi, m-delta and m-alpha |
| 19 | End-to-end polarimetric capstone |

## Polarimetric conventions

- **LSAR:** full polarimetry is treated as HH/HV/VH/VV.
- **SSAR:** compact/hybrid polarimetry is treated as RH/RV.
- The polarimetric modules consume the persisted workflow spatial subset rather than introducing a second participant-facing AOI workflow.
- Complex off-diagonal covariance terms are retained as complex quantities; they are not replaced by magnitudes.
- The standard C3 → Pauli T3 transformation is implemented as a unitary basis transformation with the complex-conjugate relationship required for Hermitian covariance matrices.

## Memory model

Large NISAR HDF5 products are **not** included in this repository. Source products remain on local storage. The workflow reads only the required layers for the persisted subset, with a memory guard applied before large covariance arrays are loaded.

A **16 GB RAM** system is the target for the hands-on workflow; actual requirements depend on the selected product, AOI and analysis.

## Data

Do not commit NISAR HDF5 products, NetCDF products, generated outputs, credentials, or local session state to this repository.

Users should obtain NISAR products through the appropriate official data distribution mechanisms and comply with the applicable data terms.

See [Data and Reproducibility](docs/data_and_reproducibility.md).

## Installation

### Recommended: Conda

```bash
conda env create -f environment.yml
conda activate nisar-training
python -m ipykernel install --user --name nisar-training --display-name "NISAR Training"
jupyter lab
```

Then open the notebooks in `notebooks/` and select the **NISAR Training** kernel.

### Windows workshop helpers

The repository retains tested Windows helpers under `tools/windows/`:

- `INSTALL_NISAR_TRAINING.bat`
- `START_NISAR_TRAINING.bat`
- `CHECK_NISAR_TRAINING.bat`

They are convenience scripts for Windows/Miniconda deployments, not a replacement for understanding the documented environment.

## Quick start

1. Install Miniconda/Conda.
2. Create the `nisar-training` environment.
3. Launch JupyterLab from the repository root.
4. Select the **NISAR Training** kernel.
5. Start with `notebooks/01_Setup_and_Product_Selection.ipynb`.
6. Continue through Modules 01–12 for the GCOV foundation.
7. Use Modules 13–19 for polarimetric analysis when an appropriate LSAR or SSAR product is available.

See [docs/installation.md](docs/installation.md) and [docs/training_workflow.md](docs/training_workflow.md).

## Scientific status and limitations

This is a research and training toolkit, not an operational production processor.

The repository includes regression tests for numerical and structural behavior, including complex C3/T3 transformation, eigenvalue preservation, compact-pol power relationships, masking and memory-guard behavior.

Some model-based decomposition implementations, particularly Freeman–Durden and Yamaguchi-4, are provided as educational/convention-sensitive workflows and should be independently validated against an established reference implementation before quantitative publication or operational use.

Polarimetric calibration, product-version differences, sign conventions and metadata interpretation must be checked against the official product documentation for the NISAR product being analyzed.

See [Scientific Validation and Limitations](docs/scientific_validation.md).

## Testing

From the repository root:

```bash
pytest -q
python tools/audit_package.py
```

Notebook code cells are also checked for syntax/JSON validity in the public CI workflow.

## Contributing

Contributions are welcome, especially:

- bug fixes and reproducibility improvements
- scientific validation against representative NISAR products
- documentation improvements
- additional product compatibility
- tests and benchmark cases
- educational notebook improvements.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Citation

If you use this toolkit in research, teaching, presentations or derivative scientific work, please cite the software release. GitHub uses `CITATION.cff` to provide citation information through the repository's **Cite this repository** interface.

See [CITATION.cff](CITATION.cff).

A DOI can be added to the citation record when the public release is archived through Zenodo or another DOI service.

## License

The original software in this repository is released under the **Apache License 2.0**. See [LICENSE](LICENSE).

Third-party dependencies and materials remain under their respective licenses.

## Disclaimer

This project is developed and maintained independently by the author in a personal capacity. It is not an official product, endorsement, training package, or representation of the author's employer or of NASA, ISRO, SAC, JPL, ASF, the NISAR mission, or any other organization.

Users are responsible for validating scientific results and for complying with the terms applicable to any external datasets or materials they use.
