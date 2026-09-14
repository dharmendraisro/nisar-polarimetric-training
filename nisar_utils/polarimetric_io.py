# SPDX-License-Identifier: Apache-2.0
"""Polarimetric I/O built around the authoritative persisted spatial subset."""
from __future__ import annotations
from pathlib import Path
import h5py
import numpy as np
from .config import load_config, save_session
from .polarimetry import polarimetric_memory_guard
from .gcov import read_gcov_mask

FULL_POL_DIAGONAL = ("HHHH", "HVHV", "VVVV")
FULL_POL_OFFDIAGONAL = ("HHHV", "HHVV", "HVVV")
FULL_POL_TERMS = FULL_POL_DIAGONAL + FULL_POL_OFFDIAGONAL
COMPACT_POL_TERMS = ("RHRH", "RHRV", "RVRV")

def get_authoritative_subset(cfg=None):
    """Return the exact r0/r1/c0/c1 subset saved by Module 06.

    No new AOI is created here. The persisted spatial_subset is authoritative.
    """
    cfg = cfg or load_config()
    sp = cfg.get("spatial_subset")
    if not sp:
        raise RuntimeError("No persisted spatial_subset found. Run Module 06 first.")
    required = {"r0","r1","c0","c1"}
    missing = required-set(sp)
    if missing:
        raise RuntimeError(f"persisted spatial_subset is missing keys: {sorted(missing)}")
    r0,r1,c0,c1 = [int(sp[k]) for k in ("r0","r1","c0","c1")]
    if not (r0 < r1 and c0 < c1):
        raise ValueError(f"Invalid persisted spatial_subset: {sp}")
    return {"r0":r0,"r1":r1,"c0":c0,"c1":c1}

def subset_slices(spatial_subset):
    sp = spatial_subset
    return slice(int(sp["r0"]),int(sp["r1"])), slice(int(sp["c0"]),int(sp["c1"]))

def detect_polarimetric_mode(h5_path, frequency=None):
    """Detect the training branch from actual GCOV datasets, not filename guesses.

    LSAR_FULL_POL requires all three diagonal terms AND all three
    off-diagonal terms -- Module 14's loader (load_branch_terms with
    FULL_POL_TERMS) needs the complete six-term upper-triangular set and
    will raise KeyError on anything less, so classifying a partial product
    as full-pol here would just defer that failure to a less obvious
    place. A product with, say, only HHHV and not HHVV/HVVV falls through
    to UNSUPPORTED instead.
    """
    h5_path=Path(h5_path)
    with h5py.File(h5_path,"r") as f:
        candidates=[]
        for family in ("LSAR","SSAR"):
            gp=f"/science/{family}/GCOV/grids"
            if gp not in f: continue
            freqs=list(f[gp].keys())
            for freq in freqs:
                if frequency and freq != frequency: continue
                base=f"{gp}/{freq}"
                names=set(f[base].keys())
                fp=all(x in names for x in FULL_POL_DIAGONAL) and all(x in names for x in FULL_POL_OFFDIAGONAL)
                cp=all(x in names for x in COMPACT_POL_TERMS)
                candidates.append((family,freq,names,fp,cp))
        if not candidates:
            raise RuntimeError("No supported NISAR GCOV family/frequency found.")
        # Prefer a complete supported branch; otherwise report the first discovered grid.
        for family,freq,names,fp,cp in candidates:
            if family=="LSAR" and fp:
                return {"mode":"LSAR_FULL_POL","family":family,"frequency":freq,"base":f"/science/{family}/GCOV/grids/{freq}","terms":sorted(names)}
        for family,freq,names,fp,cp in candidates:
            if family=="SSAR" and cp:
                return {"mode":"SSAR_COMPACT_POL","family":family,"frequency":freq,"base":f"/science/{family}/GCOV/grids/{freq}","terms":sorted(names)}
        return {"mode":"UNSUPPORTED","family":candidates[0][0],"frequency":candidates[0][1],"base":f"/science/{candidates[0][0]}/GCOV/grids/{candidates[0][1]}","terms":sorted(candidates[0][2])}

def save_detected_mode(result):
    save_session({"polarimetric_mode":result["mode"],"polarimetric_family":result["family"],"polarimetric_frequency":result["frequency"],"polarimetric_base":result["base"]})

