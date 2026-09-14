NISAR GCOV TRAINING — PARTICIPANT SETUP

FIRST TIME
1. Install Miniconda for Windows.
2. Extract the whole training package — don't cherry-pick files out of it.
3. Open the Miniconda Prompt.
4. cd into the package root.
5. Run INSTALL_NISAR_TRAINING.bat.
6. Run START_NISAR_TRAINING.bat.
7. In Jupyter, select the "NISAR Training" kernel.
8. Run the package's system check before opening Module 01.

EVERY TIME AFTER THAT
1. Open the Miniconda Prompt.
2. cd into the package root.
3. Run START_NISAR_TRAINING.bat.

PLEASE DON'T
- create a second Conda environment for this
- pip-install extra packages into it
- move or rename nisar_utils
- rename any of the package folders
- copy someone else's environment onto your machine

environment.yml is the source of truth for dependencies. The environment
itself is named nisar-training.

ON MULTI-FREQUENCY PRODUCTS
If your GCOV product has more than one frequency, Module 02 will stop and
ask you to pick one. That choice is saved as default_frequency and used by
every module after it — don't skip past this step, the rest of the
workflow depends on it being set.

MAPPING FEATURES: an OpenStreetMap basemap, footprint maps built from the
actual product geometry, optional GIS overlays, interactive AOI drawing,
and map-aware GCOV visualization throughout.
