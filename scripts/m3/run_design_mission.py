"""
Milestone 3 -- Section 4: end-to-end design mission (vertical take-off to
vertical landing) flown by Mission Planner v2 with the online 6-DOF trim at
every step.

    python scripts/m3/run_design_mission.py                       # default mission input
    python scripts/m3/run_design_mission.py --mission my.json     # any other mission file
    python scripts/m3/run_design_mission.py --replot              # re-plot from the saved log (no re-flight)

Input : inputs/m3_design_mission.json (segments, payload, atmosphere, wind,
        reserve, cruise condition, conversion schedule)
Outputs (outputs/m3/):
  m3_4p1_mission_definition.md          Section 4.1 table (as flown)
  m3_4p2_mission_time_history.png       Section 4.2 mission time histories, segments shaded
  m3_4p3_constraint_utilisation.png     Section 4.3 every limit as a fraction of its allowable
  m3_4p3_margins.md                     Section 4.3 peak utilisation and smallest margin per constraint
  m3_4p4_segment_summary.md             Section 4.4 power, fuel, loading per segment
  m3_4p4_power_breakdown.png            Section 4.4 power and rotor/wing lift share through the mission
  m3_4_paths_on_corridor.png            flown conversion / reconversion over the Milestone 2 corridor map
  m3_4_mission_log.csv                  full time history (every trimmed step)
  m3_4_mission_summary.json             headline numbers (used by make_m3_tables.py)
"""
import argparse
import csv
import json
import os
import time

import numpy as np

from _common import CFG, plt, save_figure, write_text, md_table, OUT_DIR, M2_DIR, DEFAULT_MISSION, MODEL_NOTE
import m3.design_mission as DM

LOG = os.path.join(OUT_DIR, "m3_4_mission_log.csv")
NONNUM = ('segment', 'kind', 'flags', 'trim_status')


def save_log(log):
    with open(LOG, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(log[0].keys()))
        w.writeheader()
        w.writerows(log)


