"""
tandem_fvw.py  --  one-file free-vortex wake (FVW) model of a tandem rotor
                   in forward flight (and hover), CH-47 class baseline.

Run (from the repository root):
       python src/tandem_fvw.py ch47 0.05,0.10,0.15,0.20,0.25
       python src/tandem_fvw.py dingeldein 0.11,0.145,0.19,0.24,0.295
       python src/tandem_fvw.py ch47 0.1 --quick      (coarse grid smoke test)
       Writes <config>_mu<mu>_<single|tandem>.json and <config>_summary.json to
       src/data/fvw/ (or --out=DIR).  The revolution-averaged forward-rotor
       downwash on the aft disk ('aft_grid') in the tandem files is what
       tandem_forward_flight.FVWInterferenceMap feeds into the edgewise BEMT.

Model (Lagrangian free-vortex wake, time-marching):
  * Blades: lifting line, N_S spanwise panels per blade, linear airfoil
    (same constants as the BEMT tool's TANDEM_AIRFOIL), rigid blades.
  * Wake: vortex-lattice of trailed + shed filaments behind every blade.
    Wake markers are released at the blade every time step and convected
    with the local velocity (free stream + all induced velocities from both
    rotors), 2nd-order Adams-Bashforth in time.
  * Filaments: Biot-Savart with Vatistas (n=2) core, core growth by
    Squire's model with Bhagwat & Leishman's turbulent viscosity factor.
  * Trim: each rotor trims its own thrust (W/2) with collective and drives
    its hub roll/pitch moments to zero with cyclic (articulated-rotor
    equivalent of zero flapping). Shaft tilted forward to balance fuselage drag.
  * Interference: the forward rotor's wake (and bound vortices) evaluated on
    the aft disk, revolution-averaged, compared with Coleman's skewed-cylinder
    inflow and with the isolated-rotor runs.

Coordinates: aircraft-fixed, x points aft (free stream blows +x), z up.
Forward hub at the origin, aft hub at (D_SEP, 0, STAGGER).
"""

import os
import sys
import json
import time
import numpy as np
try:
    from numba import njit, prange
except ImportError:          # reading cached maps does not need numba; running the wake does
    def njit(*args, **kwargs):
        return (lambda f: f) if not (len(args) == 1 and callable(args[0])) else args[0]
    prange = range

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "fvw")

# ----------------------------------------------------------------------------
# Baseline (CH-47 class, from src/tandem_rotor_config.py)
# ----------------------------------------------------------------------------
R = 9.14                 # rotor radius [m]
ROOT_CUT = 1.10          # root cutout [m]
NB = 3                   # blades per rotor
CHORD_ROOT = 0.82        # chord law c(x) = 0.82 * (1 - 0.15 x)   (x = r/R)
TAPER = 0.85
TWIST_RATE = np.radians(-8.0)  # linear washout per unit r/R
D_SEP = 13.60            # shaft separation [m] (1.487 R)
STAGGER = 1.30           # aft hub above forward hub [m]
V_TIP = 220.0            # tip speed [m/s] (baseline table value)
OMEGA = V_TIP / R
MASS = 22680.0
G0 = 9.80665
W = MASS * G0
RHO = 1.225
F_PLATE = 3.7            # fuselage equivalent flat-plate area [m^2]  (assumed, ~40 ft^2)

A0 = 5.73                # lift-curve slope [1/rad]
CD_MIN = 0.0095
EPS_CD = 1.15
N_GAMMA_IT = 6           # fixed-point iterations for bound circulation per step
RIGID_WAKE = False       # True = prescribed rigid wake (diagnostic / Model A)
CD_LIN = 0.0             # linear drag term (used for the NACA 0012 polar)
ALPHA_STALL = np.radians(14.0)
CL_CLIP = 1.45

NU = 1.5e-5              # air kinematic viscosity
ALPHA_L = 1.25643        # Lamb-Oseen constant
A1_VISC = 6.5e-5         # Bhagwat & Leishman: delta = 1 + a1 * Gamma / nu
CORE0_FRAC = 0.10        # initial core radius / chord (tip region)
CORE0_INBOARD = 0.30     # inboard trailers get a fatter core (sheet smoothing)


