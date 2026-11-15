"""
Milestone 3 -- Section 3: final aircraft performance summary (frozen design).

Uses the existing Milestone 2 6-DOF trim (src/m2/trim_6dof.py) at a small set
of operating points; nothing is re-validated or re-swept (Milestone 1 / 2
results are referenced). Only the quantities affected by the final design
(refined blade, 2 x CT7-8A, MCP rating in airplane mode) are recomputed.

    python scripts/m3/performance_summary.py

Outputs (outputs/m3/):
  m3_3p1_operating_points.md       Section 3.1 hover and airplane-mode operating points
  m3_3p1_specific_range.png        Section 3.1 fuel per km vs airspeed and RPM at the cruise altitude
  m3_3p3_operating_limits.png      Section 3.3 max hover mass vs altitude, max level speed vs altitude
  m3_3p3_limits_table.md           Section 3.3 operating limits of the final design
  m3_3p2_conversion_summary.md     Section 3.2 corridor (from the Milestone 2 map) per nacelle angle
  m3_3_performance.json            headline numbers (used by make_m3_tables.py)
"""
import json
import os

import numpy as np

from _common import CFG, plt, save_figure, write_text, md_table, OUT_DIR, M2_DIR, MODEL_NOTE, DEFAULT_MISSION
from m2.trim_6dof import trim_6dof, make_condition, diagnose

G = CFG.G
A_DISK = np.pi * CFG.ROTOR.radius_m ** 2
MCP = CFG.MCP_FRACTION
SFC = CFG.ENGINE_SFC_KG_PER_J
with open(DEFAULT_MISSION, encoding='utf-8') as f:
    MISSION = json.load(f)
H_PAD, DT_PAD = MISSION["atmosphere"]["pad_altitude_m"], MISSION["atmosphere"]["dISA_K"]
H_CR, V_CR, RPM_CR = (MISSION["cruise"][k] for k in ("altitude_m", "speed_mps", "rpm"))


def trim(V, nacelle, rpm, h, dT=0.0, mass=CFG.GROSS_MASS_KG, rating=1.0):
    c = make_condition(V, nacelle, rpm=rpm, altitude_m=h, dISA_K=dT)
    c.P_avail_per_rotor_W *= rating
    return trim_6dof(CFG.get_default_aircraft(mass), CFG.ROTOR, CFG.airfoil_provider, c), c


M_SEARCH_MAX = 11000.0     # upper bound of the hover-mass search [kg]


def short(why):
    """Compact limit label for the tables."""
    return why.replace("trimmed but limited by ", "").replace("insufficient control authority: ", "")


def bisect(f, lo, hi, tol, n_max=12):
    """Largest x in [lo, hi] with f(x) True (f(lo) True assumed); None if f(lo) is False."""
    if not f(lo):
        return None
    if f(hi):
        return hi
    for _ in range(n_max):
        if hi - lo <= tol:
            break
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) else (lo, mid)
    return lo


# ---------------------------------------------------------------------------
def hover_points():
    rows, out = [], []
    for label, h, dT in (("Sea level ISA", 0.0, 0.0), (f"Design pads {H_PAD:.0f} m ISA+{DT_PAD:.0f}", H_PAD, DT_PAD),
                         ("2000 m ISA (M2 reference)", 2000.0, 0.0)):
        tr, c = trim(0.0, 90.0, CFG.HOVER_RPM, h, dT)
        T = tr.rotor_lift_N / 2
        P1 = tr.P_req_W / 2
        FM = T * np.sqrt(T / (2 * c.rho * A_DISK)) / P1
        d = dict(case=label, h=h, dT=dT, rho=c.rho, rpm=CFG.HOVER_RPM, coll=tr.collective_deg, T_kN=T / 1e3,
                 P_kW=tr.P_req_W / 1e3, Pav_kW=tr.P_avail_W / 1e3, margin=100 * tr.power_margin_frac, FM=FM,
                 PL=CFG.GROSS_MASS_KG / (tr.P_req_W / 1e3), tipM=tr.adv_tip_mach, stall=100 * tr.stalled_fraction,
                 sm=tr.stall_margin_deg, fuel_kg_h=SFC * tr.P_req_W * 3600, feasible=tr.feasible)
        out.append(d)
        rows.append([label, f"{c.rho:.3f}", f"{CFG.HOVER_RPM:.0f}", f"{d['coll']:.1f}", f"{d['T_kN']:.1f}",
                     f"{d['P_kW']:.0f} / {d['Pav_kW']:.0f}", f"{d['margin']:.0f} %", f"{FM:.3f}",
                     f"{d['PL']:.2f}", f"{d['tipM']:.3f}", f"{d['stall']:.1f} %", f"{d['fuel_kg_h']:.0f}"])
    return out, md_table(["Hover (OGE, MTOW 7200 kg)", "rho [kg/m3]", "RPM", "Collective [deg]",
                          "Thrust / rotor [kN]", "P_req / P_avail (TO) [kW]", "Power margin", "Figure of merit",
                          "Power loading [kg/kW]", "Tip Mach", "Stalled area", "Fuel flow [kg/h]"], rows)