def load_log():
    out = []
    with open(LOG, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            e = {}
            for k, v in r.items():
                if k in NONNUM:
                    e[k] = v
                elif k == 'feasible':
                    e[k] = v == 'True'
                else:
                    e[k] = float(v) if v not in ('', 'nan') else np.nan
            out.append(e)
    return out


def bounds_of(log):
    seg = [e['segment'] for e in log]
    b = [0] + [i for i in range(1, len(seg)) if seg[i] != seg[i - 1]] + [len(seg)]
    return [(seg[b[j]], b[j], b[j + 1] - 1) for j in range(len(b) - 1)]


def shade(axs, log, t, labels_on=None, first=0):
    """Segment shading on every axis; segment numbers (offset by `first`) on top of the given axes."""
    for j, (name, i0, i1) in enumerate(bounds_of(log), start=first):
        a, b = t[i0], t[min(i1 + 1, len(t) - 1)]
        for ax in axs:
            if j % 2 == 0:
                ax.axvspan(a, b, color='0.90', zorder=0, lw=0)
        for ax in (labels_on or []):
            ax.text(0.5 * (a + b), 1.01, str(j + 1), transform=ax.get_xaxis_transform(), ha='center',
                    va='bottom', fontsize=7.5, fontweight='bold')


def seg_legend(fig, log, y=0.005):
    txt = "   ".join(f"{j + 1}: {name}" for j, (name, _, _) in enumerate(bounds_of(log)))
    fig.text(0.5, y, "Segments - " + txt, ha='center', va='bottom', fontsize=8, wrap=True)


def time_axis(log):
    t = np.array([e['t_s'] for e in log]) / 60.0
    return t


def plot_time_history(log, viol, M):
    """Section 4.2: mission time histories. Time axis in minutes; the long
    cruise is shown in full (a broken axis would hide the slow mass decay)."""
    L = {k: np.array([e[k] for e in log], float) for k in log[0] if k not in NONNUM}
    t = time_axis(log)
    fig, axs = plt.subplots(4, 2, figsize=(16, 15), sharex='col')
    ax = axs[0, 0]
    ax.plot(t, L['altitude_m'], 'k-', lw=1.8)
    ax.axhline(M["atmosphere"]["pad_altitude_m"], color='0.4', lw=0.8, ls='--')
    ax.set_ylabel("Altitude (pressure, ISA+%g) [m]" % M["atmosphere"]["dISA_K"])
    ax = axs[0, 1]
    ax.plot(t, L['V_mps'], 'b-', lw=1.8, label='true airspeed')
    ax.plot(t, L['ground_speed_mps'], 'c--', lw=1.4, label='ground speed')
    ax.set_ylabel("Speed [m/s]")
    ax.legend(loc='center left')
    axd = ax.twinx()
    axd.plot(t, L['distance_km'], color='tab:gray', lw=1.6, label='cumulative ground distance')
    axd.set_ylabel("Ground distance [km]", color='tab:gray')
    axd.grid(False)
    axd.legend(loc='center right')
    ax = axs[1, 0]
    ax.plot(t, L['mass_kg'], 'k-', lw=1.8, label='gross mass')
    ax.set_ylabel("Gross mass [kg]")
    ax.legend(loc='lower left')
    axf = ax.twinx()
    axf.plot(t, L['fuel_kg'], color='tab:orange', lw=1.8, label='fuel remaining')
    axf.axhline(M["loading"]["reserve_fuel_kg"], color='tab:orange', ls='--', lw=1.0, label='reserve')
    axf.set_ylabel("Fuel [kg]", color='tab:orange')
    axf.set_ylim(0, M["loading"]["fuel_kg"] * 1.08)
    axf.grid(False)
    axf.legend(loc='upper right')
    ax = axs[1, 1]
    ax.plot(t, L['nacelle_deg'], color='tab:purple', lw=1.8, label='nacelle angle')
    ax.set_ylabel("Nacelle angle [deg] (90 = helicopter)", color='tab:purple')
    ax.set_ylim(-5, 100)
    axr = ax.twinx()
    axr.plot(t, L['rpm'], color='tab:brown', lw=1.6, label='rotor speed')
    axr.set_ylabel("Rotor speed [RPM]", color='tab:brown')
    axr.set_ylim(0, 620)
    axr.grid(False)
    ax = axs[2, 0]
    ax.plot(t, L['P_req_kW'], 'r-', lw=1.6, label='power required (both rotors)')
    ax.plot(t, L['P_avail_kW'], 'g-', lw=1.6, label='power available (TO rating / MCP)')
    ax.plot(t, 0.95 * L['P_avail_kW'], 'g:', lw=1.0, label='95 % of available (5 % margin limit)')
    ax.set_ylabel("Power [kW]")
    ax.legend(loc='upper right')
    ax = axs[2, 1]
    ax.plot(t, L['collective_deg'], 'tab:blue', lw=1.6, label='collective theta0')
    ax.plot(t, L['theta1c_deg'], 'tab:green', lw=1.4, label='long. cyclic theta1c')
    ax.plot(t, L['elevator_deg'], 'tab:olive', lw=1.4, label='elevator')
    ax.plot(t, L['theta_deg'], 'k', lw=1.2, label='pitch attitude')
    ax.axhline(CFG.ControlLimits().collective_deg[1], color='tab:blue', ls='--', lw=0.8)
    ax.set_ylabel("Controls / attitude [deg]")
    ax.legend(loc='center right', ncol=2)
    ax = axs[3, 0]
    ax.plot(t, L['rotor_stall_pct'], 'm-', lw=1.6, label='stalled loaded rotor area [%]')
    ax.axhline(100 * CFG.ControlLimits().max_stall_fraction, color='m', ls='--', lw=0.9, label='limit 5 %')
    ax.plot(t, 100 * L['tip_mach'], color='tab:red', lw=1.4, label='advancing-tip Mach x 100')
    ax.axhline(100 * CFG.ControlLimits().max_tip_mach, color='tab:red', ls='--', lw=0.9, label='tip-Mach limit 0.85')
    ax.set_ylabel("Rotor limits [%]")
    ax.set_ylim(0, 100)
    ax.legend(loc='center right', fontsize=7.5)
    ax = axs[3, 1]
    ax.plot(t, L['wing_alpha_margin_deg'], color='tab:cyan', lw=1.6, label='wing stall margin alpha_stall - |alpha_w|')
    ax.plot(t, L['power_margin_pct'], color='g', lw=1.4, label='power margin [%]')
    ax.axhline(5, color='g', ls='--', lw=0.8)
    ax.axhline(0, color='tab:cyan', ls='--', lw=0.8)
    ax.set_ylabel("Margins [deg] / [%]")
    ax.legend(loc='lower right', fontsize=7.5)
    for a in axs[-1]:
        a.set_xlabel("Mission time [min]")
    shade(list(axs.flat), log, t, labels_on=[axs[0, 0], axs[0, 1]])
    if viol:
        for a in axs.flat:
            for v in viol:
                a.axvline(v[1] / 60, color='r', lw=0.6, alpha=0.5)
    nv = len(viol)
    fig.suptitle(f"Section 4.2 -- {M['name']}: time histories (Mission Planner v2, online 6-DOF trim every step)\n"
                 f"start {log[0]['mass_kg']:.0f} kg, pads at {M['atmosphere']['pad_altitude_m']:.0f} m ISA+"
                 f"{M['atmosphere']['dISA_K']:.0f}, {M['wind']['headwind_aloft_mps']:.0f} m/s headwind aloft; "
                 f"{'no limit violations' if nv == 0 else f'{nv} limit violations (red lines)'}", fontsize=12)
    seg_legend(fig, log)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    save_figure(fig, "m3_4p2_mission_time_history", "4.2",
                f"{M['name']}: altitude, true airspeed and ground speed with cumulative ground distance, gross mass "
                f"and fuel remaining (dashed: {M['loading']['reserve_fuel_kg']:.0f} kg reserve), nacelle angle and "
                f"rotor RPM, power required vs available (take-off rating in helicopter mode and conversion, "
                f"max-continuous {100 * CFG.MCP_FRACTION:.0f} % in airplane mode), controls and attitude, rotor stall "
                f"and tip-Mach indicators, wing-stall and power margins. Shaded bands and numbers = mission segments. "
                f"Pads {M['atmosphere']['pad_altitude_m']:.0f} m ISA+{M['atmosphere']['dISA_K']:.0f}, "
                f"{M['wind']['headwind_aloft_mps']:.0f} m/s headwind aloft, calm at the pads; {MODEL_NOTE}.")
    # zoom on departure and arrival (helicopter mode + conversion are a few minutes of a 4-hour mission)
    plot_terminal_zoom(log, M)


def plot_terminal_zoom(log, M):
    L = {k: np.array([e[k] for e in log], float) for k in log[0] if k not in NONNUM}
    t = L['t_s']
    segs = bounds_of(log)
    climb_i = [i0 for n, i0, _ in segs if n == "Climb to cruise"][0]
    desc_i = [i1 for n, _, i1 in segs if n == "Descent"][0]
    windows = [("Departure: take-off, conversion, acceleration", 0, climb_i + 2),
               ("Arrival: deceleration, reconversion, landing", desc_i - 1, len(log) - 1)]
    fig, axs = plt.subplots(4, 2, figsize=(15, 12.5), sharex='col')
    for c, (title, i0, i1) in enumerate(windows):
        sl = slice(i0, i1 + 1)
        tt = t[sl]
        a = axs[0, c]
        a.plot(tt, L['altitude_m'][sl], 'k-', lw=1.8)
        a.set_ylabel("Altitude [m]")
        a.set_title(title, fontsize=10.5, pad=16)
        a2 = a.twinx()
        a2.plot(tt, L['V_mps'][sl], 'b-', lw=1.5)
        a2.set_ylabel("True airspeed [m/s]", color='b')
        a2.grid(False)
        a = axs[1, c]
        a.plot(tt, L['nacelle_deg'][sl], color='tab:purple', lw=1.8)
        a.set_ylabel("Nacelle [deg]", color='tab:purple')
        a2 = a.twinx()
        a2.plot(tt, L['rpm'][sl], color='tab:brown', lw=1.5)
        a2.set_ylabel("RPM", color='tab:brown')
        a2.set_ylim(0, 620)
        a2.grid(False)
        a = axs[2, c]
        a.plot(tt, L['P_req_kW'][sl], 'r-', lw=1.6, label='required')
        a.plot(tt, L['P_avail_kW'][sl], 'g-', lw=1.6, label='available')
        a.set_ylabel("Power [kW]")
        a.legend(loc='best')
        a = axs[3, c]
        a.plot(tt, L['rotor_lift_pct'][sl], 'tab:red', lw=1.6, label='rotor lift share [%]')
        a.plot(tt, L['wing_lift_pct'][sl], 'tab:blue', lw=1.6, label='wing + tail lift share [%]')
        a.plot(tt, L['rotor_stall_pct'][sl] * 10, 'm:', lw=1.4, label='stalled rotor area x10 [%]')
        a.set_ylabel("Lift share / stall [%]")
        a.set_xlabel("Mission time [s]")
        a.legend(loc='best', fontsize=7.5)
        sub = [e for e in log[sl]]
        names = [n for n, _, _ in segs]
        shade(axs[:, c], sub, tt, labels_on=[axs[0, c]], first=names.index(sub[0]['segment']))
    fig.suptitle("Section 4.2 -- Departure and arrival detail (segments numbered as in the full time history)",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save_figure(fig, "m3_4p2_terminal_phases_zoom", "4.2",
                "Zoom on the helicopter-mode, conversion and reconversion phases of the design mission: altitude and "
                "airspeed, nacelle angle and RPM, power required vs available, rotor vs wing lift share and stalled "
                f"rotor area (x10). Same run as the full time history; {MODEL_NOTE}.")


def plot_utilisation(log, U, viol):
    t = time_axis(log)
    fig, ax = plt.subplots(figsize=(15, 6.5))
    for k, u in U.items():
        ax.plot(t, u, lw=1.5, label=k)
    ax.axhline(1.0, color='r', lw=1.4, ls='--', label='limit (utilisation = 1)')
    ax.set_ylim(0, 1.25)
    ax.set_xlabel("Mission time [min]")
    ax.set_ylabel("Fraction of the allowable used [-]")
    shade([ax], log, t, labels_on=[ax])
    ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), fontsize=8.5)
    ax.set_title("Section 4.3 -- Constraint utilisation through the design mission (<= 1 feasible); "
                 f"{len(viol)} violations", fontsize=11, pad=16)
    seg_legend(fig, log, y=-0.04)
    fig.tight_layout()
    save_figure(fig, "m3_4p3_constraint_utilisation", "4.3",
                "Every feasibility limit of Mission Planner v2 expressed as the fraction of its allowable value used: "
                "power required / 95 % of available (5 % margin), stalled rotor area / 5 %, advancing-tip Mach / 0.85, "
                "reverse-flow area / 3 %, |wing alpha| / 15 deg (V > 10 m/s), collective / 65 deg, max normalized "
                "pilot stick input, nacelle rate / 8 deg/s, fraction of usable fuel above the reserve burned. The "
                f"highest curve at any time is the active constraint. {MODEL_NOTE}.")