CONFIGS = {
    # CH-47 class baseline used by the project (src/tandem_rotor_config.py)
    "ch47": dict(CD_MIN=0.0095, CD_LIN=0.0, EPS_CD=1.15, ALPHA_STALL=np.radians(14.0), CL_CLIP=1.45, R=9.14, ROOT_CUT=1.10, NB=3, CHORD_ROOT=0.82, TAPER=0.85, TWIST_RATE=np.radians(-8.0),
                 D_SEP=13.60, STAGGER=1.30, V_TIP=220.0, W=22680.0 * 9.80665, F_PLATE=3.7),
    # Dingeldein NACA TN-3236 (1954) tandem model: 15 ft dia, 2 blades, sigma 0.054,
    # untwisted, untapered NACA 0012, shafts 1.03 D apart, coplanar, Vtip 500 ft/s,
    # CT = 0.0034 per rotor, f = 2 ft^2 per rotor (the test doubled lift and drag for the tandem).
    # Root cutout not stated: 0.15 R assumed.
    "dingeldein": dict(R=2.286, ROOT_CUT=0.343, NB=2, CHORD_ROOT=0.054 * np.pi * 2.286 / 2, TAPER=1.0,
                       TWIST_RATE=0.0, D_SEP=1.03 * 2 * 2.286, STAGGER=0.0, V_TIP=152.4,
                       W=2 * 0.0034 * 1.225 * np.pi * 2.286 ** 2 * 152.4 ** 2, F_PLATE=2 * 0.186,
                       # NACA 0012 section drag polar of the NACA single-rotor theory era:
                       # cd = 0.0087 - 0.0216 a + 0.400 a^2  (a in rad)
                       CD_MIN=0.0087, CD_LIN=-0.0216, EPS_CD=0.400, ALPHA_STALL=np.radians(12.0),
                       CL_CLIP=1.2),
}


def set_config(name):
    """overwrite the module-level geometry with one of CONFIGS"""
    g = globals()
    for k, v in CONFIGS[name].items():
        g[k] = v
    g["OMEGA"] = g["V_TIP"] / g["R"]
    g["CONFIG"] = name


def chord(x):
    return CHORD_ROOT * (1.0 - (1.0 - TAPER) * x)


# ----------------------------------------------------------------------------
# Biot-Savart kernels (numba)
# ----------------------------------------------------------------------------
@njit(parallel=True, fastmath=True)
def induced(points, A, B, gam, rc2):
    """Velocity at points (M,3) from straight segments A->B (S,3), strength gam,
    squared core radius rc2. Vatistas n=2 regularisation."""
    M = points.shape[0]
    S = A.shape[0]
    out = np.zeros((M, 3))
    inv4pi = 1.0 / (4.0 * np.pi)
    for m in prange(M):
        px, py, pz = points[m, 0], points[m, 1], points[m, 2]
        ux = 0.0
        uy = 0.0
        uz = 0.0
        for s in range(S):
            g = gam[s]
            if g == 0.0:
                continue
            ax = px - A[s, 0]; ay = py - A[s, 1]; az = pz - A[s, 2]
            bx = px - B[s, 0]; by = py - B[s, 1]; bz = pz - B[s, 2]
            r0x = B[s, 0] - A[s, 0]; r0y = B[s, 1] - A[s, 1]; r0z = B[s, 2] - A[s, 2]
            cx = ay * bz - az * by
            cy = az * bx - ax * bz
            cz = ax * by - ay * bx
            l0 = r0x * r0x + r0y * r0y + r0z * r0z
            if l0 < 1e-12:
                continue
            la = np.sqrt(ax * ax + ay * ay + az * az)
            lb = np.sqrt(bx * bx + by * by + bz * bz)
            if la < 1e-9 or lb < 1e-9:
                continue
            dot = r0x * (ax / la - bx / lb) + r0y * (ay / la - by / lb) + r0z * (az / la - bz / lb)
            c2 = cx * cx + cy * cy + cz * cz
            h2 = c2 / l0
            k = g * inv4pi * dot / (l0 * np.sqrt(rc2[s] * rc2[s] + h2 * h2))
            ux += k * cx
            uy += k * cy
            uz += k * cz
        out[m, 0] = ux
        out[m, 1] = uy
        out[m, 2] = uz
    return out


