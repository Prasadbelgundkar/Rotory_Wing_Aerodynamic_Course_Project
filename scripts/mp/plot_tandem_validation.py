"""
plot_tandem_validation.py

Quantitative validation of the tandem interference models against
Dingeldein (1954), NACA TN-3236, Figure 6: level-flight power of a tandem
model rotor (front, rear and single rotor measured separately).

Rig (TN-3236): two 15 ft diameter (R = 2.286 m) two-blade rotors, solidity
0.054, untwisted, untapered NACA 0012, shafts 1.03 D apart, coplanar, NO disk
overlap, Omega R = 500 ft/s, C_T = 0.0034 per rotor, f = 2 ft^2 per rotor.
Root cutout not stated in the report: 0.15 R assumed.

Predictions, all from the integrated tool (src/tandem_forward_flight.py):
  * isolated rotor   : edgewise BEMT, interference 'none'
  * rear rotor       : edgewise BEMT + 'coleman' or + 'fvw' interference field
  * standalone FVW   : full free-vortex wake runs (src/tandem_fvw.py), for reference

Only published data digitised from TN-3236 Fig. 6 (src/data/dingeldein_tn3236_fig6.csv)
is used for validation.

Outputs: outputs/mp/tandem_validation_dingeldein.png
         outputs/mp/tandem_validation_table.md
"""

import csv
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

from airfoil import LinearAirfoil
from rotor import Rotor, constant_chord, constant_twist
from tandem_forward_flight import solve_tandem_forward_flight, get_fvw_map

HP = 745.7
RHO, A_SOUND = 1.225, 340.3            # sea-level standard (tunnel conditions)
RADIUS_M = 2.286                       # 7.5 ft
ROOT_CUTOUT_M = 0.15 * RADIUS_M        # assumed
NUM_BLADES = 2
SIGMA = 0.054
CHORD_M = SIGMA * np.pi * RADIUS_M / NUM_BLADES
V_TIP = 152.4                          # 500 ft/s
OMEGA = V_TIP / RADIUS_M
SEP_M = 1.03 * 2.0 * RADIUS_M
CT = 0.0034
WEIGHT_N = 2.0 * CT * RHO * np.pi * RADIUS_M ** 2 * V_TIP ** 2   # both rotors
FLAT_PLATE_M2 = 2.0 * 0.186            # 2 ft^2 per rotor, doubled for the tandem

# NACA 0012 section polar used in the NACA single-rotor theory of the period:
# cd = 0.0087 - 0.0216 a + 0.400 a^2; the linear term is dropped (LinearAirfoil form).
AIRFOIL = LinearAirfoil(a0=5.73, Cd_min=0.0087, eps=0.400,
                        stall_alpha_rad=np.radians(12.0), Cl_max_clip=1.2)

C_ISO, C_AFT, C_FWD, C_FVW = "#52514e", "#eb6834", "#2a78d6", "#7a4fb0"


def build_rotor(name):
    return Rotor(radius_m=RADIUS_M, root_cutout_m=ROOT_CUTOUT_M, num_blades=NUM_BLADES,
                 chord_fn=constant_chord(CHORD_M), twist_fn=constant_twist(0.0), name=name)


def load_measured():
    meas = {}
    path = os.path.join(SRC_DIR, "data", "dingeldein_tn3236_fig6.csv")
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(l for l in fh if not l.startswith("#")):
            meas.setdefault(row["series"], []).append((float(row["mu"]), float(row["power_hp"])))
    return {k: np.array(v) for k, v in meas.items()}


def nearest(series, mu, tol=0.008):
    i = int(np.argmin(np.abs(series[:, 0] - mu)))
    return series[i, 1] if abs(series[i, 0] - mu) <= tol else np.nan


def standalone_fvw():
    with open(os.path.join(SRC_DIR, "data", "fvw", "dingeldein_summary.json")) as f:
        S = json.load(f)
    out = {}
    for s in S:
        out.setdefault(round(s["mu"], 3), {})[(s["config"], s["rotor"])] = s["P"] / HP
    return out


