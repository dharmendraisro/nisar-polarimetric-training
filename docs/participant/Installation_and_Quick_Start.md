# Participant Installation and Quick Start

## System

- Windows 10/11 64-bit is the primary tested workshop platform.
- 16 GB RAM or more is recommended.
- Local SSD storage is preferred for large HDF5 products.
- Internet is needed for initial software installation and optional online mapping; core processing can run from local software and data after setup.

## One-time setup

1. Install Miniconda.
2. Clone/download the repository.
3. From the repository root, create the environment:

```bash
conda env create -f environment.yml
conda activate nisar-training
python -m ipykernel install --user --name nisar-training --display-name "NISAR Training"
```

4. Start JupyterLab from the repository root:

```bash
jupyter lab
```

5. Select the **NISAR Training** kernel.

Windows workshop helpers are available under `tools/windows/`.

## Training sequence

Foundation: **Modules 01–12**.

Polarimetric extension: **Modules 13–19**.

Start with:

`notebooks/01_Setup_and_Product_Selection.ipynb`

## Data

Keep large NISAR HDF5 products outside the software environment, for example:

```text
D:\NISAR_Data\
    NISAR_product.h5
```

Do not upload mission products to GitHub.

## If something fails

Run:

```bash
python tools/audit_package.py
```

For reproducible problems, open a GitHub issue and include the module, operating system, environment, product mode/frequency, exact error and relevant workflow context. Do not attach restricted or very large mission datasets.
