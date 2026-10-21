"""
plot_tandem_forward_flight.py

Rotorcraft assessment in FORWARD FLIGHT: CH-47 class tandem at MTOW, sea-level
ISA, advance-ratio sweep, baseline (no interference) vs Coleman skewed-cylinder
vs free-vortex-wake interference, all through the integrated edgewise BEMT
(src/tandem_forward_flight.py).

Assumptions: equal thrust split, each rotor trimmed to W/2 with zero hub
moments, shaft tilt balances fuselage drag (f = 3.7 m^2, assumed), tip speed
220 m/s, forward rotor CCW / aft rotor CW seen from above, one-way coupling
(forward wake on aft rotor only).  FVW maps are valid for this geometry only
(d = 13.60 m, aft hub 1.30 m higher) and are trusted up to mu ~ 0.2.

Outputs: outputs/mp/tandem_forward_flight.png
         outputs/mp/tandem_forward_flight_table.md
"""

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import tandem_rotor_config as C
from environment import isa
from tandem_forward_flight import solve_tandem_forward_flight, get_fvw_map

V_TIP = 220.0
OMEGA = V_TIP / C.FWD_ROTOR_RADIUS_M
FLAT_PLATE_M2 = 3.7
MODELS = (("none", "Baseline (no interference)", "#52514e", "-"),
          ("coleman", "Coleman skewed cylinder (overlap only)", "#2a78d6", ":"),
          ("fvw", "Free-vortex-wake interference", "#eb6834", "-"))


def run_sweep():
    atm = isa(0.0, 0.0)
    rho, a = atm.density_kg_m3, atm.speed_of_sound_mps
    W = C.GROSS_MASS_KG * C.G
    cached = get_fvw_map("ch47").mu
    mus = np.unique(np.round(np.concatenate([cached, 0.5 * (cached[1:] + cached[:-1])]), 4))
    res = {m: [] for m, *_ in MODELS}
    for mu in mus:
        for m, *_ in MODELS:
            r = solve_tandem_forward_flight(C.build_fwd_rotor(), C.build_aft_rotor(), C.default_airfoil_provider,
                                            mu, OMEGA, W, rho, a, C.LONGITUDINAL_SEP_M, FLAT_PLATE_M2, model=m)
            if not r.converged:
                raise RuntimeError(f"trim failed at mu={mu:.3f}, model={m}")
            res[m].append(r)
    return mus, cached, res, W


def standalone_fvw():
    with open(os.path.join(SRC_DIR, "data", "fvw", "ch47_summary.json")) as f:
        S = json.load(f)
    out = {}
    for s in S:
        out.setdefault(round(s["mu"], 3), {})[(s["config"], s["rotor"])] = s["P"]
    pts = []
    for mu, d in sorted(out.items()):
        if ("single", "fwd") in d and ("tandem", "aft") in d:
            iso = d[("single", "fwd")]
            pts.append((mu, d[("tandem", "fwd")] + d[("tandem", "aft")], 2 * iso,
                        (d[("tandem", "aft")] / iso - 1) * 100))
    return np.array(pts)


