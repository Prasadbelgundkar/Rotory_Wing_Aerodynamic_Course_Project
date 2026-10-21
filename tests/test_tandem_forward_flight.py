"""Verification of the forward-flight tandem interference integration
(src/tandem_forward_flight.py + external_inflow in src/m2/edgewise_bemt.py)."""

import os
import sys

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (os.path.join(ROOT, "src"), os.path.join(ROOT, "src", "m2")):
    if p not in sys.path:
        sys.path.insert(0, p)

import tandem_rotor_config as C
from edgewise_bemt import run_edgewise_bemt
from tandem_forward_flight import (FVWInterferenceMap, coleman_skewed_field,
                                   solve_tandem_forward_flight, trim_rotor_forward_flight)

RHO, A_SOUND = 1.225, 340.3
OMEGA = 220.0 / C.FWD_ROTOR_RADIUS_M
W = C.GROSS_MASS_KG * C.G


def _run(rotor, V, alpha, ext=None, rotation="ccw", n_r=30, n_psi=48):
    return run_edgewise_bemt(rotor, C.default_airfoil_provider, V, OMEGA, np.radians(6.0), 0.0, 0.0,
                             alpha, 90.0, RHO, A_SOUND, n_r=n_r, n_psi=n_psi, rotation=rotation,
                             external_inflow=ext)


def test_external_inflow_none_equals_zero_field():
    """Baseline recovery: a zero interference field reproduces the original solver exactly."""
    rot = C.build_aft_rotor()
    a = _run(rot, 30.0, np.radians(2.0))
    b = _run(rot, 30.0, np.radians(2.0), ext=np.zeros((30, 48)))
    assert a.T_N == b.T_N and a.power_W == b.power_W
    assert np.array_equal(a.U_P, b.U_P)


def test_uniform_external_inflow_equals_axial_climb():
    """Limiting case: a uniform imposed downwash in hover is the same as an axial climb at that speed."""
    rot = C.build_aft_rotor()
    vc = 3.0
    climb = _run(rot, vc, np.pi / 2)
    imposed = _run(rot, 0.0, 0.0, ext=np.full((30, 48), vc))
    assert imposed.T_N == pytest.approx(climb.T_N, rel=1e-6)
    assert imposed.power_W == pytest.approx(climb.power_W, rel=1e-6)


def test_external_inflow_shape_and_finite_checks():
    rot = C.build_aft_rotor()
    with pytest.raises(ValueError):
        _run(rot, 30.0, 0.0, ext=np.zeros((10, 10)))
    bad = np.zeros((30, 48))
    bad[3, 4] = np.nan
    with pytest.raises(ValueError):
        _run(rot, 30.0, 0.0, ext=bad)


def test_forward_flight_trim_converges():
    rot = C.build_fwd_rotor()
    t = trim_rotor_forward_flight(rot, C.default_airfoil_provider, 0.15 * 220.0, OMEGA,
                                  np.radians(1.0), 0.5 * W, RHO, A_SOUND)
    assert t.converged
    assert t.result.T_N == pytest.approx(0.5 * W, rel=1e-3)
    assert abs(t.result.Mx_hub_Nm) < 1e-3 * 0.5 * W * rot.radius_m
    assert abs(t.result.My_hub_Nm) < 1e-3 * 0.5 * W * rot.radius_m


def _tandem(mu, model, **kw):
    return solve_tandem_forward_flight(C.build_fwd_rotor(), C.build_aft_rotor(), C.default_airfoil_provider,
                                       mu, OMEGA, W, RHO, A_SOUND, C.LONGITUDINAL_SEP_M, 3.7,
                                       model=model, **kw)


def test_model_none_is_two_isolated_rotors():
    """Switch off: counter-rotating mirror rotors need the same power as an isolated rotor."""
    r = _tandem(0.15, "none")
    assert r.converged
    assert np.all(r.dv_aft == 0.0)
    assert r.aft.result.power_W == pytest.approx(r.fwd.result.power_W, rel=1e-6)


def test_interference_ordering_and_forward_rotor_unchanged():
    """Physical direction: aft power none < coleman < fvw; forward rotor not affected (one-way model)."""
    res = {m: _tandem(0.10, m) for m in ("none", "coleman", "fvw")}
    assert all(r.converged for r in res.values())
    p = {m: r.aft.result.power_W for m, r in res.items()}
    assert p["none"] < p["coleman"] < p["fvw"]
    assert res["fvw"].fwd.result.power_W == res["none"].fwd.result.power_W
    # aft rotor needs more collective to carry the same thrust in the downwash
    assert res["fvw"].aft.theta0_deg > res["none"].aft.theta0_deg


def test_coleman_field_zero_without_overlap():
    r = np.linspace(1.0, 9.14, 20)
    psi = np.linspace(0, 2 * np.pi, 36, endpoint=False)
    f = coleman_skewed_field(0.1, 10.0, 0.05, 9.14, 2.0 * 9.14 + 0.01, r, psi)
    assert np.all(f == 0.0)


def test_fvw_map_reproduces_cached_grid_and_rejects_extrapolation():
    m = FVWInterferenceMap("ch47")
    mu0 = float(m.mu[0])
    x = m.x[2:5]
    psi = m.psi[[0, 9, 18]]
    got = m.normalised(mu0, x, psi)
    assert np.allclose(got, m.dv_norm[0][[0, 9, 18]][:, 2:5].T, atol=1e-12)
    with pytest.raises(ValueError):
        m.normalised(m.mu[-1] + 0.05, x, psi)


def test_fvw_map_mu_interpolation_is_between_neighbours():
    m = FVWInterferenceMap("ch47")
    if len(m.mu) < 2:
        pytest.skip("needs two cached advance ratios")
    mid = 0.5 * (m.mu[0] + m.mu[1])
    x, psi = m.x, m.psi
    a, b, c = m.normalised(m.mu[0], x, psi), m.normalised(mid, x, psi), m.normalised(m.mu[1], x, psi)
    assert np.allclose(b, 0.5 * (a + c), atol=1e-12)