def cruise_points():
    pts = [("Long-range cruise (design mission)", H_CR, DT_PAD, V_CR, RPM_CR),
           ("Cruise, higher RPM", H_CR, DT_PAD, V_CR + 10, CFG.AIRPLANE_RPM),
           ("High-speed cruise", 3000.0, DT_PAD, 100.0, CFG.AIRPLANE_RPM),
           ("Dash", 3000.0, DT_PAD, 110.0, CFG.DASH_RPM)]
    rows, out = [], []
    for label, h, dT, V, rpm in pts:
        tr, c = trim(V, 0.0, rpm, h, dT, rating=MCP)
        T = tr.rotor_propulsive_N
        eta = T * V / tr.P_req_W
        LDe = CFG.GROSS_MASS_KG * G * V / tr.P_req_W
        J = V / (CFG.rpm_to_omega(rpm) * 2 * CFG.ROTOR.radius_m / (2 * np.pi))
        d = dict(case=label, h=h, dT=dT, V=V, rpm=rpm, coll=tr.collective_deg, T_kN=T / 1e3,
                 wing=100 * tr.wing_lift_N / (CFG.GROSS_MASS_KG * G), P_kW=tr.P_req_W / 1e3,
                 Pav_kW=tr.P_avail_W / 1e3, eta=eta, LDe=LDe, J=J, alpha_w=tr.aero.alpha_wing_deg,
                 kg_km=SFC * tr.P_req_W / V * 1e3, tipM=tr.adv_tip_mach, feasible=tr.feasible, diag=diagnose(tr))
        out.append(d)
        rows.append([label, f"{h:.0f} m ISA+{dT:.0f}", f"{V:.0f} ({V * 3.6:.0f} km/h)", f"{rpm:.0f}", f"{J:.2f}",
                     f"{d['coll']:.1f}", f"{d['T_kN']:.2f}", f"{d['wing']:.0f} %", f"{d['alpha_w']:.1f}",
                     f"{d['P_kW']:.0f} / {d['Pav_kW']:.0f}", f"{eta:.3f}", f"{LDe:.1f}", f"{d['kg_km']:.3f}",
                     f"{d['tipM']:.3f}", "yes" if tr.feasible else d['diag']])
    return out, md_table(["Airplane mode (7200 kg, nacelle 0)", "Altitude", "TAS [m/s]", "RPM",
                          "Advance ratio J = V/(nD)", "Collective [deg]", "Total rotor thrust [kN]", "Wing lift share",
                          "Wing alpha [deg]", "P_req / P_avail (MCP) [kW]", "Propulsive eff. TV/P",
                          "Effective L/D = WV/P", "Fuel [kg/km, still air]", "Helical tip Mach", "Feasible"], rows)