def main():
    mus, cached, res, W = run_sweep()
    P = {m: np.array([r.total_power_W for r in res[m]]) / 1e3 for m in res}
    P_aft = {m: np.array([r.aft.result.power_W for r in res[m]]) / 1e3 for m in res}
    th0 = {m: np.array([r.aft.theta0_deg for r in res[m]]) for m in res}
    th1s = {m: np.array([r.aft.theta1s_deg for r in res[m]]) for m in res}
    th1c = {m: np.array([r.aft.theta1c_deg for r in res[m]]) for m in res}
    dv = {m: np.array([r.mean_dv_aft for r in res[m]]) for m in res}
    V = mus * V_TIP
    P_avail = C.INSTALLED_SHAFT_POWER_W * C.DRIVETRAIN_EFFICIENCY / 1e3
    roc = {m: (P_avail - P[m]) * 1e3 / W for m in res}           # excess-power climb rate [m/s]
    sa = standalone_fvw()

    # ---------------- table ----------------
    lines = ["| μ | V [m/s] | P baseline [kW] | P Coleman [kW] | P FVW [kW] | ΔP FVW | aft ΔP FVW | "
             "mean Δv aft FVW / Coleman [m/s] | aft Δθ0 FVW [deg] | ROC margin base / FVW [m/s] |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for i, mu in enumerate(mus):
        lines.append(
            f"| {mu:.3f} | {V[i]:.1f} | {P['none'][i]:.0f} | {P['coleman'][i]:.0f} | {P['fvw'][i]:.0f} | "
            f"{(P['fvw'][i] / P['none'][i] - 1) * 100:+.1f} % | {(P_aft['fvw'][i] / P_aft['none'][i] - 1) * 100:+.0f} % | "
            f"{dv['fvw'][i]:.1f} / {dv['coleman'][i]:.1f} | {th0['fvw'][i] - th0['none'][i]:+.2f} | "
            f"{roc['none'][i]:.1f} / {roc['fvw'][i]:.1f} |")
    out_dir = os.path.join(PROJECT_ROOT, "outputs", "mp")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "tandem_forward_flight_table.md"), "w", encoding="utf-8") as f:
        f.write("# CH-47 class tandem, forward flight, MTOW, SL ISA\n\n" + "\n".join(lines) + "\n\n"
                f"Rotor power available: {P_avail:.0f} kW (7 MW installed × 0.96 drivetrain). "
                "ROC margin = (P_avail − P_req) / W, rotor power only.\n")
    print("\n".join(lines))

    # ---------------- figure ----------------
    fig, ax = plt.subplots(2, 2, figsize=(12, 8.6))
    a = ax[0, 0]
    for m, lab, c, ls in MODELS:
        a.plot(mus, P[m], ls, color=c, lw=2, label=lab)
    if len(sa):
        a.plot(sa[:, 0], sa[:, 1] / 1e3, "D", color="#7a4fb0", mfc="none", ms=7, mew=1.4,
               label="Standalone free-vortex wake (tandem total)")
    a.axhline(P_avail, color="#0b0b0b", lw=1, ls="--")
    a.text(mus[0], P_avail - 260, f"Rotor power available {P_avail / 1e3:.2f} MW", fontsize=8)
    a.set_xlabel("Advance ratio μ [-]")
    a.set_ylabel("Total rotor shaft power [kW]")
    a.set_ylim(0, P_avail * 1.08)
    a.legend(frameon=False, fontsize=7.5, loc="lower left")
    a.set_title("(a) Power required, both rotors", fontsize=10)

    a = ax[0, 1]
    for m, lab, c, ls in MODELS[1:]:
        a.plot(mus, (P_aft[m] / P_aft["none"] - 1) * 100, ls, color=c, lw=2, label=f"Aft rotor, {lab}")
        a.plot(mus, (P[m] / P["none"] - 1) * 100, "--", color=c, lw=1.3, label=f"Total, {lab}")
    if len(sa):
        a.plot(sa[:, 0], sa[:, 3], "D", color="#7a4fb0", mfc="none", ms=7, mew=1.4,
               label="Aft rotor, standalone free-vortex wake")
    a.set_xlabel("Advance ratio μ [-]")
    a.set_ylabel("Power increase over baseline [%]")
    a.set_ylim(0, 100)
    a.legend(frameon=False, fontsize=7, loc="upper right")
    a.set_title("(b) Interference power penalty", fontsize=10)

    a = ax[1, 0]
    for m, lab, c, ls in MODELS:
        a.plot(mus, th0[m], ls, color=c, lw=2, label=f"θ0, {lab}")
    a.plot(mus, th1s["none"], "-", color="#52514e", lw=1, alpha=0.7, label="θ1s, baseline")
    a.plot(mus, th1s["fvw"], "-", color="#eb6834", lw=1, alpha=0.7, label="θ1s, FVW")
    a.plot(mus, th1c["none"], "--", color="#52514e", lw=1, alpha=0.7, label="θ1c, baseline")
    a.plot(mus, th1c["fvw"], "--", color="#eb6834", lw=1, alpha=0.7, label="θ1c, FVW")
    a.set_xlabel("Advance ratio μ [-]")
    a.set_ylabel("Aft-rotor blade pitch [deg]")
    a.set_ylim(-13, 9)
    a.legend(frameon=False, fontsize=7, ncol=2, loc="lower left")
    a.set_title("(c) Aft-rotor trim controls (collective at root incl. 10° twist offset)", fontsize=10)

    a = ax[1, 1]
    for m, lab, c, ls in MODELS:
        a.plot(mus, roc[m], ls, color=c, lw=2, label=lab)
    a.set_xlabel("Advance ratio μ [-]")
    a.set_ylabel("Excess-power climb rate [m/s]")
    a.legend(frameon=False, fontsize=7.5, loc="lower right")
    a.set_title("(d) Climb margin at MTOW", fontsize=10)
    for a in ax.flat:
        a.grid(alpha=0.3)
        a.axvspan(0.20, mus[-1] + 0.005, color="#e4e3df", alpha=0.5, lw=0)
        a.set_xlim(mus[0] - 0.005, mus[-1] + 0.005)
        sec = a.secondary_xaxis("top", functions=(lambda x: x * V_TIP, lambda v: v / V_TIP))
        sec.set_xlabel("V [m/s]", fontsize=8)
    fig.suptitle("CH-47 class tandem in level forward flight: baseline vs augmented BEMT", fontsize=11)
    fig.text(0.5, -0.03,
             "MTOW 22 680 kg, sea-level ISA, ΩR = 220 m/s, d = 13.60 m (1.49 R, 14.9 % overlap), aft hub 1.30 m higher, "
             "equal thrust split, each rotor trimmed to W/2 with zero hub moments,\nshaft tilt from fuselage drag "
             "(f = 3.7 m², assumed). FVW interference: one-way, forward wake on aft rotor; maps cached at μ = "
             + ", ".join(f"{m:.2f}" for m in cached) + ", linear in between. Shaded: μ > 0.2, outside validated range.",
             ha="center", fontsize=8, color="#333333")
    fig.tight_layout()
    path = os.path.join(out_dir, "tandem_forward_flight.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
