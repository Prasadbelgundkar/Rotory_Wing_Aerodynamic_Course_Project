"""
tandem_forward_flight.py

Tandem-rotor interference in FORWARD FLIGHT, integrated into the edgewise
(azimuth-resolved) BEMT of Milestone 2 (src/m2/edgewise_bemt.py).

Each rotor is solved with run_edgewise_bemt and trimmed to its share of the
weight with zero hub moments (collective + both cyclics, articulated-rotor
equivalent).  The forward rotor's wake acts on the aft rotor through an extra
through-disk velocity field dv(r, psi) passed as `external_inflow`.  Three
switchable interference models:

  'none'    : two isolated rotors (baseline; reproduces the original tool).
  'coleman' : Coleman, Feingold & Stempin (1945) skewed vortex-cylinder inflow
              of the forward rotor, v0 (1 + tan(chi/2) x/R), applied only where
              the aft disk lies inside the forward disk (planform overlap).
  'fvw'     : revolution-averaged downwash of the forward rotor's free-vortex
              wake on the aft disk (src/tandem_fvw.py, cached in src/data/fvw/),
              stored normalised by the forward rotor's Glauert induced velocity
              and re-scaled by the BEMT forward rotor's own value, linearly
              interpolated in advance ratio between the cached FVW runs.

The FVW maps belong to one geometry (d/R, stagger, blade count): they must be
regenerated with tandem_fvw.py for a different configuration.  Only the
forward-on-aft effect is modelled; the aft rotor's upwash on the forward rotor
(about -6 to -8 % forward-rotor power in the full FVW) is neglected.

Frames: aircraft x aft, y right, z up.  FVW map azimuth is geometric (from
+x toward +y about the aft hub).  The edgewise BEMT azimuth runs in the
blade's direction of rotation from downstream, so for a 'cw' rotor the map is
read at -psi.
"""

import glob
import json
import os
import sys
from dataclasses import dataclass
from typing import Callable, Dict, Optional

import numpy as np
from scipy.optimize import fsolve

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.join(HERE, "m2")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from edgewise_bemt import run_edgewise_bemt, EdgewiseRotorResult  # noqa: E402

FVW_DATA_DIR = os.path.join(HERE, "data", "fvw")
INTERFERENCE_MODELS = ("none", "coleman", "fvw")
HELICOPTER_NACELLE_DEG = 90.0   # shaft vertical in the M2 frame convention


# ---------------------------------------------------------------------------
# FVW interference map
# ---------------------------------------------------------------------------
class FVWInterferenceMap:
    """Forward-rotor-induced downwash on the aft disk from cached FVW runs.

    Stored as dv / v0_fwd on a (psi_geom, r/R) grid for each advance ratio,
    v0_fwd = lambda_i(Glauert) * Omega R of the forward rotor in that run.
    """

    def __init__(self, config: str = "ch47", data_dir: str = FVW_DATA_DIR):
        files = sorted(glob.glob(os.path.join(data_dir, f"{config}_mu*_tandem.json")))
        if not files:
            raise FileNotFoundError(
                f"No FVW maps for '{config}' in {data_dir}; run "
                f"'python src/tandem_fvw.py {config} <mu list>' first")
        entries = []
        for fn in files:
            with open(fn) as f:
                d = json.load(f)
            g = d["aft_grid"]
            R = self._radius(config)
            v0 = d["lam_glauert"] * self._tip_speed(config)
            entries.append((float(d["mu"]), np.array(g["r"]) / R,
                            np.radians(np.array(g["psi_deg"])),
                            np.array(g["v_down"]) / v0))
        entries.sort(key=lambda e: e[0])
        self.config = config
        self.mu = np.array([e[0] for e in entries])
        self.x = entries[0][1]
        self.psi = entries[0][2]
        self.dv_norm = np.stack([e[3] for e in entries])        # (n_mu, n_psi, n_x)

    @staticmethod
    def _cfg(config):
        import tandem_fvw
        return tandem_fvw.CONFIGS[config]

    def _radius(self, config):
        return self._cfg(config)["R"]

    def _tip_speed(self, config):
        return self._cfg(config)["V_TIP"]

    @property
    def mu_range(self):
        return float(self.mu[0]), float(self.mu[-1])

    def normalised(self, mu: float, x: np.ndarray, psi_geom: np.ndarray) -> np.ndarray:
        """dv/v0_fwd at (x, psi_geom) [(n_r,), (n_psi,)] -> (n_r, n_psi)."""
        lo, hi = self.mu_range
        if not (lo - 1e-9 <= mu <= hi + 1e-9):
            raise ValueError(f"mu = {mu:.3f} outside the cached FVW range [{lo:.3f}, {hi:.3f}]; "
                             f"run src/tandem_fvw.py at that advance ratio")
        # linear in mu
        j = int(np.clip(np.searchsorted(self.mu, mu) - 1, 0, len(self.mu) - 2)) if len(self.mu) > 1 else 0
        if len(self.mu) == 1:
            field = self.dv_norm[0]
        else:
            w = (mu - self.mu[j]) / (self.mu[j + 1] - self.mu[j])
            field = (1 - w) * self.dv_norm[j] + w * self.dv_norm[j + 1]
        # periodic in psi, clamped in x (map covers 0.15R .. 0.98R)
        psi_ext = np.concatenate([self.psi, [self.psi[0] + 2 * np.pi]])
        field_ext = np.vstack([field, field[:1]])                   # (n_psi+1, n_x)
        xq = np.clip(x, self.x[0], self.x[-1])
        by_psi = np.array([np.interp(xq, self.x, row) for row in field_ext])   # (n_psi+1, n_r)
        pq = np.mod(psi_geom, 2 * np.pi)
        out = np.array([np.interp(pq, psi_ext, by_psi[:, i]) for i in range(len(xq))])
        return out                                                   # (n_r, n_psi)