def specific_range(mass=6800.0):
    Vs = np.arange(55.0, 116.0, 5.0)
    res = {}
    for rpm in (CFG.LONG_RANGE_RPM, 300.0, CFG.AIRPLANE_RPM):
        kgkm, ok, why = [], [], []
        for V in Vs:
            tr, _ = trim(V, 0.0, rpm, H_CR, DT_PAD, mass=mass, rating=MCP)
            kgkm.append(SFC * tr.P_req_W / V * 1e3 if np.isfinite(tr.P_req_W) else np.nan)
            ok.append(tr.feasible)
            why.append(diagnose(tr))
        res[rpm] = (np.array(kgkm), np.array(ok), why)
    fig, ax = plt.subplots(figsize=(10, 6))
    best = {}
    feas_vals = np.concatenate([k[ok] for k, ok, _ in res.values()])
    y_bot = 0.9 * np.nanmin(feas_vals)
    for j, ((rpm, (k, ok, why)), col) in enumerate(zip(res.items(), ('tab:blue', 'tab:orange', 'tab:green'))):
        # infeasible trims (collective saturation, wing stall, power) carry no meaningful power: not plotted,
        # only marked along the bottom of the axes
        ax.plot(Vs[ok], k[ok], 'o-', color=col, lw=2, label=f"{rpm:.0f} RPM (feasible trim)")
        if np.any(~ok):
            ax.plot(Vs[~ok], np.full((~ok).sum(), y_bot * (1 + 0.012 * j)), 'x', color=col, ms=9, mew=2,
                    label=f"{rpm:.0f} RPM: no feasible trim")
        if np.any(ok):
            i = int(np.nanargmin(np.where(ok, k, np.nan)))
            best[rpm] = dict(V=float(Vs[i]), kg_km=float(k[i]),
                             V_max_feasible=float(Vs[ok].max()), limit_above=why[min(len(why) - 1, int(np.where(ok)[0].max()) + 1)])
    ax.set_xlabel("True airspeed [m/s]")
    ax.set_ylabel("Fuel per km, still air [kg/km]")
    ax.set_title(f"Section 3.1 -- Airplane-mode fuel per km at {H_CR:.0f} m ISA+{DT_PAD:.0f}, mid-cruise mass "
                 f"{mass:.0f} kg, MCP rating", fontsize=10.5)
    ax.legend()
    save_figure(fig, "m3_3p1_specific_range", "3.1",
                f"Fuel burned per km (SFC {SFC * 3.6e9:.0f} g/kWh x trimmed power / TAS, no wind) vs true airspeed in "
                f"airplane mode at {H_CR:.0f} m ISA+{DT_PAD:.0f}, {mass:.0f} kg (mid-cruise of the design mission), "
                f"for 250 / 300 / 350 RPM; crosses along the bottom = speeds with no feasible trim (collective saturation at 65 deg, wing stall at 55 m/s, or power at 115 m/s / 350 RPM). "
                f"{MODEL_NOTE}.")
    return best


def hover_ceiling():
    alts = np.arange(0.0, 5001.0, 1000.0)
    out = {}
    for dT in (0.0, 15.0):
        mmax, lim = [], []
        for h in alts:
            m = bisect(lambda m: trim(0.0, 90.0, CFG.HOVER_RPM, h, dT, mass=m)[0].feasible, 5000.0, M_SEARCH_MAX, 25.0)
            mmax.append(np.nan if m is None else m)
            tr, _ = trim(0.0, 90.0, CFG.HOVER_RPM, h, dT, mass=(m or 5000.0) + 30.0)
            lim.append(diagnose(tr))
        mmax = np.array(mmax)
        # ceiling at MTOW: where m_max crosses 7200 kg
        ceil = np.nan
        if np.nanmax(mmax) >= CFG.GROSS_MASS_KG >= np.nanmin(mmax):
            ceil = float(np.interp(CFG.GROSS_MASS_KG, mmax[::-1], alts[::-1]))
        elif np.nanmin(mmax) > CFG.GROSS_MASS_KG:
            ceil = float('inf')
        out[dT] = dict(alt=alts.tolist(), m_max=mmax.tolist(), limit=lim, ceiling_m=ceil)
    return out