def load_detected_mode(cfg=None):
    """Return the detected polarimetric branch, from cache if present.

    Both branches return the same four-key shape
    (polarimetric_mode/family/frequency/base) regardless of whether the
    session already had it cached or this call just detected it fresh --
    detect_polarimetric_mode() itself returns a differently-named "mode"
    key (plus a "terms" list this function doesn't expose), so returning
    that raw result on a cache miss used to hand callers a dict that
    didn't have the key they immediately look up (mode['polarimetric_mode']),
    which only ever worked by accident because Module 13 always runs
    first in the normal curriculum and pre-populates the cache via
    save_detected_mode() before any of Modules 14-19 call this.
    """
    cfg=cfg or load_config()
    if cfg.get("polarimetric_mode"): return {k:cfg.get(k) for k in ("polarimetric_mode","polarimetric_family","polarimetric_frequency","polarimetric_base")}
    result=detect_polarimetric_mode(cfg["nisar_file"],cfg.get("default_frequency"))
    save_detected_mode(result)
    return {"polarimetric_mode":result["mode"],"polarimetric_family":result["family"],"polarimetric_frequency":result["frequency"],"polarimetric_base":result["base"]}

def _subset_shape_and_dtypes(h5_path, base_group, terms, spatial_subset):
    rs, cs = subset_slices(spatial_subset)
    shape = None
    dtypes = {}
    with h5py.File(h5_path, "r") as f:
        for term in terms:
            p = f"{base_group.rstrip('/')}/{term}"
            if p not in f:
                raise KeyError(f"Required covariance term not found: {p}")
            ds = f[p]
            if len(ds.shape) != 2:
                raise ValueError(f"Expected 2-D GCOV raster for {p}; found shape {ds.shape}")
            shape = (int(rs.stop) - int(rs.start), int(cs.stop) - int(cs.start))
            dtypes[term] = str(ds.dtype)
    if shape is None:
        raise ValueError("No polarimetric terms requested")
    return shape, dtypes

def read_terms_for_subset(h5_path, base_group, terms, spatial_subset):
    rs,cs=subset_slices(spatial_subset)
    out={}
    with h5py.File(h5_path,"r") as f:
        for term in terms:
            p=f"{base_group.rstrip('/')}/{term}"
            if p not in f: raise KeyError(f"Required covariance term not found: {p}")
            out[term]=f[p][rs,cs]
    return out

def apply_mask_to_terms(data, invalid_mask):
    """Set MASK == 0 pixels to NaN across every term in `data`.

    Unlike nisar_utils.gcov.apply_gcov_mask() -- which only touches
    real-valued diagonal channels, since Modules 07/08 never plot the
    complex off-diagonal ones -- the polarimetric reconstruction and
    decomposition modules (14-19) use every term numerically, diagonal
    and complex off-diagonal alike. A transmit-gap or other invalid pixel
    has to be masked in all of them, not just the ones that get plotted,
    or the covariance matrix at that pixel would mix valid and invalid
    channels.
    """
    masked = {}
    for term, arr in data.items():
        arr = np.asarray(arr)
        if arr.shape != invalid_mask.shape:
            raise ValueError(
                f"{term} shape {arr.shape} does not match MASK shape {invalid_mask.shape}."
            )
        out = arr.astype(np.complex128) if np.iscomplexobj(arr) else arr.astype(np.float64)
        out = out.copy()
        out[invalid_mask] = np.nan
        masked[term] = out
    return masked

def load_branch_terms(cfg, terms):
    sp=get_authoritative_subset(cfg)
    mode=load_detected_mode(cfg)
    shape, dtypes = _subset_shape_and_dtypes(cfg["nisar_file"], mode["polarimetric_base"], terms, sp)
    guard=polarimetric_memory_guard(shape,n_complex_terms=len(terms))
    if not guard["safe"]:
        raise MemoryError(f"AOI exceeds the polarimetric 16-GB training budget; no arrays were loaded: {guard}")
    data=read_terms_for_subset(cfg["nisar_file"],mode["polarimetric_base"],terms,sp)
    rs, cs = subset_slices(sp)
    with h5py.File(cfg["nisar_file"], "r") as f:
        invalid_mask, _ = read_gcov_mask(f, mode["polarimetric_base"], rs.start, rs.stop, cs.start, cs.stop)
    data = apply_mask_to_terms(data, invalid_mask)
    guard["dataset_dtypes"] = dtypes
    guard["loaded_after_preflight"] = True
    guard["masked_pixel_count"] = int(np.count_nonzero(invalid_mask))
    return data,sp,guard,mode
