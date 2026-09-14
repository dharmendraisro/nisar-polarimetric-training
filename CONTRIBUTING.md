# Contributing

Thank you for helping improve the NISAR Polarimetric Analysis Training Toolkit.

## Before opening an issue

Please check existing issues and documentation first. For scientific problems, include enough information for another researcher to reproduce the observation.

## Bug reports

Please provide:

- operating system
- Python/Conda environment information
- NISAR product type and processing version, when available
- LSAR or SSAR mode
- frequency
- module/notebook name and section
- exact error message or traceback
- expected behavior
- observed behavior
- a minimal reproducible example when possible.

Do **not** upload restricted, private or very large NISAR data to an issue. Describe the relevant product structure instead.

## Scientific validation reports

For numerical or polarimetric issues, identify the reference equation, publication, official documentation, SNAP/PolSARpro comparison, or other reference implementation used to establish the expected result.

## Pull requests

1. Create a focused branch.
2. Make the smallest change that solves the problem.
3. Add or update tests when behavior changes.
4. Run `pytest -q`.
5. Run `python tools/audit_package.py`.
6. Check affected notebooks for valid JSON and executable code syntax.
7. Explain the scientific or technical rationale in the pull request.

## Contributions and licensing

By intentionally submitting a contribution for inclusion in this project, you confirm that you have the right to submit it and that, unless separately agreed in writing, the contribution may be distributed under the Apache License 2.0 terms applicable to this project.

Please do not submit third-party code or material unless its licensing permits the proposed use.
