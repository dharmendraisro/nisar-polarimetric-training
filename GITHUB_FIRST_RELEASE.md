# GitHub First Public Release — v1.0.0

This document is the maintainer checklist for publishing the prepared repository as a new public GitHub project.

## 1. Before publication

- Confirm that the original code, notebooks and documentation are yours to release under Apache-2.0 in your personal capacity.
- Confirm that no employer-confidential material, internal documents, credentials, private paths or restricted datasets are present.
- Confirm that third-party material remains under its original terms.
- Replace `<YOUR-GITHUB-USERNAME>` in `CITATION.cff`.

## 2. Create the GitHub repository

Recommended repository name:

`nisar-polarimetric-training`

Recommended description:

`Open-source Python/Jupyter training and research toolkit for NISAR L2 GCOV full- and compact-polarimetric analysis.`

Recommended visibility:

**Public**

Do not initialize the GitHub repository with another README, license or `.gitignore` because this prepared repository already contains them.

## 3. Local Git setup

From the repository root:

```bash
git init -b main
git add .
git status
git commit -m "Initial public release v1.0.0"
```

Then add the GitHub remote shown by GitHub and push:

```bash
git remote add origin https://github.com/<YOUR-GITHUB-USERNAME>/nisar-polarimetric-training.git
git push -u origin main
```

## 4. Recommended GitHub repository settings

- Keep the repository public.
- Enable Issues.
- Enable Discussions later if community activity justifies them.
- Enable Dependabot alerts and dependency review/security features available for the public repository.
- Review the repository Community Standards page and confirm README, license, contribution guidance and code of conduct are detected.
- Add topics such as `nisar`, `sar`, `polarimetry`, `remote-sensing`, `earth-observation`, `gcov`, `jupyter`, `python`.

## 5. Create the v1.0.0 release

Create a GitHub Release from the `main` commit.

Tag:

`v1.0.0`

Release title:

`v1.0.0 — Initial Public Release`

Suggested release notes:

> Initial public release of the NISAR Polarimetric Analysis Training Toolkit. Includes 19 Jupyter modules covering NISAR L2 GCOV foundations, LSAR full polarimetry, SSAR compact/hybrid polarimetry, QC, visualization, GIS export, polarimetric decompositions, regression tests and documentation.

The repository itself is the primary source distribution. A clean release ZIP may be attached as an optional workshop convenience artifact.

## 6. DOI / archival release

After the GitHub release is public, optionally connect the repository to Zenodo and archive v1.0.0. Once a DOI is assigned, update `CITATION.cff` and the README with the DOI.

## 7. Do not upload

Never upload:

- NISAR HDF5/NetCDF mission products
- generated GeoTIFFs
- private or restricted data
- credentials or tokens
- `config/user_session.json`
- local Conda environments
- `.pytest_cache` or `__pycache__`

## 8. First post-release workflow

Use GitHub Issues for reproducible bugs and scientific validation reports. Use pull requests for changes. Keep `main` releasable and use tagged releases for stable versions.
