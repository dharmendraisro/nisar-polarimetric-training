# Teaching Notes — NISAR GCOV & Polarimetric Analysis Training

A facilitation companion to the 12-notebook GCOV curriculum. It sits
alongside `instructor_notes/Professional_Trainer_Guide.md` rather than
replacing it — that guide states the core philosophy in a paragraph
(discovery-driven processing, nothing hard-coded); this document walks
through what that looks like module by module, with talking points, demo
cues, and a few pitfalls worth heading off before they happen.

This covers Modules 01–12, the frozen GCOV core. The polarimetric
extension (Modules 13–19 — mode discovery, full-pol covariance
reconstruction, eigen/Cloude–Pottier, Pauli/Freeman–Durden/Yamaguchi, and
compact-pol Stokes decompositions) reuses the same AOI from Module 06 and
the same discovery-driven approach, but it's still a development/
scientific-validation release. Treat 13–19 as instructor-led demos for now
rather than assessed capstone work the way Module 11 is.

Who this is for: participants comfortable reading Python but possibly new
to SAR or HDF5. It runs as a single intensive day (roughly 6–7 hours across
all 12 modules) or splits cleanly into two days after Module 06. Send the
install guide out ahead of time, and make clear that Miniconda +
`INSTALL_NISAR_TRAINING.bat` need to be done *before* people arrive — Module
01 assumes a working `nisar-training` kernel is already there.

---

## Before anyone sits down

`default_frequency` auto-detects by default, which is fine for a
single-frequency product. If the sample product you're handing out has
more than one frequency, Module 02 will stop and prompt for a choice — and
if twenty people hit that prompt independently at the same moment, you'll
spend the first ten minutes fielding the same question over and over. Walk
through it together as the first live action of the day instead.

Two more things worth checking before the room fills up: that the sample
`.h5` file (supplied separately — the package itself carries no NISAR
data) is actually reachable from every machine, and that everyone's kernel
picker shows **NISAR Training**, not a bare `Python 3`. If it's the latter,
`INSTALL_NISAR_TRAINING.bat` didn't register the kernel properly — fix that
before Module 01, not mid-session.

---

## Module 01 — Setup, Product Selection & First Map

The goal is simple: go from "a path to an .h5 file" to "I can see this
scene on a map," in one sitting. The footprint comes from the product's own
geocoded grid and CRS, not from anything hard-coded — worth pointing out
explicitly, since it's the first example of a pattern the whole curriculum
leans on.

Show both footprint views back to back: static matplotlib, then the
interactive Folium/OSM one. The static version is what has to work if the
room's internet is unreliable; the interactive one is a bonus on top.

The notebook's own checkpoint asks where the scene is, what its footprint
looks like, and which CRS it uses. Don't let people skim past this — get
them to actually say the EPSG code out loud. They'll need it later to
sanity-check output from half the other modules.

One thing to flag up front: the interactive map needs live internet for
OSM tiles. If connectivity in the room is shaky, tell people the static
map is the one that has to work.

## Module 02 — Persistent Session & Product Orientation

This identifies the product properly, discovers which frequencies and
polarizations this specific file actually has, and locks in a frequency
choice that gets saved to `config/user_session.json` for every later module
to read back.

This is where the multi-frequency prompt from the pre-session checklist
shows up, if it wasn't pre-empted. It's a good moment to explain *why*
session persistence exists — so nobody has to re-answer "which frequency?"
in Modules 03 through 11. Also worth stressing: the frequency/polarization
list comes from the HDF5 file itself, not from parsing the filename. The
filename is treated as a hint and cross-checked, never trusted outright —
a useful contrast to draw if anyone's used tools that do it the naive way.

Checkpoint: once a frequency is picked, tie it back to the Module 01
footprint — same scene, now with a frequency attached to it.

## Module 03 — L1 Product Explorer, Metadata First

The whole point here is reading metadata before touching any pixel data —
shape, units, validity, all of it, read first. It's the antidote to "just
load the array and see what happens."

There's an optional GIS-layer overlay step (GeoJSON, Shapefile,
GeoPackage, auto-reprojected to WGS84) that's skippable with Enter. Unless
someone specifically wants to go down that road, don't let debugging a
participant's own shapefile eat into workshop time.

## Module 04 — L2 GCOV Product Explorer

Here's the conceptual heart of the whole curriculum: diagonal covariance
terms (HHHH, HVHV, VVVV, VHVH) are real-valued power, off-diagonal terms
are complex and carry phase/coherence information. Every visualization and
export decision from Module 08 onward traces back to that one distinction,
so it's worth slowing down here rather than rushing to the next module.

If the audience's real interest is backscatter-based retrieval — soil
moisture cal/val, for instance — this is the natural point to connect the
diagonal terms to the σ⁰ backscatter channels they'll actually use in
practice. The notebook itself stays generic and instrument-agnostic on
purpose, so that connection has to come from you, not the material.

## Module 05 — Large-Data Performance & Windowed Access

The technique here — reading a chunked window instead of loading the full
array — isn't academic. A full-resolution GCOV frame genuinely won't fit
comfortably in memory on a 16 GB training laptop, and that same number
resurfaces in Module 08 as its visualization budget. Mention it now so it
isn't a surprise three modules later.

## Module 06 — Spatial Subsetting with AOI Validation

