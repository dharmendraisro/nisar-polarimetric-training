# Installation

## Recommended environment

The tested environment is defined in the repository root as `environment.yml`.

```bash
conda env create -f environment.yml
conda activate nisar-training
python -m ipykernel install --user --name nisar-training --display-name "NISAR Training"
jupyter lab
```

Launch JupyterLab from the repository root so that the notebooks can locate `nisar_utils`, `config`, and the project resources.

## Windows

For Windows/Miniconda workshop deployment, the convenience scripts are in `tools/windows/`.

If you run them manually, execute them from the repository root or adjust the working directory as documented by the script.

## Data storage

Keep large NISAR HDF5 products outside the Conda environment, preferably on local SSD storage. The software repository should contain code and documentation, not mission data files.

## Kernel

Select **NISAR Training** (`nisar-training`) in JupyterLab.