_MAP_CACHE: Dict[str, FVWInterferenceMap] = {}


def get_fvw_map(config: str) -> FVWInterferenceMap:
    if config not in _MAP_CACHE:
        _MAP_CACHE[config] = FVWInterferenceMap(config)
    return _MAP_CACHE[config]


# ---------------------------------------------------------------------------
# Interference fields on the aft rotor's own (r, psi) grid
# ---------------------------------------------------------------------------
def _geometric_psi(psi_rotor: np.ndarray, rotation: str) -> np.ndarray:
    return psi_rotor if rotation == "ccw" else -psi_rotor


def coleman_skewed_field(mu: float, v0_fwd: float, lam_fwd: float, R_fwd: float,
                         sep_m: float, r: np.ndarray, psi_geom: np.ndarray) -> np.ndarray:
    """Coleman skewed-cylinder downwash of the forward rotor on the aft disk
    (overlap region only), (n_r, n_psi) [m/s]."""
    chi = np.arctan2(mu, lam_fwd)
    x = sep_m + r[:, None] * np.cos(psi_geom)[None, :]     # relative to forward hub
    y = r[:, None] * np.sin(psi_geom)[None, :]
    inside = x ** 2 + y ** 2 <= R_fwd ** 2
    return np.where(inside, v0_fwd * (1.0 + np.tan(chi / 2.0) * x / R_fwd), 0.0)


# ---------------------------------------------------------------------------
# Single-rotor forward-flight trim
# ---------------------------------------------------------------------------
@dataclass
class TrimmedRotor:
    theta0_deg: float
    theta1c_deg: float
    theta1s_deg: float
    result: EdgewiseRotorResult
    trim_residual: float
    converged: bool


def trim_rotor_forward_flight(rotor, airfoil_provider: Callable, V_inf: float, omega_rad_s: float,
                              alpha_shaft_rad: float, target_thrust_N: float, rho: float, a_sound: float,
                              rotation: str = "ccw", external_inflow: Optional[np.ndarray] = None,
                              n_r: int = 30, n_psi: int = 48,
                              guess_deg=(10.0, 0.0, 0.0)) -> TrimmedRotor:
    """Trim collective and cyclics so T = target and both hub moments are zero."""
    if target_thrust_N <= 0:
        raise ValueError("target thrust must be positive")
    scaleM = target_thrust_N * rotor.radius_m * 0.01

    def run(th):
        return run_edgewise_bemt(rotor, airfoil_provider, V_inf, omega_rad_s,
                                 np.radians(th[0]), np.radians(th[1]), np.radians(th[2]),
                                 alpha_shaft_rad, HELICOPTER_NACELLE_DEG, rho, a_sound,
                                 n_r=n_r, n_psi=n_psi, rotation=rotation,
                                 external_inflow=external_inflow)

    def resid(th):
        res = run(th)
        return [res.T_N / target_thrust_N - 1.0, res.Mx_hub_Nm / scaleM, res.My_hub_Nm / scaleM]

    sol, info, ier, _ = fsolve(resid, np.asarray(guess_deg, float), full_output=True, xtol=1e-8)
    res = run(sol)
    r = float(np.max(np.abs(resid(sol))))
    ok = bool(ier == 1 and r < 1e-3 and res.converged)
    return TrimmedRotor(float(sol[0]), float(sol[1]), float(sol[2]), res, r, ok)