def plot_breakdown(log, segsum):
    """Section 4.4: mean power and fuel per segment."""
    names = [s['segment'] for s in segsum]
    x = np.arange(len(names))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 5.8))
    a1.bar(x - 0.2, [s['P_mean'] for s in segsum], 0.4, color='tab:red', label='mean power required')
    a1.bar(x + 0.2, [s['P_av_min'] for s in segsum], 0.4, color='tab:green', alpha=0.6, label='min power available')
    a1.plot(x, [s['P_max'] for s in segsum], 'k_', ms=18, mew=2, label='peak power required')
    a1.set_xticks(x)
    a1.set_xticklabels([f"{i + 1}. {n}" for i, n in enumerate(names)], rotation=60, ha='right', fontsize=8)
    a1.set_ylabel("Power, both rotors [kW]")
    a1.legend()
    a1.set_title("Power by segment")
    fuel = [s['fuel_kg'] for s in segsum]
    a2.bar(x, fuel, color='tab:orange')
    for i, f in enumerate(fuel):
        a2.text(i, f, f"{f:.0f}", ha='center', va='bottom', fontsize=7.5)
    a2.set_xticks(x)
    a2.set_xticklabels([f"{i + 1}. {n}" for i, n in enumerate(names)], rotation=60, ha='right', fontsize=8)
    a2.set_ylabel("Fuel burned [kg]")
    a2.set_yscale('log')
    a2.set_title("Fuel burned by segment (log scale)")
    fig.suptitle("Section 4.4 -- Power demand and fuel use through the design mission", fontsize=12)
    fig.tight_layout()
    save_figure(fig, "m3_4p4_power_breakdown", "4.4",
                "Mean and peak power required and minimum power available in each segment of the design mission "
                f"(left) and fuel burned per segment (right, log scale). {MODEL_NOTE}.")


