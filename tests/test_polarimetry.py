# SPDX-License-Identifier: Apache-2.0
import numpy as np
import h5py
from nisar_utils.polarimetry import (
    covariance_hermitian_from_terms, nisar_c3_to_standard_c3, standard_c3_to_t3,
    eigen_analysis, cloude_pottier_alpha, stokes_from_compact_terms,
    compact_child_parameters, m_chi_decomposition, m_delta_decomposition, m_alpha_decomposition,
)

def _raw_for_known_t3():
    # Desired Pauli T3 eigenvalues/eigenvectors are diag(3,2,1).
    # Inverse unitary transform gives standard C3 [[2.5,0,0.5],[0,1,0],[0.5,0,2.5]].
    return {
        "HHHH":np.array([[2.5]]), "HVHV":np.array([[0.5]]), "VVVV":np.array([[2.5]]),
        "HHHV":np.array([[0]],dtype=np.complex64), "HHVV":np.array([[0.5]],dtype=np.complex64),
        "HVVV":np.array([[0]],dtype=np.complex64)
    }

def test_nisar_c3_sqrt2_normalization_and_span():
    C=nisar_c3_to_standard_c3(covariance_hermitian_from_terms(_raw_for_known_t3()))
    assert np.allclose(np.trace(C,axis1=-2,axis2=-1),6.0)
    assert np.allclose(C[0,0],[[2.5,0,0.5],[0,1,0],[0.5,0,2.5]])

def test_cloude_pottier_known_t3_matrix():
    T=np.diag([3.0,2.0,1.0]).astype(np.complex64)[None,None,:,:]
    e=eigen_analysis(T)
    expected_p=np.array([3,2,1],float)/6
    expected_H=-np.sum(expected_p*np.log(expected_p)/np.log(3))
    assert np.allclose(e['eigenvalues'][0,0],[3,2,1])
    assert np.allclose(e['entropy'][0,0],expected_H)
    assert np.allclose(e['anisotropy'][0,0],1/3)
    a=cloude_pottier_alpha(e['eigenvectors'])[0,0]
    assert np.allclose(np.degrees(np.sum(a*e['probabilities'][0,0])),45.0)

def test_raw_nisar_covariance_to_t3_matches_known_matrix():
    T=standard_c3_to_t3(nisar_c3_to_standard_c3(covariance_hermitian_from_terms(_raw_for_known_t3())))
    assert np.allclose(T[0,0],np.diag([3,2,1]))

def test_c3_to_t3_preserves_eigenvalues():
    raw=_raw_for_known_t3()
    C=nisar_c3_to_standard_c3(covariance_hermitian_from_terms(raw))
    T=standard_c3_to_t3(C)
    ewC=np.linalg.eigvalsh(C[0,0])[::-1]
    ewT=np.linalg.eigvalsh(T[0,0])[::-1]
    assert np.allclose(ewC,ewT)

def test_compact_stokes_and_decompositions_conserve_power():
    g0,g1,g2,g3=stokes_from_compact_terms(np.array([[3.0]]),np.array([[0.5+0.5j]]),np.array([[1.0]]))
    p=compact_child_parameters(g0,g1,g2,g3)
    for parts in (m_chi_decomposition(g0,p['m'],p['chi2']),m_delta_decomposition(g0,p['m'],p['delta']),m_alpha_decomposition(g0,p['m'],p['alpha_s'])):
        total=sum(parts.values())
        assert np.allclose(total,g0,atol=1e-6)
        assert all(np.all(v>=-1e-7) for v in parts.values())

def test_memory_guard_runs_before_term_read(monkeypatch,tmp_path):
    from nisar_utils import polarimetric_io as pio
    h5=tmp_path/'x.h5'
    with h5py.File(h5,'w') as f:
        g=f.create_group('/science/LSAR/GCOV/grids/frequencyA')
        for t in pio.FULL_POL_TERMS:
            g.create_dataset(t,shape=(100,100),dtype=np.complex64)
    cfg={'nisar_file':str(h5),'spatial_subset':{'r0':0,'r1':100000,'c0':0,'c1':100000},'default_frequency':'frequencyA','polarimetric_mode':'LSAR_FULL_POL','polarimetric_family':'LSAR','polarimetric_frequency':'frequencyA','polarimetric_base':'/science/LSAR/GCOV/grids/frequencyA'}
    monkeypatch.setattr(pio,'read_terms_for_subset',lambda *a,**k: (_ for _ in ()).throw(AssertionError('term read occurred before memory guard')))
    try:
        pio.load_branch_terms(cfg,pio.FULL_POL_TERMS)
    except MemoryError:
        return
    raise AssertionError('Expected pre-read MemoryError')