def max_speed():
    alts = [0.0, H_PAD, 3000.0, H_CR]
    out = {}
    for name, rating in (("MCP", MCP), ("take-off rating", 1.0)):
        Vm, lim = [], []
        for h in alts:
            dT = 0.0 if h == 0.0 else DT_PAD
            V = bisect(lambda V: trim(V, 0.0, CFG.DASH_RPM, h, dT, rating=rating)[0].feasible, 80.0, 170.0, 1.0)
            Vm.append(np.nan if V is None else V)
            tr, _ = trim((V or 80.0) + 1.0, 0.0, CFG.DASH_RPM, h, dT, rating=rating)
            lim.append(diagnose(tr))
        out[name] = dict(alt=alts, V=Vm, limit=lim)
    return out


def plot_limits(hc, vm):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.5))
    for dT, st in ((0.0, 'b-o'), (15.0, 'r-s')):
        d = hc[dT]
        a1.plot(np.array(d['m_max']), d['alt'], st, lw=2, label=f"ISA{'+%g' % dT if dT else ''}: max hover mass "
                f"(ceiling at MTOW {d['ceiling_m']:.0f} m)" if np.isfinite(d['ceiling_m']) else f"ISA+{dT:g}")
    a1.axvline(CFG.GROSS_MASS_KG, color='k', ls='--', lw=1, label='MTOW 7200 kg')
    a1.plot(CFG.GROSS_MASS_KG, H_PAD, 'k*', ms=14, label=f"requirement: hover OGE at MTOW, {H_PAD:.0f} m ISA+{DT_PAD:.0f}")
    a1.set_xlabel("Maximum OGE hover mass [kg] (TO rating, 5 % power margin, <= 5 % stalled area)")
    a1.set_ylabel("Pressure altitude [m]")
    a1.legend(fontsize=8)
    a1.set_title("Hover envelope (final design)", fontsize=10.5)
    for (name, d), st in zip(vm.items(), ('g-o', 'm-s')):
        a2.plot(d['V'], d['alt'], st, lw=2, label=f"max level speed, {name}, {CFG.DASH_RPM:.0f} RPM")
    a2.axvline(CFG.M1.MAX_SPEED_TARGET_MPS, color='k', ls='--', lw=1, label='450 km/h target (125 m/s)')
    a2.set_xlabel("True airspeed [m/s]")
    a2.set_ylabel("Pressure altitude [m] (ISA at 0 m, ISA+15 above)")
    a2.legend(fontsize=8)
    a2.set_title("Airplane-mode maximum level speed at MTOW", fontsize=10.5)
    fig.suptitle("Section 3.3 -- Final operating limits", fontsize=12)
    fig.tight_layout()
    save_figure(fig, "m3_3p3_operating_limits", "3.3",
                "Left: maximum out-of-ground-effect hover mass vs pressure altitude for ISA and ISA+15 (550 RPM, "
                "take-off rating, feasible 6-DOF trim with >= 5 % power margin and <= 5 % stalled rotor area); the "
                "crossing with MTOW gives the hover ceiling. Right: maximum level airplane-mode speed at 7200 kg, "
                f"{CFG.DASH_RPM:.0f} RPM, for max-continuous and take-off ratings (sea level ISA, ISA+15 above). "
                f"{MODEL_NOTE}.")


