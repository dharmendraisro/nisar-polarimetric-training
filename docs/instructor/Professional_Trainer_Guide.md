# Professional Trainer Guide

The core teaching point, repeated throughout: discovery-driven processing.
Show how filename tokens hint at the instrument, level, product, mode, and
polarization, then validate that hint against what's actually in the
HDF5 file. Don't teach `/science/LSAR/...` as if it were a universal path —
GCOV frequencies and polarization terms differ by acquisition mode, and
that's exactly the point being demonstrated.

Suggested checkpoints as you move through the modules: filename parse →
HDF5 discovery → session persistence → dynamic term list → AOI/window →
QC → visualization → export/QGIS.