def plot_paths(log):
    cache = os.path.join(M2_DIR, "corridor_grid.npz")
    if not os.path.exists(cache):
        print("  (no Milestone 2 corridor cache -- skipping the corridor overlay)")
        return
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Patch
    from m2.conversion_corridor import CATEGORIES
    colors = {'feasible': '#4caf50', 'power': '#e53935', 'wing_stall': '#1e88e5', 'rotor_stall': '#8e24aa',
              'tip_mach': '#fb8c00', 'reverse_flow': '#6d4c41', 'control_saturation': '#9e9e9e',
              'excessive_residual': '#fdd835', 'no_physical_solution': '#212121'}
    g = dict(np.load(cache, allow_pickle=True))
    cat = g["category"].astype(int)

    def edges(v):
        v = np.asarray(v, float)
        m = 0.5 * (v[1:] + v[:-1])
        return np.concatenate([[v[0] - (m[0] - v[0])], m, [v[-1] + (v[-1] - m[-1])]])
    cols = [colors.get(c, '#cccccc') for c in CATEGORIES]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.pcolormesh(edges(g["V"]), edges(g["nacelle"]), cat, cmap=ListedColormap(cols),
                  norm=BoundaryNorm(np.arange(len(CATEGORIES) + 1) - 0.5, len(CATEGORIES)), alpha=0.5,
                  edgecolors='white', linewidth=0.3)
    segs = bounds_of(log)
    for name, st in (("Conversion", 'k-'), ("Reconversion", 'b--')):
        i0, i1 = [(a, b) for n, a, b in segs if n == name][0]
        ax.plot([e['V_mps'] for e in log[i0:i1 + 1]], [e['nacelle_deg'] for e in log[i0:i1 + 1]], st, lw=2.4,
                label=f"{name} (design mission)")
        bad = [(e['V_mps'], e['nacelle_deg']) for e in log[i0:i1 + 1] if not e['feasible']]
        if bad:
            ax.plot(*zip(*bad), 'rx', ms=8, mew=2)
    hs, _ = ax.get_legend_handles_labels()
    hs += [Patch(color=cols[i], alpha=0.5, label=CATEGORIES[i]) for i in sorted(set(cat.ravel()))]
    ax.legend(handles=hs, loc='upper left', bbox_to_anchor=(1.01, 1.0), fontsize=8)
    ax.set_xlabel("True airspeed V [m/s]")
    ax.set_ylabel("Nacelle angle [deg]")
    ax.set_title("Design-mission conversion / reconversion on the Milestone 2 corridor map\n"
                 f"(map: {CFG.REFERENCE_ALTITUDE_M:.0f} m ISA ~ same density as 1500 m ISA+15, 7200 kg, "
                 f"{CFG.CONVERSION_RPM:.0f} RPM, unaccelerated level flight)", fontsize=10)
    fig.tight_layout()
    save_figure(fig, "m3_4_paths_on_corridor", "3.2",
                "Airspeed-nacelle trajectories flown in the design mission (accelerating / climbing conversion, "
                "decelerating / descending reconversion) over the Milestone 2 steady-flight corridor map "
                "(2000 m ISA, density 1.007 kg/m3, vs 1.004 kg/m3 at the 1500 m ISA+15 pads). Red crosses would mark "
                "infeasible steps.")


