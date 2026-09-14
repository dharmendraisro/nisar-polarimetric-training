# SPDX-License-Identifier: Apache-2.0
import matplotlib.pyplot as plt
import numpy as np
from .statistics import robust_limits

# Ordered by scientific preference for the training RGB composite.
# Both channels in each pair are real-valued diagonal GCOV terms.
RGB_PAIR_CANDIDATES = (
    ("HHHH", "HVHV"),
    ("VVVV", "VHVH"),
    ("RHRH", "RVRV"),
)

def select_rgb_pair(available_terms):
    """Return the preferred real-valued co-pol/cross-pol pair, or None.

    HHHH/HVHV is preferred for H-pol dual-pol and quad-pol LSAR products.
    VVVV/VHVH is the fallback for V-pol-only LSAR dual-pol products or
    quad-pol products where the H pair is unavailable. RHRH/RVRV is the
    compact-pol fallback for SSAR products, which never carry HHHH/VVVV
    terms at all. Complex covariance terms are intentionally excluded from
    this selection.
    """
    available = {str(t).upper() for t in (available_terms or [])}
    for co_pol, cross_pol in RGB_PAIR_CANDIDATES:
        if co_pol in available and cross_pol in available:
            return co_pol, cross_pol
    return None

def plot_gcov(a,title='',vmin=None,vmax=None,ax=None):
    if ax is None: _,ax=plt.subplots(figsize=(8,6))
    if vmin is None or vmax is None: vmin,vmax=robust_limits(a)
    im=ax.imshow(a,vmin=vmin,vmax=vmax)
    ax.set_title(title); plt.colorbar(im,ax=ax,label='GCOV')
    return ax

def plot_complex_term(arr, name, ax_mag=None, ax_phase=None):
    """Plot magnitude (dB) and phase (degrees) of a complex covariance term.

    This is the QC step off-diagonal complex channels (HHHV/HHVV/HVVV for
    full-pol, RHRV for compact-pol) never got: a calibration artifact,
    phase wrap, or residual transmit-gap contamination that survived
    masking shows up here directly, in the channel it actually came from,
    rather than only indirectly -- if at all -- in a downstream H-A-alpha
    or Stokes result several steps later. MASK==0 pixels are already NaN
    by the time this is called (load_branch_terms handles that), so they
    render as blank/transparent rather than as valid-looking data.
    """
    arr = np.asarray(arr)
    mag_db = 10.0 * np.log10(np.abs(arr) ** 2 + 1e-12)
    phase_deg = np.degrees(np.angle(arr))

    if ax_mag is None or ax_phase is None:
        _, (ax_mag, ax_phase) = plt.subplots(1, 2, figsize=(12, 5))

    vmin, vmax = robust_limits(mag_db)
    im1 = ax_mag.imshow(mag_db, vmin=vmin, vmax=vmax, cmap="gray")
    ax_mag.set_title(f"{name} magnitude (dB)")
    plt.colorbar(im1, ax=ax_mag, label="dB")

    im2 = ax_phase.imshow(phase_deg, vmin=-180, vmax=180, cmap="twilight")
    ax_phase.set_title(f"{name} phase (deg)")
    plt.colorbar(im2, ax=ax_phase, label="degrees")

    return ax_mag, ax_phase
