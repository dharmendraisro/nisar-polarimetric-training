# SPDX-License-Identifier: Apache-2.0

import numpy as np
from .hdf5 import open_h5, inspect_dataset

MASKED_GCOV_TERMS = ("HHHH", "HVHV", "VVVV", "VHVH", "RHRH", "RVRV")

def read_gcov_mask(h5_file, grid_path, row_start, row_end, col_start, col_end):
    """Read the GCOV validity mask on the same window as everything else.

    Returns (invalid_mask, mask_arr): a boolean array that's True wherever
    MASK == 0, alongside the raw mask values (useful for reporting counts).
    Raises if the mask dataset is missing or its shape doesn't match the
    requested window -- silently proceeding on a shape mismatch would mean
    masking the wrong pixels.
    """
    mask_path = f"{grid_path}/mask"
    try:
        mask_arr = np.asarray(read_window(h5_file, mask_path, row_start, row_end, col_start, col_end))
    except Exception as exc:
        raise RuntimeError(f"Unable to read required GCOV MASK dataset: {mask_path}") from exc
    expected_shape = (row_end - row_start, col_end - col_start)
    if mask_arr.shape != expected_shape:
        raise ValueError(
            f"GCOV MASK shape {mask_arr.shape} does not match the "
            f"selected subset shape {expected_shape}."
        )
    return mask_arr == 0, mask_arr

def apply_gcov_mask(arr, term, invalid_mask, mask_terms=MASKED_GCOV_TERMS):
    """Set MASK == 0 pixels to NaN in a real-valued Gamma-0 channel.

    Terms outside `mask_terms` (complex off-diagonal channels, which this
    training package never plots) are returned unchanged, cast to float64.
    """
    arr = np.asarray(arr, dtype=np.float64)
    if term not in mask_terms:
        return arr
    if arr.shape != invalid_mask.shape:
        raise ValueError(f"{term} shape {arr.shape} does not match MASK shape {invalid_mask.shape}.")
    out = arr.copy()
    out[invalid_mask] = np.nan
    return out


def open_gcov(filename): return open_h5(filename)

def get_gcov_root(profile):
    if not profile.gcov_root: raise ValueError("No GCOV root discovered.")
    return profile.gcov_root

def get_frequency_path(profile, frequency):
    if frequency not in (profile.frequencies or []):
        raise ValueError(f"Frequency {frequency!r} is not available.")
    return f"{profile.gcov_root}/grids/{frequency}"

def get_grid_coordinates(h5_file, grid_path):
    return h5_file[f"{grid_path}/xCoordinates"][:], h5_file[f"{grid_path}/yCoordinates"][:]

def get_projection_info(h5_file, grid_path):
    return dict(h5_file[f"{grid_path}/projection"].attrs.items())

def read_window(h5_file, dataset_path, row_start, row_end, col_start, col_end):
    return h5_file[dataset_path][row_start:row_end, col_start:col_end]

def read_term(h5_file, profile, frequency, term, row_start, row_end, col_start, col_end):
    if term not in profile.covariance_terms.get(frequency, []):
        raise ValueError(f"{term} is not available in {frequency}.")
    return read_window(h5_file, f"{get_frequency_path(profile,frequency)}/{term}",
                       row_start,row_end,col_start,col_end)

def list_gcov_datasets(h5_file, frequency_path):
    return [n for n,o in h5_file[frequency_path].items() if hasattr(o,"shape")]