# ----------------------------------------------------------------------------
# Rotor object
# ----------------------------------------------------------------------------
class Rotor:
    def __init__(self, name, hub, spin, phase, tilt, n_span, n_age, dpsi):
        self.name = name
        self.hub = np.asarray(hub, float)
        self.spin = spin                    # +1 CCW from above, -1 CW
        self.phase = phase
        self.n_span = n_span
        self.n_age = n_age                  # number of wake rows kept (rows 0..n_age)
        self.dpsi = dpsi
        # shaft frame, tilted forward (thrust toward -x) by `tilt`
        ca, sa = np.cos(tilt), np.sin(tilt)
        self.ex = np.array([ca, 0.0, sa])
        self.ey = np.array([0.0, 1.0, 0.0])
        self.n = np.array([-sa, 0.0, ca])
        # spanwise edges, clustered at the tip
        # near-uniform panels: strong tip clustering makes the explicit lifting-line
        # iteration saw-tooth (tip panel narrower than the vortex core)
        k = np.arange(n_span + 1) / n_span
        x0 = ROOT_CUT / R
        xe = x0 + (1.0 - x0) * (0.75 * k + 0.25 * np.sin(0.5 * np.pi * k))
        self.r_edge = xe * R
        self.r_mid = 0.5 * (self.r_edge[1:] + self.r_edge[:-1])
        self.dr = np.diff(self.r_edge)
        self.c_mid = chord(self.r_mid / R)
        self.c_edge = chord(self.r_edge / R)
        self.twist = TWIST_RATE * self.r_mid / R
        # controls: collective, cosine, sine cyclic
        self.theta = np.array([np.radians(8.0), 0.0, 0.0])
        # state
        self.P = np.zeros((NB, n_age + 1, n_span + 1, 3))   # wake markers
        self.Vold = np.zeros_like(self.P)                    # previous marker velocity
        self.G = np.zeros((NB, n_age, n_span))               # ring strengths, row a = shed a steps ago
        self.age = np.zeros(n_age + 1)                       # wake age of each row [rad]
        self.age = np.arange(n_age + 1) * dpsi
        self.gmax = np.zeros(NB)

    def blade_psi(self, psi):
        return self.spin * (psi + 2.0 * np.pi * np.arange(NB) / NB) + self.phase

    def blade_geometry(self, psi):
        """unit radial / tangential vectors for each blade at rotor angle psi"""
        pb = self.blade_psi(psi)
        er = np.cos(pb)[:, None] * self.ex + np.sin(pb)[:, None] * self.ey
        et = self.spin * (-np.sin(pb)[:, None] * self.ex + np.cos(pb)[:, None] * self.ey)
        return pb, er, et

    def blade_points(self, psi):
        pb, er, et = self.blade_geometry(psi)
        edges = self.hub + er[:, None, :] * self.r_edge[None, :, None]
        mids = self.hub + er[:, None, :] * self.r_mid[None, :, None]
        return pb, er, et, edges, mids

    def init_wake(self, psi, vinf, lam_guess):
        """rigid skewed helix with momentum inflow, zero strength"""
        dt = self.dpsi / OMEGA
        for a in range(self.n_age + 1):
            _, _, _, edges, _ = self.blade_points(psi - a * self.dpsi)
            drift = (vinf - lam_guess * V_TIP * self.n) * a * dt
            self.P[:, a] = edges + drift
        self.Vold[:] = 0.0
        self.G[:] = 0.0

    def segments(self):
        """net filament segments of this rotor's lattice (bound + wake)."""
        P, G = self.P, self.G
        nb, na1, ne, _ = P.shape
        na = na1 - 1
        ns = ne - 1
        s = self.spin
        A_list, B_list, g_list, rc_list = [], [], [], []
        # spanwise segments on row a: strength G[a] - G[a-1]; row na: -G[na-1]
        Gpad = np.zeros((nb, na + 1, ns))
        Gpad[:, :na] = G
        Gprev = np.zeros((nb, na + 1, ns))
        Gprev[:, 1:] = G
        gs = (Gpad - Gprev) * s
        A_list.append(P[:, :, :-1].reshape(-1, 3))
        B_list.append(P[:, :, 1:].reshape(-1, 3))
        g_list.append(gs.reshape(-1))
        rc_list.append(np.broadcast_to(self._core_span()[None, None, :], (nb, na + 1, ns)).reshape(-1))
        # trailed segments at edge i between rows a and a+1: G[a,i-1] - G[a,i]
        Gl = np.zeros((nb, na, ne))
        Gr = np.zeros((nb, na, ne))
        Gl[:, :, 1:] = G
        Gr[:, :, :-1] = G
        gt = (Gl - Gr) * s
        A_list.append(P[:, :-1].reshape(-1, 3))
        B_list.append(P[:, 1:].reshape(-1, 3))
        g_list.append(gt.reshape(-1))
        age_mid = 0.5 * (self.age[1:] + self.age[:-1])
        rct = self._core_trailer(age_mid)            # (na, ne)
        rc_list.append(np.broadcast_to(rct[None], (nb, na, ne)).reshape(-1))
        return (np.concatenate(A_list), np.concatenate(B_list),
                np.concatenate(g_list), np.concatenate(rc_list) ** 2)

    def _core_span(self):
        return np.full(self.n_span, CORE0_INBOARD * CHORD_ROOT)

    def _core_trailer(self, age):
        gam = max(np.max(np.abs(self.gmax)), 1.0)
        delta = 1.0 + A1_VISC * gam / NU
        r0 = np.where(np.arange(self.n_span + 1) >= self.n_span - 1,
                      CORE0_FRAC, CORE0_INBOARD) * self.c_edge
        grow = 4.0 * ALPHA_L * delta * NU * age / OMEGA
        return np.sqrt(r0[None, :] ** 2 + grow[:, None])


