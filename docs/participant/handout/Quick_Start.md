# NISAR GCOV Training — Quick Start

Install Miniconda once, run INSTALL_NISAR_TRAINING.bat, then
START_NISAR_TRAINING.bat, pick the NISAR Training kernel, and open Module
01.

From the first module on you'll see the product's footprint on a map, and
that geographic thread carries through metadata, AOI, subsetting,
visualization, and GeoTIFF export.

**If your product has more than one frequency:** Module 02 will ask you to
pick one. That choice is saved as `default_frequency` and every later
module relies on it — don't skip past this step.

The interactive map needs internet access for the OpenStreetMap tiles.
The static footprint maps work fine offline either way.

## One thing worth planning for

`default_frequency` is set to auto-detect by default, which is fine for a
single-frequency product. If your sample product has more than one
frequency, Module 02 will pause and prompt for a choice — worth walking
through that prompt together as the first live step of the session, rather
than letting everyone hit it independently and ask you about it at once.