def test_save_session_merges_instead_of_overwriting(tmp_path, monkeypatch):
    # Regression test for the bug where Module 13's save_detected_mode()
    # (which only ever knows about the polarimetric_* keys) silently wiped
    # out nisar_file/default_frequency/spatial_subset saved by earlier
    # modules, breaking load_config() in every module after it.
    from nisar_utils import config as cfgmod
    monkeypatch.setattr(cfgmod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cfgmod, "SESSION_FILE", tmp_path / "user_session.json")

    cfgmod.save_session({"nisar_file": str(tmp_path / "product.h5")})
    cfgmod.save_session({"nisar_file": str(tmp_path / "product.h5"), "default_frequency": "frequencyA"})
    cfgmod.save_session({
        "nisar_file": str(tmp_path / "product.h5"),
        "spatial_subset": {"r0": 0, "r1": 10, "c0": 0, "c1": 10},
    })
    # This call only supplies polarimetric_* keys, exactly like
    # nisar_utils.polarimetric_io.save_detected_mode() does.
    cfgmod.save_session({
        "polarimetric_mode": "LSAR_FULL_POL",
        "polarimetric_family": "LSAR",
        "polarimetric_frequency": "frequencyA",
        "polarimetric_base": "/science/LSAR/GCOV/grids/frequencyA",
    })

    cfg = cfgmod.load_config(require_file=False)
    assert cfg["nisar_file"] == str((tmp_path / "product.h5").resolve())
    assert cfg["default_frequency"] == "frequencyA"
    assert cfg["spatial_subset"] == {"r0": 0, "r1": 10, "c0": 0, "c1": 10}
    assert cfg["polarimetric_mode"] == "LSAR_FULL_POL"

def test_load_branch_terms_applies_gcov_mask_to_every_term(tmp_path):
    # Regression/feature test: a transmit-gap or otherwise invalid pixel
    # (MASK == 0) must be masked in *every* term load_branch_terms returns
    # -- diagonal and complex off-diagonal alike -- not just the ones that
    # get plotted directly. This is what Modules 14-19 (LSAR full-pol and
    # SSAR compact-pol alike) all rely on automatically, since they all
    # load their data through this one function.
    from nisar_utils import polarimetric_io as pio

    h5_path = tmp_path / "masked_fullpol.h5"
    shape = (4, 4)
    with h5py.File(h5_path, "w") as f:
        g = f.create_group("/science/LSAR/GCOV/grids/frequencyA")
        mask = np.ones(shape, dtype="u1")
        mask[1, 1] = 0
        mask[3, 0] = 0
        g.create_dataset("mask", data=mask)
        for t in pio.FULL_POL_DIAGONAL:
            g.create_dataset(t, data=np.full(shape, 2.0, dtype="f4"))
        for t in pio.FULL_POL_OFFDIAGONAL:
            g.create_dataset(t, data=np.full(shape, 1.0 + 1.0j, dtype="c8"))

    cfg = {
        "nisar_file": str(h5_path),
        "spatial_subset": {"r0": 0, "r1": 4, "c0": 0, "c1": 4},
        "default_frequency": "frequencyA",
        "polarimetric_mode": "LSAR_FULL_POL",
        "polarimetric_family": "LSAR",
        "polarimetric_frequency": "frequencyA",
        "polarimetric_base": "/science/LSAR/GCOV/grids/frequencyA",
    }

    data, sp, guard, mode = pio.load_branch_terms(cfg, pio.FULL_POL_TERMS)

    assert guard["masked_pixel_count"] == 2
    for term in pio.FULL_POL_TERMS:
        arr = data[term]
        assert np.isnan(arr[1, 1]).all() if np.iscomplexobj(arr) else np.isnan(arr[1, 1])
        assert np.isnan(arr[3, 0]).all() if np.iscomplexobj(arr) else np.isnan(arr[3, 0])
        # every other pixel must remain untouched
        assert np.isfinite(arr[0, 0]).all() if np.iscomplexobj(arr) else np.isfinite(arr[0, 0])
    # a complex term specifically must have been masked too, not just the
    # real diagonal ones
    assert np.isnan(data["HHVV"][1, 1].real)