def airfoil(alpha):
    cl = A0 * alpha
    cd = CD_MIN + CD_LIN * alpha + EPS_CD * alpha ** 2
    st = np.abs(alpha) >= ALPHA_STALL
    cl = np.where(st, np.sign(alpha) * np.minimum(np.abs(cl), CL_CLIP), cl)
    cd = np.where(st, np.maximum(cd, 0.05), cd)
    return cl, cd


def blade_loads(rot, psi, vind_mid, vinf):
    """lifting-line section solution given induced velocity at panel midpoints."""
    pb, er, et, edges, mids = rot.blade_points(psi)
    th = (rot.theta[0] + rot.twist[None, :]
          + rot.theta[1] * np.cos(pb)[:, None] + rot.theta[2] * np.sin(pb)[:, None])
    w = vinf[None, None, :] + vind_mid                       # air velocity (inertial)
    ut = OMEGA * rot.r_mid[None, :] - np.einsum("bsk,bk->bs", w, et)
    up = -np.einsum("bsk,k->bs", w, rot.n)
    U = np.sqrt(ut ** 2 + up ** 2)
    phi = np.arctan2(up, ut)
    alpha = th - phi
    cl, cd = airfoil(alpha)
    gam = 0.5 * U * rot.c_mid[None, :] * cl
    Lp = RHO * U * gam
    Dp = 0.5 * RHO * U ** 2 * rot.c_mid[None, :] * cd
    dT = (Lp * np.cos(phi) - Dp * np.sin(phi)) * rot.dr[None, :]
    dF = (Lp * np.sin(phi) + Dp * np.cos(phi)) * rot.dr[None, :]
    dFp = Dp * np.cos(phi) * rot.dr[None, :]
    T = dT.sum()
    Q = (dF * rot.r_mid[None, :]).sum()
    Q0 = (dFp * rot.r_mid[None, :]).sum()
    # hub moments from thrust distribution, in shaft frame
    arm = rot.r_mid[None, :] * dT
    Mx = (arm * np.sin(pb)[:, None]).sum()    # about ex  (roll-like)
    My = -(arm * np.cos(pb)[:, None]).sum()   # about ey  (pitch-like)
    return dict(gam=gam, T=T, Q=Q, Q0=Q0, Mx=Mx, My=My, up=up, alpha=alpha)


# ----------------------------------------------------------------------------
# Simulation
# ----------------------------------------------------------------------------
def gather(rotors, skip=None):
    As, Bs, gs, rcs = [], [], [], []
    for r in rotors:
        if r is skip:
            continue
        a, b, g, rc = r.segments()
        As.append(a); Bs.append(b); gs.append(g); rcs.append(rc)
    return (np.ascontiguousarray(np.concatenate(As)), np.ascontiguousarray(np.concatenate(Bs)),
            np.ascontiguousarray(np.concatenate(gs)), np.ascontiguousarray(np.concatenate(rcs)))