def conversion_summary():
    cache = os.path.join(M2_DIR, "corridor_grid.npz")
    if not os.path.exists(cache):
        return None, "Milestone 2 corridor cache not found."
    from m2.conversion_corridor import CATEGORIES
    g = dict(np.load(cache, allow_pickle=True))
    cat = g["category"].astype(int)
    feas = cat == CATEGORIES.index('feasible')
    V, N = np.asarray(g["V"], float), np.asarray(g["nacelle"], float)
    rows, d = [], []
    for j, n in enumerate(N):
        v = V[feas[j]]
        lo, hi = (float(v.min()), float(v.max())) if v.size else (np.nan, np.nan)
        below = [CATEGORIES[c] for c in cat[j][V < lo]] if v.size else []
        above = [CATEGORIES[c] for c in cat[j][V > hi]] if v.size else []
        gaps = [float(x) for x in V[(V > lo) & (V < hi) & ~feas[j]]] if v.size else []
        rows.append([f"{n:.1f}", f"{lo:.0f}" if v.size else "-", f"{hi:.0f}" if v.size else "-",
                     ", ".join(sorted(set(below[-1:]))) or "-", ", ".join(sorted(set(above[:1]))) or "-",
                     ", ".join(f"{x:.0f}" for x in gaps) or "-"])
        d.append(dict(nacelle=float(n), V_min=lo, V_max=hi, gaps=gaps))
    path = ", ".join(f"({v:.0f}, {n:.0f})" for v, n in CFG.CONVERSION_PATH)
    rpath = ", ".join(f"({v:.0f}, {n:.0f})" for v, n in CFG.RECONVERSION_PATH)
    txt = ["# Section 3.2 -- conversion summary (Milestone 2 corridor map, reused)", "",
           f"Map: {CFG.REFERENCE_ALTITUDE_M:.0f} m ISA (rho = 1.007 kg/m3, the same density as the 1500 m ISA+15 "
           "design pads to within 0.3 %), 7200 kg, 550 RPM, steady level flight, 6-DOF trim at every point. "
           "Not recomputed: the rotor, airframe and mass of the final design are those of Milestone 2.", "",
           md_table(["Nacelle [deg]", "Min feasible V [m/s]", "Max feasible V [m/s]", "Limit just below V_min",
                     "Limit just above V_max", "Infeasible speeds inside the band"], rows), "",
           f"Recommended conversion path (V [m/s], nacelle [deg]): {path}.",
           f"Recommended reconversion path: {rpath} (nacelles tilted back earlier, slightly beyond vertical at "
           "25-35 m/s, so the rotors decelerate the aircraft instead of a nose-up attitude that stalls the wing).", ""]
    return d, "\n".join(txt)