def test_detect_polarimetric_mode_requires_all_three_offdiagonal_terms(tmp_path):
    # Regression test: a product with all diagonal terms but only ONE of
    # the three off-diagonal terms must NOT be classified as
    # LSAR_FULL_POL, since Module 14's loader requires the complete
    # six-term set and would raise KeyError on the missing ones. It should
    # fall through to UNSUPPORTED instead of failing later, less clearly.
    from nisar_utils import polarimetric_io as pio

    h5_path = tmp_path / "partial_offdiag.h5"
    with h5py.File(h5_path, "w") as f:
        g = f.create_group("/science/LSAR/GCOV/grids/frequencyA")
        for t in pio.FULL_POL_DIAGONAL:
            g.create_dataset(t, shape=(2, 2), dtype="f4")
        # Only one of the three off-diagonal terms present.
        g.create_dataset("HHHV", shape=(2, 2), dtype="c8")

    result = pio.detect_polarimetric_mode(h5_path)
    assert result["mode"] == "UNSUPPORTED"


def test_detect_polarimetric_mode_accepts_complete_offdiagonal_set(tmp_path):
    from nisar_utils import polarimetric_io as pio

    h5_path = tmp_path / "complete_fullpol.h5"
    with h5py.File(h5_path, "w") as f:
        g = f.create_group("/science/LSAR/GCOV/grids/frequencyA")
        for t in pio.FULL_POL_TERMS:
            g.create_dataset(t, shape=(2, 2), dtype="c8")

    result = pio.detect_polarimetric_mode(h5_path)
    assert result["mode"] == "LSAR_FULL_POL"

def test_load_detected_mode_consistent_shape_on_cache_miss(tmp_path, monkeypatch):
    # Regression test: on a completely fresh session (no polarimetric_mode
    # cached yet -- i.e. Module 13 has not run), load_detected_mode() used
    # to return detect_polarimetric_mode()'s raw result dict, which has a
    # "mode" key instead of "polarimetric_mode". Every caller in Modules
    # 14-19 immediately does mode['polarimetric_mode'], which only worked
    # by accident because the normal curriculum always runs Module 13
    # (which populates the cache correctly) first.
    from nisar_utils import polarimetric_io as pio
    # Keep the repository working tree clean: a cache-miss detection should
    # not create the real user_session.json used by interactive notebooks.
    monkeypatch.setattr(pio, "save_session", lambda payload: tmp_path / "user_session.json")

    h5_path = tmp_path / "fresh.h5"
    with h5py.File(h5_path, "w") as f:
        g = f.create_group("/science/LSAR/GCOV/grids/frequencyA")
        for t in pio.FULL_POL_TERMS:
            g.create_dataset(t, shape=(2, 2), dtype="c8")

    cfg = {"nisar_file": str(h5_path), "default_frequency": "frequencyA"}
    mode = pio.load_detected_mode(cfg)

    assert mode["polarimetric_mode"] == "LSAR_FULL_POL"
    assert mode["polarimetric_family"] == "LSAR"
    assert mode["polarimetric_frequency"] == "frequencyA"
    assert mode["polarimetric_base"] == "/science/LSAR/GCOV/grids/frequencyA"
    assert set(mode.keys()) == {
        "polarimetric_mode", "polarimetric_family",
        "polarimetric_frequency", "polarimetric_base",
    }