def trim_jacobian(rot, vinf, lam):
    """dT, dMx, dMy / d(theta0, theta1c, theta1s) with uniform inflow, over one rev."""
    def avg(theta):
        save = rot.theta.copy()
        rot.theta = theta
        acc = np.zeros(3)
        for p in np.linspace(0, 2 * np.pi / NB, 12, endpoint=False):
            vm = np.broadcast_to(-lam * V_TIP * rot.n, (NB, rot.n_span, 3))
            L = blade_loads(rot, p, vm, vinf)
            acc += [L["T"], L["Mx"], L["My"]]
        rot.theta = save
        return acc / 12
    base = avg(rot.theta)
    J = np.zeros((3, 3))
    for j in range(3):
        th = rot.theta.copy()
        th[j] += np.radians(0.5)
        J[:, j] = (avg(th) - base) / np.radians(0.5)
    return J


def run_case(mu, config, n_span=8, dpsi_deg=10.0, wake_revs=5.0, n_revs=10,
             trim_start=1, verbose=True, sample_grid=True):
    """config: 'single' (forward rotor alone) or 'tandem'."""
    dpsi = np.radians(dpsi_deg)
    dt = dpsi / OMEGA
    n_age = int(round(wake_revs * 2 * np.pi / dpsi))
    V = mu * V_TIP
    drag = 0.5 * RHO * V ** 2 * F_PLATE
    tilt = np.arctan2(drag, W)
    vinf = np.array([V * np.cos(0.0), 0.0, 0.0])
    T_target = 0.5 * W

    rotors = [Rotor("fwd", [0, 0, 0], +1, 0.0, tilt, n_span, n_age, dpsi)]
    if config == "tandem":
        rotors.append(Rotor("aft", [D_SEP, 0, STAGGER], -1, np.pi + np.pi / NB, tilt, n_span, n_age, dpsi))

    # momentum (Glauert) inflow for initial wake and reference
    A_disk = np.pi * R ** 2
    CT = T_target / (RHO * A_disk * V_TIP ** 2)
    lam = np.sqrt(CT / 2)
    for _ in range(50):
        lam = CT / (2 * np.sqrt(mu ** 2 + lam ** 2))
    lam_i = lam  # induced inflow ratio (shaft ~ TPP, small tilt)
    for r in rotors:
        r.init_wake(0.0, vinf, lam_i)
    # pre-trim every rotor on uniform Glauert inflow so the free-wake run starts close
    J = {}
    for r in rotors:
        for _ in range(4):
            Jr = trim_jacobian(r, vinf, lam_i)
            acc = np.zeros(3)
            for p in np.linspace(0, 2 * np.pi / NB, 12, endpoint=False):
                vm = np.broadcast_to(-lam_i * V_TIP * r.n, (NB, r.n_span, 3))
                L = blade_loads(r, p, vm, vinf)
                acc += [L["T"], L["Mx"], L["My"]]
            acc /= 12
            r.theta = r.theta + np.linalg.solve(Jr, np.array([T_target, 0, 0]) - acc)
        J[r.name] = Jr

    steps_per_rev = int(round(2 * np.pi / dpsi))
    n_steps = n_revs * steps_per_rev
    hist = {r.name: [] for r in rotors}
    rev_acc = {r.name: np.zeros(5) for r in rotors}

    # aft-disk sampling grid (in the aft rotor's plane, aft-hub frame)
    rg = np.linspace(0.15, 0.98, 12) * R
    pg = np.radians(np.arange(0, 360, 10))
    hub_aft = np.array([D_SEP, 0, STAGGER])
    n_aft = rotors[0].n
    gx = hub_aft[0] + np.outer(np.cos(pg), rg) * rotors[0].ex[0]
    gz = hub_aft[2] + np.outer(np.cos(pg), rg) * rotors[0].ex[2]
    gy = np.outer(np.sin(pg), rg)
    grid = np.ascontiguousarray(np.stack([gx, gy, gz], -1).reshape(-1, 3))
    grid_acc = np.zeros(grid.shape[0])
    grid_n = 0

    t0 = time.time()
    psi = 0.0
    for step in range(n_steps):
        # --- 1. solve bound circulation (row 0 strengths) with the wake frozen
        for it in range(N_GAMMA_IT):
            Aall, Ball, gall, rcall = gather(rotors)
            for r in rotors:
                _, _, _, _, mids = r.blade_points(psi)
                v = induced(np.ascontiguousarray(mids.reshape(-1, 3)), Aall, Ball, gall, rcall)
                L = blade_loads(r, psi, v.reshape(NB, r.n_span, 3), vinf)
                r.G[:, 0] = 0.5 * r.G[:, 0] + 0.5 * L["gam"] if it else L["gam"]
                r._loads = L
        for r in rotors:
            r.gmax = np.max(np.abs(r.G[:, 0]), axis=1)
            L = r._loads
            rev_acc[r.name] += [L["T"], L["Q"], L["Q0"], L["Mx"], L["My"]]

        # --- sample forward-rotor-induced inflow on the aft disk (last 2 revs)
        if config == "tandem" and step >= n_steps - 2 * steps_per_rev and sample_grid:
            Af, Bf, gf, rcf = gather([rotors[0]])
            vg = induced(grid, Af, Bf, gf, rcf)
            grid_acc += -(vg @ n_aft)
            grid_n += 1

        # --- 2. convect wake markers (AB2)
        Aall, Ball, gall, rcall = gather(rotors)
        for r in rotors:
            pts = np.ascontiguousarray(r.P.reshape(-1, 3))
            if RIGID_WAKE:      # diagnostic: skewed helix convected at the Glauert inflow
                v = np.broadcast_to(vinf - lam_i * V_TIP * r.n, r.P.shape).copy()
            else:
                v = induced(pts, Aall, Ball, gall, rcall).reshape(r.P.shape) + vinf
            if step == 0:
                vstep = v
            else:
                vstep = 1.5 * v - 0.5 * r.Vold
                vstep[:, 0] = v[:, 0]          # blade-attached row: first-order release
            newP = np.empty_like(r.P)
            newP[:, 1:] = r.P[:, :-1] + dt * vstep[:, :-1]
            newV = np.empty_like(v)
            newV[:, 1:] = v[:, :-1]
            newV[:, 0] = v[:, 0]
            r.Vold = newV
            r.P = newP
            r.G[:, 1:] = r.G[:, :-1].copy()
        psi += dpsi
        for r in rotors:
            _, _, _, edges, _ = r.blade_points(psi)
            r.P[:, 0] = edges

        # --- 3. once per revolution: record and trim
        if (step + 1) % steps_per_rev == 0:
            rev = (step + 1) // steps_per_rev
            for r in rotors:
                T, Q, Q0, Mx, My = rev_acc[r.name] / steps_per_rev
                hist[r.name].append(dict(rev=rev, T=T, P=Q * OMEGA, P0=Q0 * OMEGA, Mx=Mx, My=My,
                                         theta=np.degrees(r.theta).tolist()))
                rev_acc[r.name][:] = 0
                if rev >= trim_start:
                    err = np.array([T_target - T, -Mx, -My])
                    r.theta = r.theta + (1.0 if rev < 5 else 0.5) * np.linalg.solve(J[r.name], err)
                if verbose:
                    print(f"  mu={mu:.2f} {config:6s} {r.name} rev {rev:2d}: T={T/1e3:7.1f} kN "
                          f"P={Q*OMEGA/1e3:7.1f} kW  Mx={Mx/1e3:6.1f} My={My/1e3:6.1f} kNm  "
                          f"theta=({', '.join(f'{d:.2f}' for d in np.degrees(r.theta))}) deg "
                          f"[{time.time()-t0:.0f}s]", flush=True)

    res = dict(mu=mu, V=V, config=config, tilt_deg=float(np.degrees(tilt)), lam_glauert=float(lam_i),
               CT=float(CT), hist=hist, n_span=n_span, dpsi_deg=dpsi_deg, wake_revs=wake_revs,
               T_target=T_target)
    if config == "tandem" and grid_n:
        res["aft_grid"] = dict(r=rg.tolist(), psi_deg=np.degrees(pg).tolist(),
                               v_down=(grid_acc / grid_n).reshape(len(pg), len(rg)).tolist())
    # final wake geometry snapshot (tip trailers) for plotting
    res["tip_wake"] = {r.name: r.P[:, :, -1, :].tolist() for r in rotors}
    return res


