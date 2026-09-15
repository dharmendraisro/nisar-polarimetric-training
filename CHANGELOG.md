# Changelog

## [1.1.0] — 2026-09-15

### Large-scene processing and robustness update

- Validated the training workflows across Dual-Pol, Full-Pol, and Compact-Pol paths.
- Corrected the missing NumPy import in Module 07.
- Corrected VVVV/VHVH masking behavior in Module 08.
- Revised Module 15 for memory-conscious large-AOI Full-Pol processing.
- Revised Module 16 for tile-wise Cloude–Pottier H/A/alpha processing.
- Revised Module 17 for memory-conscious Pauli, Freeman–Durden and Yamaguchi-4 processing.
- Improved handling of Yamaguchi volume-model outputs.
- Improved RGB visualization with robust percentile stretching and explicit [0,1] clipping.
- Preserved complex covariance handling and the established C3 → standard C3 → Pauli T3 scientific workflow.
- Retained full-resolution quantitative processing while separating visualization scaling from physical products.

## [1.0.0] — 2026-09-14

### Initial public release

- Public GitHub release of the NISAR Polarimetric Analysis Training Toolkit.
- 19 Jupyter notebooks covering NISAR GCOV foundations and polarimetric analysis.
- LSAR full-polarimetric workflows for HH/HV/VH/VV.
- SSAR compact/hybrid-polarimetric workflows for RH/RV.
- Persisted AOI/spatial-subset architecture carried into the polarimetric modules.
- GCOV mask handling with invalid `MASK == 0` samples represented as NaN in affected Gamma0 channels.
- Complex covariance preservation and Hermitian covariance reconstruction.
- Correct complex C3-to-standard-C3-to-Pauli-T3 transformation.
- Regression tests for complex transformation and eigenvalue preservation.
- Cloude–Pottier H/A/alpha analysis.
- Pauli, Freeman–Durden and Yamaguchi educational workflows.
- Compact-pol Stokes, m-chi, m-delta and m-alpha workflows.
- Public contribution, citation, security and community documentation.
- GitHub-ready repository layout and CI configuration.

### Development provenance

The v1.0.0 public release incorporates the results of an extensive pre-publication development and scientific-QA cycle. Internal development numbering is not part of the public release sequence.