The AOI gets defined in lat/lon, checked against the real scene extent,
and the resulting pixel indices (`r0, r1, c0, c1`) get handed off to
everything downstream. Lat/lon bounding box is the *only* method enabled in
this version — pixel/row-column and projected X/Y exist in the code but
are switched off on purpose. Say this explicitly, since participants
coming from other SAR toolchains may go looking for a pixel-coordinate
option that simply isn't there.

If time allows, demonstrate both failure modes live: an AOI that's
entirely outside the scene (hard stop) and one that partially overlaps
(flagged, needs confirmation). Seeing both makes "validated against the
actual grid" concrete rather than abstract.

This is also the natural place to break if you're running two days —
everything from here on depends on the AOI chosen at this point.

## Module 07 — QC, Statistics, Masks & Dynamic Polarization

Masks and statistics get computed generically, over whatever polarization
terms the product actually has. The "dynamic" part is doing real work: the
same code runs on a dual-pol or quad-pol product because it discovers the
term list rather than assuming HH/HV — the same discipline from Module 02,
just applied to statistics instead of session state.

## Module 08 — Dynamic Visualization & RGB Composite

R = co-pol (dB), G = cross-pol (dB), B = the co-pol/cross-pol ratio (dB).
HHHH/HVHV is preferred; the notebook falls back to VVVV/VHVH automatically
when the H-pol pair isn't there, and skips the RGB step entirely (with a
clear message) if neither pair exists. If you have a VV/VH-only product
handy, demo it — actually watching the fallback trigger lands better than
describing it.

Complex terms are never plotted, full stop — a good moment to circle back
to the Module 04 real/complex distinction and show it as a concrete design
choice rather than a rule stated in the abstract.

The visualization budget caps out at 4,000,000 pixels for a 16 GB
workstation. If the Module 06 AOI is bigger than that, only the
*displayed* arrays get downsampled — the full-resolution data and
geographic extent are untouched, and that's what Modules 09/10 actually
export. Make sure nobody walks away thinking the on-screen resolution is
what ends up in the exported file.

## Module 09 — Advanced: Frequency Masks, Metadata & Batch Processing

Batch mask/statistics generation across terms, and — worth calling out
explicitly — the start of native-resolution GeoTIFF export. GeoTIFF export
shows up in both Module 09 and Module 10; say so up front so it doesn't
read as an accident. Module 09 does the export itself, tied to the Module
06 AOI indices; Module 10 is where the QGIS validation happens. If you're
tight on time, these two are the easiest pair to fold into one block
without losing anything.

## Module 10 — GeoTIFF Export & QGIS Validation

Confirms the exported GeoTIFFs open correctly in QGIS, in the right
CRS/extent, matching the Module 06 AOI. The native CRS/EPSG from the
product profile is preserved with no reprojection or resampling — this is
the payoff for the "record the EPSG code" checkpoint back in Module 01.
Participants should be able to open QGIS and confirm the number matches
what they wrote down hours earlier.

If QGIS is installed in the room, make this a genuine hands-on step rather
than a demo — someone opening their own exported file is a lot more
convincing than watching you do it.

## Module 11 — End-to-End Capstone

Run the full pipeline start to finish, on a product of the participant's
choosing or a second sample product you supply. Treat this as an
assessment rather than a lecture — walk around, don't drive the notebook
for anyone. The clearest signal that the core discipline hasn't landed yet
is a participant who re-hardcodes a frequency or AOI instead of letting
the session carry it forward from earlier modules.

A rough capstone rubric: can they explain why their AOI was accepted or
flagged? Can they say which RGB pair got selected, and why (or why it was
skipped)? Can they state their exported GeoTIFF's CRS without opening the
file to check?

## Module 12 — Trainer Troubleshooting & Session Management

This one's for you, not the participants — session-state issues and a few
performance-tuning notes. Read it before the workshop. If you find
yourself consulting it live, that's usually a sign the pre-session
checklist above didn't get fully done.

---

## Three things worth repeating all day

Say each of these more than once, in different words, rather than stating
them once and moving on:

1. **Discover, don't hard-code.** Filenames, frequencies, polarization
   terms, footprints, CRS — all of it comes from the actual product, with
   filename hints cross-checked rather than trusted outright.
2. **Real and complex covariance terms are a hard boundary.** Diagonal
   terms (HHHH, VVVV, HVHV, VHVH) are real and get visualized/exported.
   Off-diagonal terms are complex and are never plotted, ever.
3. **Session state carries forward, so early decisions matter later.** The
   Module 02 frequency and the Module 06 AOI are what every later module
   depends on. If something looks wrong downstream, check those two before
   assuming it's a code bug.

## Adapting this for a soil-moisture cal/val audience

The curriculum stays deliberately generic and instrument-agnostic, so the
backscatter-retrieval framing has to come from you, verbally — it's not in
the notebooks. Two good places to add it:

- **Module 04**, introducing the diagonal terms: call HHHH/HVHV/VVVV/VHVH
  the σ⁰ backscatter channels used in retrieval algorithms, not just "the
  real-valued terms."
- **Module 08**, when the RGB composite renders: the co-pol/cross-pol
  ratio in the blue channel is the same kind of quantity used as a
  vegetation/roughness proxy in many soil-moisture retrieval schemes —
  participants coordinating with SRSACs on cal/val work will likely
  recognize it.