def final(res, name, nrev=4):
    """mean (and rev-to-rev std, key + '_std') over the last nrev revolutions"""
    h = res["hist"][name][-nrev:]
    out = {k: float(np.mean([e[k] for e in h])) for k in ("T", "P", "P0", "Mx", "My")}
    out.update({k + "_std": float(np.std([e[k] for e in h])) for k in ("T", "P")})
    return out


# ----------------------------------------------------------------------------
# Reference models
# ----------------------------------------------------------------------------
def coleman_skewed_on_aft(mu, lam_i, grid_r, grid_psi_deg):
    """Coleman, Feingold & Stempin skewed-cylinder inflow of the forward rotor,
    v = v0 (1 + tan(chi/2) x/R), applied where an aft-disk point lies inside
    the forward disk (overlap); zero elsewhere. Returns downwash [m/s] on grid."""
    v0 = lam_i * V_TIP
    chi = np.arctan2(mu, lam_i)
    out = np.zeros((len(grid_psi_deg), len(grid_r)))
    for i, p in enumerate(np.radians(grid_psi_deg)):
        x = D_SEP + grid_r * np.cos(p)          # position relative to forward hub
        y = grid_r * np.sin(p)
        inside = x ** 2 + y ** 2 <= R ** 2
        out[i] = np.where(inside, v0 * (1 + np.tan(chi / 2) * x / R), 0.0)
    return out