def main():
    perf = {}
    print("hover operating points ...")
    hov, t_h = hover_points()
    print("airplane operating points ...")
    cru, t_c = cruise_points()
    print("specific range ...")
    sr = specific_range()
    print("hover envelope ...")
    hc = hover_ceiling()
    print("max speed ...")
    vm = max_speed()
    plot_limits(hc, vm)
    conv, t_conv = conversion_summary()
    write_text("m3_3p2_conversion_summary.md", t_conv + "\n")

    best = sr.get(CFG.LONG_RANGE_RPM, {})
    txt = ["# Section 3.1 -- hover and airplane-mode operating points (final design)", "",
           f"6-DOF trim of the complete aircraft; {MODEL_NOTE}. Fuel flow with SFC {SFC * 3.6e9:.0f} g/kWh. "
           f"Power available: take-off rating in hover, max-continuous ({100 * MCP:.0f} %) in airplane mode; "
           f"drivetrain efficiency {CFG.M1.DRIVETRAIN_EFFICIENCY:.2f} and density lapse included.", "", t_h, "", t_c, "",
           "Best-range (minimum fuel per km, still air) speed at the cruise altitude, mid-cruise mass 6800 kg:", ""]
    txt += [f"* {rpm:.0f} RPM: {b['V']:.0f} m/s, {b['kg_km']:.3f} kg/km; highest feasible speed {b['V_max_feasible']:.0f} m/s "
            f"(above: {short(b['limit_above'])})" for rpm, b in sr.items()]
    write_text("m3_3p1_operating_points.md", "\n".join(txt) + "\n")

    hp = [h for h in hov if h['h'] == H_PAD][0]
    sl = hov[0]
    lr = cru[0]
    i_pad = hc[15.0]['alt'].index(min(hc[15.0]['alt'], key=lambda a: abs(a - H_PAD)))
    m_pad = float(np.interp(H_PAD, hc[15.0]['alt'], hc[15.0]['m_max']))
    rows = [
        ["Max OGE hover mass, sea level ISA",
         f"{hc[0.0]['m_max'][0]:.0f} kg" if hc[0.0]['m_max'][0] < M_SEARCH_MAX - 1 else
         f"> {M_SEARCH_MAX:.0f} kg (search limit)", short(hc[0.0]['limit'][0]) if hc[0.0]['m_max'][0] <
         M_SEARCH_MAX - 1 else "not reached; structural MTOW 7200 kg governs"],
        [f"Max OGE hover mass, {H_PAD:.0f} m ISA+{DT_PAD:.0f} (design pads)", f"{m_pad:.0f} kg "
         f"({m_pad - CFG.GROSS_MASS_KG:+.0f} kg vs MTOW)", short(hc[15.0]['limit'][i_pad])],
        ["OGE hover ceiling at MTOW, ISA", f"{hc[0.0]['ceiling_m']:.0f} m" if np.isfinite(hc[0.0]['ceiling_m'])
         else "> 5000 m", "power (5 % margin)"],
        ["OGE hover ceiling at MTOW, ISA+15", f"{hc[15.0]['ceiling_m']:.0f} m" if np.isfinite(hc[15.0]['ceiling_m'])
         else "> 5000 m", "power (5 % margin)"],
        [f"Hover power margin at MTOW, {H_PAD:.0f} m ISA+{DT_PAD:.0f}", f"{hp['margin']:.0f} % "
         f"({hp['P_kW']:.0f} of {hp['Pav_kW']:.0f} kW)", "TO rating"],
        ["Hover tip Mach / stalled area at MTOW, sea level", f"{sl['tipM']:.3f} / {sl['stall']:.1f} %",
         "limits 0.85 / 5 %"],
        [f"Best-range speed, {H_CR:.0f} m ISA+{DT_PAD:.0f}, {CFG.LONG_RANGE_RPM:.0f} RPM",
         f"{best.get('V', np.nan):.0f} m/s ({best.get('kg_km', np.nan):.3f} kg/km)", "minimum fuel per km"],
        [f"Practical long-range cruise (design mission)", f"{V_CR:.0f} m/s ({V_CR * 3.6:.0f} km/h) at {RPM_CR:.0f} RPM, "
         f"{lr['kg_km']:.3f} kg/km", f"collective {lr['coll']:.1f} of 65 deg"],
        [f"Max speed at {CFG.LONG_RANGE_RPM:.0f} RPM, {H_CR:.0f} m", f"{best.get('V_max_feasible', np.nan):.0f} m/s",
         short(best.get('limit_above', '-'))],
    ]
    for name, d in vm.items():
        for h, V, why in zip(d['alt'], d['V'], d['limit']):
            if h in (0.0, 3000.0, H_CR):
                rows.append([f"Max level speed, {name}, {h:.0f} m {'ISA' if h == 0 else 'ISA+%g' % DT_PAD}, "
                             f"{CFG.DASH_RPM:.0f} RPM", f"{V:.0f} m/s ({V * 3.6:.0f} km/h)", short(why)])
    if conv:
        narrow = min((c for c in conv if np.isfinite(c['V_min'])), key=lambda c: c['V_max'] - c['V_min'])
        rows.append(["Conversion corridor (M2 map)", f"narrowest at nacelle {narrow['nacelle']:.1f} deg: "
                     f"{narrow['V_min']:.0f}-{narrow['V_max']:.0f} m/s", "see m3_3p2_conversion_summary.md"])
    lim = CFG.ControlLimits()
    rows += [["Nacelle tilt rate", f"{lim.nacelle_rate_deg_s:.0f} deg/s", "actuator limit"],
             ["Rotor speed range", f"{lim.rpm[0]:.0f}-{lim.rpm[1]:.0f} RPM", "drive system"],
             ["Collective range", f"{lim.collective_deg[0]:.0f} to {lim.collective_deg[1]:.0f} deg", "pitch stops"]]
    write_text("m3_3p3_limits_table.md", "# Section 3.3 -- final operating limits\n\n"
               + md_table(["Limit", "Value", "Limited by"], rows) + "\n")
    perf.update(hover=hov, cruise=cru, specific_range={str(k): v for k, v in sr.items()}, hover_envelope=
                {str(k): v for k, v in hc.items()}, max_speed=vm, max_hover_mass_pad_kg=m_pad)
    with open(os.path.join(OUT_DIR, "m3_3_performance.json"), 'w', encoding='utf-8') as f:
        json.dump(perf, f, indent=1, default=float)


if __name__ == "__main__":
    main()
