# Scientific Validation and Limitations

## Validation status of v1.0.0

The public release includes automated tests and static notebook/package audits. These tests cover structural behavior and selected numerical relationships, including complex covariance transformation, eigenvalue preservation, compact-polarimetric power relationships, masking and memory-guard behavior.

The release should be regarded as a **research and training toolkit**, not an operational production processor. Real-product validation remains product-dependent and should be performed before publication or operational use.

## Full polarimetry

The LSAR path uses a symmetrized C3 representation and the standard Pauli-basis T3 transformation for eigen-based analysis. Complex off-diagonal terms must remain complex; replacing them by magnitudes changes polarimetric information.

## Compact polarimetry

The SSAR path uses RH/RV compact/hybrid-pol quantities and derives Stokes parameters and m-chi, m-delta and m-alpha observables. Sign and convention choices should be checked against the product convention and an independent reference when quantitative comparison is required.

## Model-based decompositions

Freeman–Durden and Yamaguchi-4 are included as educational/model-based workflows. Their implementation choices and conventions should be independently validated against an established reference implementation such as SNAP or PolSARpro before quantitative publication.

## Calibration and metadata

Product-specific polarimetric calibration status, metadata flags, processing versions and official product documentation take precedence over assumptions made by a training notebook.