def glauert_power(mu, T, kappa=1.0):
    A = np.pi * R ** 2
    CT = T / (RHO * A * V_TIP ** 2)
    lam = np.sqrt(CT / 2)
    for _ in range(80):
        lam = CT / (2 * np.sqrt(mu ** 2 + lam ** 2))
    return kappa * T * lam * V_TIP


# ----------------------------------------------------------------------------
def main():
    global OUT
    quick = "--quick" in sys.argv
    for a in sys.argv[1:]:
        if a.startswith("--out="):
            OUT = os.path.abspath(a[len("--out="):])
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cfg_name = args[0] if args else "ch47"
    set_config(cfg_name)
    os.makedirs(OUT, exist_ok=True)
    kw = dict(n_span=6, dpsi_deg=15.0, wake_revs=4.0, n_revs=6) if quick else \
         dict(n_span=8, dpsi_deg=10.0, wake_revs=5.0, n_revs=12)
    mus = [0.1, 0.2] if len(args) < 2 else [float(m) for m in args[1].split(",")]
    summary_path = os.path.join(OUT, f"{cfg_name}_summary.json")
    summary = []
    if os.path.exists(summary_path):     # keep cases at other advance ratios
        with open(summary_path) as f:
            summary = [s for s in json.load(f) if not any(abs(s["mu"] - m) < 1e-9 for m in mus)]
    for mu in mus:
        for cfg in ("single", "tandem"):
            print(f"=== mu = {mu}, {cfg} ===", flush=True)
            res = run_case(mu, cfg, **kw)
            with open(os.path.join(OUT, f"{cfg_name}_mu{mu:.2f}_{cfg}.json"), "w") as f:
                json.dump(res, f)
            for name in res["hist"]:
                fr = final(res, name)
                if cfg == "single":
                    print(f"  single-rotor induced-power factor kappa = "
                          f"{(fr['P'] - fr['P0'] - fr['T'] * np.sin(np.radians(res['tilt_deg'])) * res['V']) / glauert_power(mu, fr['T']):.3f}")
                # rotor shaft power = induced + profile + share of propulsive work
                P_prop = fr["T"] * np.sin(np.radians(res["tilt_deg"])) * res["V"]
                summary.append(dict(mu=mu, config=cfg, rotor=name, **fr, P_prop=P_prop,
                                    P_induced=fr["P"] - fr["P0"] - P_prop,
                                    P_glauert_induced=glauert_power(mu, fr["T"]),
                                    tilt_deg=res["tilt_deg"]))
            with open(os.path.join(OUT, f"{cfg_name}_summary.json"), "w") as f:
                json.dump(summary, f, indent=1)
    with open(os.path.join(OUT, f"{cfg_name}_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    for s in summary:
        print(s)


if __name__ == "__main__":
    main()