def definition_table(M, flown):
    a, ld, w = M["atmosphere"], M["loading"], M["wind"]
    rows = []
    for i, s in enumerate(flown):
        s0, s1 = s.state(0.0), s.state(1.0)
        nac = ("conversion path n(V)" if s.nacelle_of_speed is DM.NAC_CONV else
               "reconversion path n(V)" if s.nacelle_of_speed is DM.NAC_RECONV else
               f"{s0['nacelle']:.0f} -> {s1['nacelle']:.0f}")
        rows.append([i + 1, s.name, s.kind, f"{s.duration_s:.0f}", f"{s.dt_s:.0f}",
                     f"{s0['V_h']:.0f} -> {s1['V_h']:.0f}", f"{DM.seg_integral(s, 'climb'):+.0f}", nac,
                     f"{s0['rpm']:.0f} -> {s1['rpm']:.0f}", f"{s.headwind(0.5):.0f}",
                     "TO" if s.power_rating == 1.0 else f"MCP ({100 * s.power_rating:.0f} %)"])
    txt = [f"# Section 4.1 -- design mission definition: {M['name']}", "", M["description"], "",
           md_table(["Item", "Value"], [
               ["Aircraft", f"final design (frozen M2 configuration), rotor '{CFG.ROTOR_VARIANT}', 2 x {CFG.ENGINE_NAME}"],
               ["Take-off mass", f"{CFG.get_default_aircraft().mass_kg(ld['fuel_kg'], ld['payload_kg']):.0f} kg "
                                 f"(MTOW {CFG.GROSS_MASS_KG:.0f} kg)"],
               ["Payload", f"{ld['payload_kg']:.0f} kg (10 passengers), carried throughout"],
               ["Fuel at take-off / reserve", f"{ld['fuel_kg']:.0f} kg / {ld['reserve_fuel_kg']:.0f} kg "
                                              "(must remain at landing)"],
               ["Pads (take-off and landing)", f"{a['pad_altitude_m']:.0f} m, ISA+{a['dISA_K']:.0f} K"],
               ["Wind", f"{w['headwind_aloft_mps']:.0f} m/s headwind aloft (whole route), calm at the pads"],
               ["Range (ground distance)", f"{M['range_km']:.0f} km"],
               ["Cruise", f"{M['cruise']['altitude_m']:.0f} m ISA+{a['dISA_K']:.0f}, {M['cruise']['speed_mps']:.0f} m/s "
                          f"TAS, {M['cruise']['rpm']:.0f} RPM (long-range)"],
               ["Climb / descent", f"{M['climb']['rate_mps']:+.0f} / {M['descent']['rate_mps']:+.0f} m/s at "
                                   f"{M['climb']['speed_mps']:.0f} m/s, {M['climb']['rpm']:.0f} RPM"],
               ["Conversion schedule", f"0 -> 70 m/s in {M['conversion']['duration_s']:.0f} s along "
                                       f"{CFG.CONVERSION_PATH} (V, i_n), {M['conversion']['rpm']:.0f} RPM"],
               ["Reconversion schedule", f"70 -> 0 m/s in {M['reconversion']['duration_s']:.0f} s along "
                                         f"{CFG.RECONVERSION_PATH}"],
               ["Engine rating", f"take-off rating in hover / vertical / conversion; max-continuous "
                                 f"({100 * CFG.MCP_FRACTION:.0f} %) in airplane mode"],
               ["Controls", "online 6-DOF trim at every time step (no scheduled controls)"],
           ]), "", "Segments as flown (climb, cruise and vertical-descent durations sized at run time):", "",
           md_table(["#", "Segment", "Type", "Duration [s]", "dt [s]", "Airspeed [m/s]", "Altitude change [m]",
                     "Nacelle [deg]", "RPM", "Headwind [m/s]", "Engine rating"], rows)]
    write_text("m3_4p1_mission_definition.md", "\n".join(txt) + "\n")