def run_tandem_validation():
    meas = load_measured()
    mus = get_fvw_map("dingeldein").mu
    fwd_rot, aft_rot = build_rotor("TN-3236 front"), build_rotor("TN-3236 rear")
    pred = {m: [] for m in ("none", "coleman", "fvw")}
    for mu in mus:
        for model in pred:
            r = solve_tandem_forward_flight(fwd_rot, aft_rot, lambda x: AIRFOIL, mu, OMEGA, WEIGHT_N,
                                            RHO, A_SOUND, SEP_M, FLAT_PLATE_M2, model=model,
                                            fvw_config="dingeldein")
            if not r.converged:
                raise RuntimeError(f"trim failed at mu={mu:.3f}, model={model}")
            pred[model].append((r.fwd.result.power_W / HP, r.aft.result.power_W / HP))
    pred = {k: np.array(v) for k, v in pred.items()}
    iso = pred["none"][:, 0]
    aft_fvw, aft_col = pred["fvw"][:, 1], pred["coleman"][:, 1]
    sa = standalone_fvw()
    sa_iso = np.array([sa[round(m, 3)][("single", "fwd")] for m in mus])
    sa_aft = np.array([sa[round(m, 3)][("tandem", "aft")] for m in mus])

    m_single = np.array([nearest(meas["single_rotor"], m) for m in mus])
    m_rear = np.array([nearest(meas["rear_rotor"], m) for m in mus])
    m_inc = m_rear - m_single

    # ---------------- table ----------------
    rows = []
    lines = ["| μ | single meas. [hp] | BEMT isolated | rear meas. | BEMT+FVW rear | err | "
             "rear−single meas. | BEMT+FVW Δ | Coleman Δ | standalone FVW Δ |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for i, mu in enumerate(mus):
        err = (aft_fvw[i] - m_rear[i]) / m_rear[i] * 100
        rows.append(err)
        lines.append(f"| {mu:.3f} | {m_single[i]:.1f} | {iso[i]:.1f} | {m_rear[i]:.1f} | {aft_fvw[i]:.1f} | "
                     f"{err:+.0f} % | {m_inc[i]:.1f} | {aft_fvw[i] - iso[i]:.1f} | {aft_col[i] - iso[i]:.1f} | "
                     f"{sa_aft[i] - sa_iso[i]:.1f} |")
    low = mus <= 0.20
    mape_low = float(np.nanmean(np.abs(np.array(rows))[low]))
    inc_err_low = float(np.nanmean(np.abs(((aft_fvw - iso) - m_inc) / m_inc)[low]) * 100)
    lines += ["", f"Rear-rotor power, BEMT+FVW, mean |error| for μ ≤ 0.20: {mape_low:.1f} %.",
              f"Interference increment, BEMT+FVW, mean |error| for μ ≤ 0.20: {inc_err_low:.0f} % (under-predicted).",
              "Coleman overlap model: 0 hp at every μ (the TN-3236 disks do not overlap)."]
    out_dir = os.path.join(PROJECT_ROOT, "outputs", "mp")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "tandem_validation_table.md"), "w", encoding="utf-8") as f:
        f.write("# Validation against Dingeldein NACA TN-3236 Fig. 6\n\n" + "\n".join(lines) + "\n")
    print("\n".join(lines))

    # ---------------- figure ----------------
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    ax[0].plot(meas["single_rotor"][:, 0], meas["single_rotor"][:, 1], "o", color=C_ISO, mfc="none", ms=8,
               mew=1.5, label="Single rotor, measured")
    ax[0].plot(meas["rear_rotor"][:, 0], meas["rear_rotor"][:, 1], "^", color=C_AFT, mfc="none", ms=8,
               mew=1.5, label="Rear rotor, measured")
    ax[0].plot(meas["front_rotor"][:, 0], meas["front_rotor"][:, 1], "s", color=C_FWD, mfc="none", ms=7,
               mew=1.2, label="Front rotor, measured (not modelled)")
    ax[0].plot(mus, iso, "-", color=C_ISO, lw=2, label="BEMT, isolated rotor (baseline)")
    ax[0].plot(mus, aft_col, ":", color=C_FWD, lw=2, label="BEMT + Coleman, rear rotor (= baseline)")
    ax[0].plot(mus, aft_fvw, "-", color=C_AFT, lw=2, label="BEMT + FVW interference, rear rotor")
    ax[0].set_xlabel("Tip-speed ratio μ [-]")
    ax[0].set_ylabel("Rotor shaft power [hp]")
    ax[0].set_xlim(0.05, 0.32)
    ax[0].set_ylim(0, 32)
    ax[0].legend(frameon=False, fontsize=7.5, loc="lower right")
    ax[0].set_title("(a) Rotor power", fontsize=10)
    ax[0].grid(alpha=0.3)

    ax[1].plot(mus, m_inc, "^", color=C_AFT, mfc="none", ms=9, mew=1.6, label="Measured: rear − single")
    ax[1].plot(mus, aft_fvw - iso, "-o", color=C_AFT, lw=2, ms=4, label="BEMT + FVW interference field")
    ax[1].plot(mus, sa_aft - sa_iso, "--", color=C_FVW, lw=1.5, label="Standalone free-vortex wake")
    ax[1].plot(mus, aft_col - iso, ":", color=C_FWD, lw=2, label="BEMT + Coleman (no overlap → 0)")
    ax[1].axvspan(0.20, 0.32, color="#e4e3df", alpha=0.5, lw=0)
    ax[1].text(0.205, 10.0, "μ > 0.2: blade model\nunreliable", fontsize=7.5, color=C_ISO)
    ax[1].set_xlabel("Tip-speed ratio μ [-]")
    ax[1].set_ylabel("Extra rear-rotor power from interference [hp]")
    ax[1].set_xlim(0.05, 0.32)
    ax[1].set_ylim(-1, 18)
    ax[1].legend(frameon=False, fontsize=7.5, loc="upper right")
    ax[1].set_title("(b) Interference increment", fontsize=10)
    ax[1].grid(alpha=0.3)

    fig.suptitle("Validation vs. Dingeldein, NACA TN-3236 Fig. 6 (level flight, sea level)", fontsize=11)
    fig.text(0.5, -0.06,
             "Two 2-blade rotors, R = 2.286 m, σ = 0.054, untwisted NACA 0012, shafts 1.03 D apart (no overlap), "
             "ΩR = 152.4 m/s, C_T = 0.0034 per rotor, f = 0.372 m².\nEach rotor trimmed to its thrust with zero "
             "hub moments; shaft tilt balances fuselage drag. Markers digitised from the report (±0.5 hp). "
             f"Rear-rotor error {mape_low:.1f} % (mean |error|, μ ≤ 0.2).",
             ha="center", fontsize=8, color="#333333")
    fig.tight_layout()
    plot_path = os.path.join(out_dir, "tandem_validation_dingeldein.png")
    fig.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {plot_path}")


if __name__ == "__main__":
    run_tandem_validation()
