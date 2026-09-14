# SPDX-License-Identifier: Apache-2.0
import numpy as np

from nisar_utils.product import parse_filename
from nisar_utils.spatial import coordinate_to_index
from nisar_utils.workflow import default_window, resolve_frequency
from nisar_utils.visualization import select_rgb_pair


def test_parse_official_nisar_gcov_filename():
    name = (
        "NISAR_L2_UR_GCOV_029_048_D_074_2005_QPDH_A_"
        "20260828T125812_20260828T125901_CRID_CAL_001_VV_001.h5"
    )
    p = parse_filename(name)
    assert p["mission"] == "NISAR"
    assert p["instrument"] == "L"
    assert p["product_level"] == "L2"
    assert p["product_type"] == "GCOV"
    assert p["cycle"] == "029"
    assert p["relative_orbit"] == "048"
    assert p["orbit_direction"] == "D"
    assert p["frame"] == "074"


def test_coordinate_to_index_handles_descending_y():
    x = np.arange(0.0, 10.0)
    y = np.arange(10.0, 0.0, -1.0)
    r0, r1, c0, c1 = coordinate_to_index(x, y, 2.0, 5.0, 3.0, 7.0)
    assert (r0, r1, c0, c1) == (3, 8, 2, 6)


def test_default_window_is_bounded():
    r0, r1, c0, c1 = default_window(np.arange(500), np.arange(300), size=128)
    assert (r1-r0, c1-c0) == (128, 128)
    assert 0 <= r0 < r1 <= 300
    assert 0 <= c0 < c1 <= 500


def test_resolve_frequency_auto_for_single_frequency():
    class Profile:
        frequencies = ["A"]
    assert resolve_frequency({"default_frequency": "auto"}, Profile()) == "A"


def test_select_rgb_pair_prefers_h_pair():
    assert select_rgb_pair({"HHHH", "HVHV", "VVVV", "VHVH"}) == ("HHHH", "HVHV")


def test_select_rgb_pair_falls_back_to_v_pair():
    assert select_rgb_pair({"VVVV", "VHVH"}) == ("VVVV", "VHVH")


def test_select_rgb_pair_falls_back_to_compact_pol():
    # SSAR compact-pol GCOV products never carry HHHH/VVVV terms at all —
    # RHRH/RVRV must still resolve to a usable RGB pair, and must not
    # regress the LSAR fallback order above it.
    assert select_rgb_pair({"RHRH", "RVRV"}) == ("RHRH", "RVRV")
    assert select_rgb_pair({"HHHH", "HVHV", "RHRH", "RVRV"}) == ("HHHH", "HVHV")


def test_select_rgb_pair_ignores_complex_only_terms():
    assert select_rgb_pair({"HHHV", "HHVV", "RHRV"}) is None


def test_discover_gcov_root_survives_broken_links(tmp_path):
    # Regression test: h5py's Group.visititems() aborts the whole traversal
    # with "RuntimeError: Object visitation failed" the moment it hits one
    # unresolvable object (a dangling soft/external link is the common
    # trigger in real, large HDF5 products). discover_gcov_root() must not
    # use that low-level traversal directly.
    import h5py
    from nisar_utils.product import discover_gcov_root

    h5_path = tmp_path / "with_broken_links.h5"
    with h5py.File(h5_path, "w") as f:
        grp = f.create_group("science/LSAR/GCOV/grids/frequencyA")
        grp.create_dataset("HHHH", shape=(2, 2), dtype="f4")
        f["science/LSAR/GCOV/dangling_soft"] = h5py.SoftLink("/does/not/exist")
        f["science/LSAR/GCOV/grids/frequencyA/dangling_ext"] = h5py.ExternalLink(
            "missing_file.h5", "/nope"
        )

    with h5py.File(h5_path, "r") as f:
        assert discover_gcov_root(f) == "/science/LSAR/GCOV"


def test_gcov_mask_helpers(tmp_path):
    import h5py
    from nisar_utils.gcov import read_gcov_mask, apply_gcov_mask

    h5_path = tmp_path / "masked.h5"
    with h5py.File(h5_path, "w") as f:
        grid = f.create_group("science/LSAR/GCOV/grids/frequencyA")
        grid.create_dataset("mask", data=np.array([[1, 1, 0], [1, 0, 1]], dtype="u1"))
        grid.create_dataset("HHHH", data=np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]))

    with h5py.File(h5_path, "r") as f:
        invalid_mask, mask_arr = read_gcov_mask(
            f, "science/LSAR/GCOV/grids/frequencyA", 0, 2, 0, 3
        )
        assert invalid_mask.tolist() == [[False, False, True], [False, True, False]]

        hhhh = f["science/LSAR/GCOV/grids/frequencyA/HHHH"][:]
        masked = apply_gcov_mask(hhhh, "HHHH", invalid_mask)
        assert np.isnan(masked[0, 2]) and np.isnan(masked[1, 1])
        assert masked[0, 0] == 1.0 and masked[1, 2] == 6.0

        # A term not in MASKED_GCOV_TERMS (e.g. a complex off-diagonal
        # channel) must pass through untouched.
        unmasked = apply_gcov_mask(hhhh, "HHHV", invalid_mask)
        assert not np.isnan(unmasked).any()


def test_plot_complex_term_magnitude_and_phase(monkeypatch):
    import matplotlib
    matplotlib.use("Agg")
    from nisar_utils.visualization import plot_complex_term

    arr = np.array([[1.0 + 1.0j, 2.0 + 0.0j], [0.0 + 2.0j, np.nan + 1.0j]])
    ax_mag, ax_phase = plot_complex_term(arr, "TEST")

    expected_mag_db = 10.0 * np.log10(np.abs(arr) ** 2 + 1e-12)
    expected_phase_deg = np.degrees(np.angle(arr))

    plotted_mag = ax_mag.images[0].get_array().data
    plotted_phase = ax_phase.images[0].get_array().data

    assert np.allclose(plotted_mag, expected_mag_db, equal_nan=True)
    assert np.allclose(plotted_phase, expected_phase_deg, equal_nan=True)


def test_discover_hdf5_excludes_mask_from_covariance_terms(tmp_path):
    # Regression test: a loose "any 4 letters" pattern also matches the
    # "mask" auxiliary dataset (and, since "ma" != "sk", files it as an
    # off-diagonal covariance term), which every module from 02 onward
    # iterates over as if it were a real polarization channel.
    import h5py
    from nisar_utils.product import discover_hdf5

    h5_path = tmp_path / "with_mask.h5"
    with h5py.File(h5_path, "w") as f:
        grid = f.create_group("science/LSAR/GCOV/grids/frequencyA")
        grid.create_dataset("HHHH", shape=(2, 2), dtype="f4")
        grid.create_dataset("HVHV", shape=(2, 2), dtype="f4")
        grid.create_dataset("mask", shape=(2, 2), dtype="u1")

    result = discover_hdf5(h5_path)
    terms = result["covariance_terms"]["frequencyA"]
    assert "mask" not in terms
    assert set(terms) == {"HHHH", "HVHV"}
    assert "mask" not in result["off_diagonal_terms"]["frequencyA"]