def tables(log, viol, M, U):
    mt = DM.margin_table(log, U)
    rows = [[r['constraint'], f"{r['peak']:.3f}", f"{r['margin_pct']:.1f} %", r['segment'], f"{r['t_s'] / 60:.1f}",
             f"{r['V']:.0f}", f"{r['h']:.0f}", f"{r['nacelle']:.0f}", f"{r['rpm']:.0f}"] for r in mt]
    first = mt[0]
    txt = ["# Section 4.3 -- limit margins along the mission", "",
           f"{len(log)} trimmed time steps, {len(viol)} limit violations. Utilisation = fraction of the allowable "
           "value used (<= 1 feasible); margin = 1 - utilisation.", "",
           md_table(["Constraint", "Peak utilisation", "Minimum margin", "Segment", "Time [min]", "V [m/s]",
                     "Altitude [m]", "Nacelle [deg]", "RPM"], rows), "",
           f"**Minimum margin:** {first['constraint']} -- {first['margin_pct']:.1f} % margin in segment "
           f"'{first['segment']}' at t = {first['t_s'] / 60:.1f} min (V = {first['V']:.0f} m/s, "
           f"h = {first['h']:.0f} m, nacelle {first['nacelle']:.0f} deg, {first['rpm']:.0f} RPM)."]
    if viol:
        txt += ["", "Violations:"] + [f"* t = {t:.0f} s [{s}]: {r}" for s, t, r in viol[:30]]
    write_text("m3_4p3_margins.md", "\n".join(txt) + "\n")

    ss = DM.segment_summary(log)
    rows = [[i + 1, s['segment'], f"{s['dt']:.0f}", f"{s['dist_km']:.1f}", f"{s['h0']:.0f} -> {s['h1']:.0f}",
             f"{s['V0']:.0f} -> {s['V1']:.0f}", f"{s['m0']:.0f} -> {s['m1']:.0f}", f"{s['P_mean']:.0f}",
             f"{s['P_max']:.0f}", f"{s['P_av_min']:.0f}", f"{s['fuel_kg']:.1f}",
             f"{s['fuel_kg'] / max(s['dt'], 1e-9) * 3600:.0f}", f"{s['rotor_lift_pct']:.0f}",
             "yes" if s['feasible'] else "NO"] for i, s in enumerate(ss)]
    tot_fuel = log[0]['fuel_kg'] - log[-1]['fuel_kg']
    txt = ["# Section 4.4 -- segment summary", "",
           md_table(["#", "Segment", "Time [s]", "Ground dist. [km]", "Altitude [m]", "TAS [m/s]", "Mass [kg]",
                     "Mean P_req [kW]", "Peak P_req [kW]", "Min P_avail [kW]", "Fuel [kg]", "Fuel flow [kg/h]",
                     "Rotor lift share [%]", "Feasible"], rows), "",
           f"Total: {log[-1]['t_s'] / 3600:.2f} h, {log[-1]['distance_km']:.1f} km ground distance, fuel used "
           f"{tot_fuel:.0f} kg, fuel at landing {log[-1]['fuel_kg']:.0f} kg "
           f"(reserve {M['loading']['reserve_fuel_kg']:.0f} kg -> {log[-1]['fuel_kg'] - M['loading']['reserve_fuel_kg']:+.0f} kg "
           f"above reserve)."]
    write_text("m3_4p4_segment_summary.md", "\n".join(txt) + "\n")
    summ = dict(mission=M['name'], time_h=log[-1]['t_s'] / 3600, distance_km=log[-1]['distance_km'],
                fuel_used_kg=tot_fuel, fuel_landing_kg=log[-1]['fuel_kg'],
                reserve_kg=M['loading']['reserve_fuel_kg'], violations=len(viol),
                min_margin=dict(constraint=first['constraint'], margin_pct=first['margin_pct'],
                                segment=first['segment'], t_min=first['t_s'] / 60),
                max_power_kW=max(e['P_req_kW'] for e in log),
                min_power_margin_pct=min(e['power_margin_pct'] for e in log),
                cruise=dict(altitude_m=M['cruise']['altitude_m'], V_mps=M['cruise']['speed_mps'],
                            rpm=M['cruise']['rpm']),
                segments=ss, margins=mt)
    with open(os.path.join(OUT_DIR, "m3_4_mission_summary.json"), 'w', encoding='utf-8') as f:
        json.dump(summ, f, indent=1, default=float)
    return ss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mission", default=DEFAULT_MISSION)
    ap.add_argument("--replot", action="store_true", help="re-plot from outputs/m3/m3_4_mission_log.csv")
    a = ap.parse_args()
    M = DM.load_mission(a.mission)
    t0 = time.time()
    if a.replot and os.path.exists(LOG):
        log = load_log()
        viol = [(e['segment'], e['t_s'], e['flags'] or e['trim_status']) for e in log if not e['feasible']]
        _, _, flown = None, None, None
    else:
        print(f"Flying '{M['name']}' ({M['range_km']:.0f} km) ...")
        log, viol, flown = DM.fly(M)
        save_log(log)
        print(f"  {len(log)} trimmed steps in {time.time() - t0:.0f} s, {len(viol)} violations")
    if flown is not None:
        definition_table(M, flown)
    U = DM.utilisation(log, M)
    ss = tables(log, viol, M, U)
    plot_time_history(log, viol, M)
    plot_utilisation(log, U, viol)
    plot_breakdown(log, ss)
    plot_paths(log)


if __name__ == "__main__":
    main()