def test_covariance_offdiagonal_extraction_shape():
    # Regression test for a real indexing bug: C[..., (i, j)] (a tuple
    # used as a single fancy index) does NOT extract the scalar element
    # at row i, col j -- it selects two whole slices along the last axis,
    # producing an extra trailing dimension. C[..., i, j] (two separate
    # integer indices) is correct. This went unnoticed in Module 14
    # because the wrong-shaped result was only ever fed into
    # np.nanmedian(), which silently ignores shape.
    C = np.zeros((4, 4, 3, 3), dtype=np.complex128)
    C[..., 0, 1] = 1.0 + 2.0j
    i, j = (0, 1)
    a = C[..., i, j]
    assert a.shape == (4, 4)
    assert np.all(a == 1.0 + 2.0j)

def test_eigen_analysis_survives_nan_pixels_in_batch():
    # Regression test for a real crash: np.linalg.eigh on a batch of 3x3
    # matrices can raise LinAlgError("Eigenvalues did not converge") for
    # the WHOLE batch the moment a single matrix in it contains NaN --
    # which is exactly what a masked (MASK==0 / transmit-gap) pixel looks
    # like after load_branch_terms(). This must not happen: eigen_analysis
    # has to isolate the NaN pixel and return NaN there, not crash the
    # entire image's eigendecomposition.
    T3 = np.zeros((5, 5, 3, 3), dtype=np.complex128)
    T3[..., 0, 0] = 3.0
    T3[..., 1, 1] = 2.0
    T3[..., 2, 2] = 1.0
    # One masked pixel: every entry NaN, as apply_mask_to_terms would leave it.
    T3[2, 2, :, :] = np.nan

    e = eigen_analysis(T3)

    # The masked pixel must be NaN everywhere in the output...
    assert np.all(np.isnan(e["eigenvalues"][2, 2]))
    assert np.all(np.isnan(e["eigenvectors"][2, 2]))
    assert np.isnan(e["span"][2, 2])
    assert np.isnan(e["entropy"][2, 2])
    assert np.isnan(e["anisotropy"][2, 2])
    # ...but must NOT be silently reported as exactly zero, which would
    # misleadingly look like a valid, fully anisotropic/zero-entropy pixel.
    assert e["entropy"][2, 2] != 0.0 or np.isnan(e["entropy"][2, 2])

    # Every OTHER pixel must be completely unaffected -- same numbers as
    # the already-verified known-matrix case (diag(3,2,1) -> H~=0.9206).
    for r in range(5):
        for c in range(5):
            if (r, c) == (2, 2):
                continue
            assert np.isfinite(e["entropy"][r, c])
            assert abs(e["entropy"][r, c] - 0.920619835714305) < 1e-6

def test_no_full_pol_terms_namespace_collision():
    # Regression test for a real bug: polarimetry.py used to define its
    # own dead, non-standard FULL_POL_TERMS constant (10 terms, including
    # names like "HHVH" that don't exist in real GCOV products). Module
    # 19 does `from nisar_utils.polarimetric_io import *` followed by
    # `from nisar_utils.polarimetry import *`, so the second wildcard
    # import silently clobbered the correct 6-term constant with the
    # wrong one -- load_branch_terms(cfg, FULL_POL_TERMS) would then ask
    # for terms that don't exist on any real product at all.
    import nisar_utils.polarimetric_io as pio
    import nisar_utils.polarimetry as ppy

    assert not hasattr(ppy, "FULL_POL_TERMS"), (
        "polarimetry.py must not define its own FULL_POL_TERMS -- it "
        "collides with, and can silently shadow, polarimetric_io.FULL_POL_TERMS"
    )

    ns = {}
    exec("from nisar_utils.polarimetric_io import *", ns)
    exec("from nisar_utils.polarimetry import *", ns)
    assert tuple(ns["FULL_POL_TERMS"]) == pio.FULL_POL_TERMS

