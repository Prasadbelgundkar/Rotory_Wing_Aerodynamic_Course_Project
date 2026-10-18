"""
plot_fvw_standalone.py -- figures of the standalone (two-way) free-vortex wake runs used in the deck.

Reads the cached runs in src/data/fvw/ (written by src/tandem_fvw.py) and writes to outputs/mp/:
  ch47_convergence.png         Validation 1/3 (code verification)
  dingeldein_validation.png    Validation 2/3 (standalone FVW vs NACA TN-3236 Fig. 6)
  ch47_aft_inflow.png          Assessment 2/4 (why the aft rotor pays)
  ch47_power.png               Assessment 3/4 (tool vs standalone two-way free wake)
  plus wake side views, dingeldein_power.png, dingeldein_aft_inflow.png and *_table.json

The CH-47 standalone cross-check in the deck uses mu = 0.10 and 0.20 only (the extra CH-47 runs at
0.05/0.15/0.25 feed the integrated tool's interference maps), so those are the ones plotted here.
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
import tandem_fvw as fvw  # noqa: E402

DATA = os.path.join(ROOT, "src", "data")
RES = os.path.join(DATA, "fvw")                 # cached FVW runs (input)
OUT = os.path.join(ROOT, "outputs", "mp")       # figures and tables (output)
DECK_MUS = {"ch47": (0.10, 0.20)}               # standalone cross-check cases shown in the deck
C_FWD, C_AFT, C_ISO = "#2a78d6", "#eb6834", "#52514e"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e4e3df", "grid.linewidth": 0.6})


def load(cfg, mu, kind):
    with open(os.path.join(RES, f"{cfg}_mu{mu:.2f}_{kind}.json")) as f:
        return json.load(f)


def summary(cfg):
    with open(os.path.join(RES, f"{cfg}_summary.json")) as f:
        S = json.load(f)
    keep = DECK_MUS.get(cfg)
    return S if keep is None else [s for s in S if any(abs(s["mu"] - m) < 1e-6 for m in keep)]


def pick(S, mu, config, rotor):
    for s in S:
        if abs(s["mu"] - mu) < 1e-6 and s["config"] == config and s["rotor"] == rotor:
            return s
    return None


def fig_power(cfg, title, fname):
    fvw.set_config(cfg)
    S = summary(cfg)
    mus = sorted({s["mu"] for s in S if s["config"] == "tandem"})
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8))
    w = 0.26
    x = np.arange(len(mus))
    for ax, key, lab in ((axes[0], "P", "Shaft power per rotor [kW]"),
                         (axes[1], "P_induced", "Induced power per rotor [kW]")):
        iso = [pick(S, m, "single", "fwd")[key] / 1e3 for m in mus]
        fwd = [pick(S, m, "tandem", "fwd")[key] / 1e3 for m in mus]
        aft = [pick(S, m, "tandem", "aft")[key] / 1e3 for m in mus]
        for off, vals, c, l in ((-w, iso, C_ISO, "Isolated rotor"), (0, fwd, C_FWD, "Tandem: forward"),
                                (w, aft, C_AFT, "Tandem: aft")):
            b = ax.bar(x + off, vals, w * 0.92, color=c, label=l)
            ax.bar_label(b, fmt="%.0f", fontsize=7, padding=2)
        ax.set_xticks(x, [f"μ = {m:.2f}" for m in mus])
        ax.set_ylabel(lab)
        ax.grid(axis="x", visible=False)
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle(title, fontsize=10)
    fig.text(0.5, -0.04, "Free-vortex wake, each rotor trimmed to its thrust (W/2) with zero hub moments. "
             "Induced = shaft − profile − propulsive (T·V·sin tilt).", ha="center", fontsize=7.5, color="#52514e")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_aft_inflow(cfg, mus, fname):
    fvw.set_config(cfg)
    fig, axes = plt.subplots(2, len(mus), figsize=(4.2 * len(mus), 7.6),
                             subplot_kw=dict(projection="polar"), squeeze=False)
    for j, mu in enumerate(mus):
        res = load(cfg, mu, "tandem")
        g = res["aft_grid"]
        r = np.array(g["r"]) / fvw.R
        p = np.radians(g["psi_deg"])
        v = np.array(g["v_down"])
        vc = fvw.coleman_skewed_on_aft(mu, res["lam_glauert"], np.array(g["r"]), g["psi_deg"])
        vmax = max(v.max(), vc.max())
        vmin = min(v.min(), 0)
        levels = np.linspace(vmin, vmax, 15)
        # psi here is measured from +x (aft); plot with the forward direction up
        P = np.append(p, p[0] + 2 * np.pi)
        for i, (field, lab) in enumerate(((v, "Free-vortex wake"), (vc, "Coleman skewed cylinder (overlap only)"))):
            ax = axes[i, j]
            F = np.vstack([field, field[:1]])
            cs = ax.contourf(P, r, F.T, levels=levels, cmap="Blues")
            ax.set_theta_zero_location("S")
            ax.set_yticklabels([])
            ax.set_xticklabels([])
            ax.grid(False)
            area = r[None, :] * np.ones_like(field)
            mean = (field * area).sum() / area.sum()
            ax.set_title(f"μ = {mu:.2f}: {lab}\narea-mean Δv = {mean:.2f} m/s", fontsize=8.5)
            ax.annotate("front", xy=(np.pi, 1.08), ha="center", fontsize=7, annotation_clip=False)
            fig.colorbar(cs, ax=ax, shrink=0.7, label="downwash from forward rotor [m/s]")
    fig.suptitle("Forward-rotor induced downwash over the aft rotor disk (revolution-averaged)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_wake(cfg, mu, fname):
    fvw.set_config(cfg)
    res = load(cfg, mu, "tandem")
    fig, ax = plt.subplots(figsize=(9, 3.4))
    for name, c in (("fwd", C_FWD), ("aft", C_AFT)):
        tip = np.array(res["tip_wake"][name])  # (NB, n_age+1, 3)
        for b in range(tip.shape[0]):
            ax.plot(tip[b, :, 0] / fvw.R, tip[b, :, 2] / fvw.R, color=c, lw=0.8,
                    label=f"{'Forward' if name == 'fwd' else 'Aft'} rotor tip vortices" if b == 0 else None)
    tilt = np.radians(res["tilt_deg"])
    for xc, zc, c in ((0, 0, C_FWD), (fvw.D_SEP / fvw.R, fvw.STAGGER / fvw.R, C_AFT)):
        ax.plot([xc - np.cos(tilt), xc + np.cos(tilt)], [zc + np.sin(tilt), zc - np.sin(tilt)], color=c, lw=3,
                solid_capstyle="round")
    ax.set_aspect("equal")
    ax.set_xlabel("x / R  (free stream from left to right)")
    ax.set_ylabel("z / R")
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    ax.set_title(f"Free-vortex wake side view, μ = {mu:.2f} (thick lines = rotor disks)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_convergence(cfg, mu, fname):
    res = load(cfg, mu, "tandem")
    fig, ax = plt.subplots(1, 2, figsize=(8, 3))
    for name, c in (("fwd", C_FWD), ("aft", C_AFT)):
        h = res["hist"][name]
        rv = [e["rev"] for e in h]
        ax[0].plot(rv, [e["T"] / 1e3 for e in h], color=c, lw=2, label=name)
        ax[1].plot(rv, [e["P"] / 1e3 for e in h], color=c, lw=2, label=name)
    ax[0].axhline(res["T_target"] / 1e3, color="#898781", lw=1, ls="--")
    ax[0].set_ylabel("Thrust [kN]")
    ax[1].set_ylabel("Shaft power [kW]")
    for a in ax:
        a.set_xlabel("Rotor revolution")
    ax[0].legend(frameon=False)
    fig.suptitle(f"Trim and wake convergence, {cfg}, μ = {mu:.2f}", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=200, bbox_inches="tight")
    plt.close(fig)


def table_rows(cfg):
    with open(os.path.join(OUT, f"{cfg}_table.json")) as fh:
        return json.load(fh)


def table(cfg):
    fvw.set_config(cfg)
    S = summary(cfg)
    rows = []
    for mu in sorted({s["mu"] for s in S if s["config"] == "tandem"}):
        iso = pick(S, mu, "single", "fwd")
        f = pick(S, mu, "tandem", "fwd")
        a = pick(S, mu, "tandem", "aft")
        res = load(cfg, mu, "tandem")
        g = res["aft_grid"]
        v = np.array(g["v_down"])
        r = np.array(g["r"])
        area = r[None, :] * np.ones_like(v)
        dv = (v * area).sum() / area.sum()
        vc = fvw.coleman_skewed_on_aft(mu, res["lam_glauert"], r, g["psi_deg"])
        dvc = (vc * area).sum() / area.sum()
        vi = res["lam_glauert"] * fvw.V_TIP
        rows.append(dict(mu=mu, V=res["V"], kappa_iso=(iso["P_induced"] / iso["P_glauert_induced"]),
                         P_iso=iso["P"] / 1e3, P_fwd=f["P"] / 1e3, P_aft=a["P"] / 1e3,
                         Pi_iso=iso["P_induced"] / 1e3, Pi_fwd=f["P_induced"] / 1e3, Pi_aft=a["P_induced"] / 1e3,
                         dP_tandem_pct=100 * (f["P"] + a["P"] - 2 * iso["P"]) / (2 * iso["P"]),
                         dP_aft_pct=100 * (a["P"] - iso["P"]) / iso["P"],
                         dv_fvw=dv, dv_coleman=dvc, v_i=vi,
                         dP_aft_from_dv=a["T"] * dv / 1e3, dP_aft_coleman=a["T"] * dvc / 1e3,
                         dP_aft_full_2vi=a["T"] * 2 * vi / 1e3))
    with open(os.path.join(OUT, f"{cfg}_table.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    for row in rows:
        print({k: round(v, 3) for k, v in row.items()})
    return rows


def fig_dingeldein(fname="dingeldein_validation.png"):
    """free-wake results against digitised TN-3236 Fig. 6"""
    import csv
    meas = {}
    with open(os.path.join(DATA, "dingeldein_tn3236_fig6.csv")) as fh:
        for row in csv.DictReader(l for l in fh if not l.startswith("#")):
            meas.setdefault(row["series"], []).append((float(row["mu"]), float(row["power_hp"])))
    S = summary("dingeldein")
    mus = sorted({s["mu"] for s in S if s["config"] == "tandem" and pick(S, s["mu"], "single", "fwd")})
    hp = 1 / 745.7
    iso = np.array([pick(S, m, "single", "fwd")["P"] * hp for m in mus])
    iso_e = np.array([pick(S, m, "single", "fwd")["P_std"] * hp for m in mus])
    fwd = np.array([pick(S, m, "tandem", "fwd")["P"] * hp for m in mus])
    fwd_e = np.array([pick(S, m, "tandem", "fwd")["P_std"] * hp for m in mus])
    aft = np.array([pick(S, m, "tandem", "aft")["P"] * hp for m in mus])
    aft_e = np.array([pick(S, m, "tandem", "aft")["P_std"] * hp for m in mus])
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
    spec = (("single_rotor", "Single rotor", C_ISO, "o", iso, iso_e),
            ("front_rotor", "Front rotor", C_FWD, "s", fwd, fwd_e),
            ("rear_rotor", "Rear rotor", C_AFT, "^", aft, aft_e))
    for key, lab, c, mk, model, err in spec:
        m = np.array(meas[key])
        ax[0].plot(m[:, 0], m[:, 1], mk, color=c, mfc="none", ms=8, mew=1.5, label=f"{lab}, measured")
        ax[0].errorbar(mus, model, yerr=err, color=c, lw=2, capsize=3, label=f"{lab}, free-vortex wake")
    ax[0].set_xlabel("Tip-speed ratio μ")
    ax[0].set_ylabel("Rotor power [hp]")
    ax[0].set_xlim(0, 0.32)
    ax[0].set_ylim(0, 30)
    ax[0].legend(frameon=False, fontsize=7, ncol=2, loc="lower center")
    ax[0].set_title("Individual rotors", fontsize=9)
    m = np.array(meas["tandem_total"])
    ax[1].plot(m[:, 0], m[:, 1], "D", color="#0b0b0b", mfc="none", ms=8, mew=1.5, label="Tandem total, measured")
    ax[1].errorbar(mus, fwd + aft, yerr=np.hypot(fwd_e, aft_e), color="#0b0b0b", lw=2, capsize=3,
                   label="Tandem total, free-vortex wake")
    ax[1].plot(mus, 2 * iso, color=C_ISO, lw=1.5, ls="--", label="2 × isolated rotor (no interference)")
    ax[1].set_xlabel("Tip-speed ratio μ")
    ax[1].set_ylabel("Rotor power [hp]")
    ax[1].set_xlim(0, 0.32)
    ax[1].set_ylim(0, 50)
    ax[1].legend(frameon=False, fontsize=7, loc="lower center")
    ax[1].set_title("Tandem total", fontsize=9)
    # interference increment: rear rotor minus single rotor (the phenomenon itself)
    ms = dict(meas["single_rotor"])
    inc = [(m_, p_ - ms[min(ms, key=lambda k: abs(k - m_))]) for m_, p_ in meas["rear_rotor"]
           if min(abs(k - m_) for k in ms) < 0.01]
    inc = np.array(inc)
    ax[2].plot(inc[:, 0], inc[:, 1], "^", color=C_AFT, mfc="none", ms=8, mew=1.5,
               label="Measured: rear − single")
    ax[2].errorbar(mus, aft - iso, yerr=np.hypot(aft_e, iso_e), color=C_AFT, lw=2, capsize=3,
                   label="Free-vortex wake: aft − isolated")
    tab = {round(r_["mu"], 3): r_ for r_ in table_rows("dingeldein")}
    full = [tab[round(m_, 3)]["dP_aft_full_2vi"] * 1e3 * hp for m_ in mus]
    ax[2].plot(mus, full, color=C_ISO, lw=1.5, ls="--", label="Momentum, full 2v_i downwash (TN-3236 method)")
    ax[2].plot(mus, np.zeros(len(mus)), color=C_FWD, lw=1.5, ls=":", label="Coleman overlap model (no overlap → 0)")
    ax[2].set_xlabel("Tip-speed ratio μ")
    ax[2].set_ylabel("Extra power on the rear rotor [hp]")
    ax[2].set_xlim(0, 0.32)
    ax[2].set_ylim(-1, 14)
    ax[2].legend(frameon=False, fontsize=7, loc="upper right")
    ax[2].set_title("Interference increment", fontsize=9)
    fig.suptitle("Validation: Dingeldein NACA TN-3236 Fig. 6 (C_T = 0.0034, ΩR = 500 ft/s, shafts 1.03D apart)",
                 fontsize=10)
    fig.text(0.5, -0.03, "Markers digitised from the report; error bars = revolution-to-revolution std of the "
             "free-wake power over the last 4 revolutions.", ha="center", fontsize=7.5, color="#52514e")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cfgs = sys.argv[1:] or ["ch47", "dingeldein"]
    for cfg in cfgs:
        if not os.path.exists(os.path.join(RES, f"{cfg}_summary.json")):
            continue
        S = summary(cfg)
        mus = sorted({s["mu"] for s in S if s["config"] == "tandem"})
        mus = [m for m in mus if pick(S, m, "single", "fwd") and pick(S, m, "tandem", "aft")]
        if not mus:
            continue
        label = {"ch47": "CH-47 class baseline", "dingeldein": "Dingeldein TN-3236 tandem model"}[cfg]
        fig_power(cfg, f"{label}: isolated vs tandem rotor power", f"{cfg}_power.png")
        fig_aft_inflow(cfg, mus, f"{cfg}_aft_inflow.png")
        for mu in mus:
            fig_wake(cfg, mu, f"{cfg}_wake_mu{mu:.2f}.png")
        fig_convergence(cfg, mus[-1], f"{cfg}_convergence.png")
        table(cfg)
        if cfg == "dingeldein":
            fig_dingeldein()