# ---------------------------------------------------------------------------
# Tandem forward flight
# ---------------------------------------------------------------------------
@dataclass
class TandemForwardFlight:
    mu: float
    V_inf: float
    model: str
    shaft_tilt_deg: float
    fwd: TrimmedRotor
    aft: TrimmedRotor
    dv_aft: np.ndarray            # (n_r, n_psi) interference velocity on the aft rotor [m/s]
    total_power_W: float
    converged: bool

    @property
    def mean_dv_aft(self) -> float:
        """area-weighted mean interference downwash on the aft disk [m/s]"""
        r = self.aft.result.r_m
        w = r / r.sum()
        return float((self.dv_aft.mean(axis=1) * w).sum())


def solve_tandem_forward_flight(rotor_fwd, rotor_aft, airfoil_provider: Callable, mu: float,
                                omega_rad_s: float, gross_weight_N: float, rho: float, a_sound: float,
                                longitudinal_sep_m: float, flat_plate_m2: float,
                                thrust_split_fwd: float = 0.5, model: str = "fvw",
                                fvw_config: str = "ch47", rotation_fwd: str = "ccw",
                                rotation_aft: str = "cw", n_r: int = 30, n_psi: int = 48
                                ) -> TandemForwardFlight:
    """Trim a tandem in level forward flight with the chosen interference model.

    Shaft tilt balances fuselage drag (tan a = D / W), as in tandem_fvw.py;
    each rotor carries its thrust share with zero hub moments.
    """
    if model not in INTERFERENCE_MODELS:
        raise ValueError(f"model must be one of {INTERFERENCE_MODELS}")
    if not 0.0 < thrust_split_fwd < 1.0:
        raise ValueError("thrust_split_fwd must be in (0, 1)")
    if mu < 0:
        raise ValueError("mu must be >= 0")
    OR = omega_rad_s * rotor_fwd.radius_m
    V = mu * OR
    drag = 0.5 * rho * V ** 2 * flat_plate_m2
    tilt = np.arctan2(drag, gross_weight_N)
    # forward-tilted disk: the free stream passes DOWN through it, in the same
    # sense as the induced flow (propulsive power T V sin a), so alpha_shaft > 0
    alpha_shaft = tilt

    fwd = trim_rotor_forward_flight(rotor_fwd, airfoil_provider, V, omega_rad_s, alpha_shaft,
                                    gross_weight_N * thrust_split_fwd, rho, a_sound,
                                    rotation=rotation_fwd, n_r=n_r, n_psi=n_psi)
    r_aft = np.linspace(rotor_aft.root_cutout_m, rotor_aft.radius_m, n_r)
    psi = np.linspace(0.0, 2.0 * np.pi, n_psi, endpoint=False)
    psi_geom = _geometric_psi(psi, rotation_aft)
    v0_fwd = fwd.result.lambda_i_G * OR

    if model == "none":
        dv = None
    elif model == "coleman":
        dv = coleman_skewed_field(fwd.result.mu, v0_fwd, fwd.result.lambda_G, rotor_fwd.radius_m,
                                  longitudinal_sep_m, r_aft, psi_geom)
    else:
        dv = v0_fwd * get_fvw_map(fvw_config).normalised(mu, r_aft / rotor_aft.radius_m, psi_geom)

    aft = trim_rotor_forward_flight(rotor_aft, airfoil_provider, V, omega_rad_s, alpha_shaft,
                                    gross_weight_N * (1.0 - thrust_split_fwd), rho, a_sound,
                                    rotation=rotation_aft, external_inflow=dv, n_r=n_r, n_psi=n_psi,
                                    guess_deg=(fwd.theta0_deg, 0.0, 0.0))
    return TandemForwardFlight(mu=mu, V_inf=V, model=model, shaft_tilt_deg=float(np.degrees(tilt)),
                               fwd=fwd, aft=aft,
                               dv_aft=np.zeros((n_r, n_psi)) if dv is None else dv,
                               total_power_W=fwd.result.power_W + aft.result.power_W,
                               converged=fwd.converged and aft.converged)