def test_yamaguchi4_outputs_are_real_valued():
    # Regression test: fullpol_yamaguchi4 used to build its volume-model
    # matrix V via np.zeros_like(Cres), which silently inherited Cres's
    # COMPLEX dtype (Vsym/Vhh/Vvv are always real physical model
    # matrices). That made the volume power and residual complex-typed
    # with a zero imaginary part -- numerically harmless in isolation, but
    # it broke any downstream code expecting real output (np.nanpercentile
    # and friends raise TypeError on complex input), which is exactly what
    # a real-image RGB composite of the decomposition does.
    import h5py
    from nisar_utils import polarimetric_io as pio
    from nisar_utils.polarimetry import fullpol_yamaguchi4

    rng = np.random.default_rng(7)
    shape = (6, 6)
    terms = {t: (rng.random(shape).astype("f4") + 0.1) for t in pio.FULL_POL_DIAGONAL}
    for t in pio.FULL_POL_OFFDIAGONAL:
        terms[t] = (rng.random(shape) + 1j * rng.random(shape)).astype("c8")

    from nisar_utils.polarimetry import covariance_hermitian_from_terms
    C = covariance_hermitian_from_terms(terms)
    y4 = fullpol_yamaguchi4(C)

    for key in ("surface", "double_bounce", "volume", "helix", "span", "residual"):
        arr = np.asarray(y4[key])
        assert not np.iscomplexobj(arr), f"{key} must be real-valued, got dtype {arr.dtype}"
        # must also be usable by nanpercentile the way the RGB-composite
        # notebook cell uses it, i.e. must not raise
        np.nanpercentile(np.maximum(arr, 0), 99)

def test_cloude_pottier_mean_alpha_matches_known_value():
    # Regression test for a real scientific bug: two notebook cells
    # (Modules 16 and 19) computed mean alpha as
    # nanmean(alpha_i * p_i) instead of sum(alpha_i * p_i) -- since the
    # probabilities already sum to 1, nanmean silently divides the
    # correct answer by 3. For the diag(3,2,1) reference case (alpha_i =
    # [0, 90, 90] degrees, p = [0.5, 1/3, 1/6]) the correct weighted mean
    # is 45 degrees; the buggy formula gave 15.
    from nisar_utils.polarimetry import eigen_analysis, cloude_pottier_mean_alpha

    T = np.diag([3.0, 2.0, 1.0]).astype(np.complex64)[None, None, :, :]
    e = eigen_analysis(T)
    mean_alpha_deg = np.degrees(cloude_pottier_mean_alpha(e["eigenvectors"], e["probabilities"]))
    assert abs(float(mean_alpha_deg[0, 0]) - 45.0) < 1e-4


def test_cloude_pottier_mean_alpha_propagates_nan_for_masked_pixels():
    from nisar_utils.polarimetry import eigen_analysis, cloude_pottier_mean_alpha

    T3 = np.zeros((3, 3, 3, 3), dtype=np.complex128)
    T3[..., 0, 0] = 3.0; T3[..., 1, 1] = 2.0; T3[..., 2, 2] = 1.0
    T3[1, 1, :, :] = np.nan

    e = eigen_analysis(T3)
    mean_alpha = cloude_pottier_mean_alpha(e["eigenvectors"], e["probabilities"])
    assert np.isnan(mean_alpha[1, 1])
    assert np.isfinite(mean_alpha[0, 0])


def test_c3_to_t3_complex_offdiagonal_matches_unitary_pauli_transform():
    # Complex-valued regression: C23 must enter the Pauli transform as
    # C32 = conj(C23), not C23 itself. This catches phase errors that a
    # purely real reference covariance cannot expose.
    rng = np.random.default_rng(1234)
    A = rng.normal(size=(3, 3)) + 1j * rng.normal(size=(3, 3))
    C = (A @ A.conj().T).astype(np.complex128)
    C = C[None, None, :, :]

    T = standard_c3_to_t3(C)
    U = np.array([
        [1/np.sqrt(2), 0, 1/np.sqrt(2)],
        [1/np.sqrt(2), 0, -1/np.sqrt(2)],
        [0, 1, 0],
    ], dtype=np.complex128)
    expected = U @ C[0, 0] @ U.conj().T

    assert np.allclose(T[0, 0], expected, atol=1e-10)
    assert np.allclose(
        np.linalg.eigvalsh(C[0, 0]),
        np.linalg.eigvalsh(T[0, 0]),
        atol=1e-10,
    )
    assert np.allclose(T[0, 0], T[0, 0].conj().T, atol=1e-10)
