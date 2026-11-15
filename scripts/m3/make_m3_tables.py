"""
Milestone 3 -- design tables and design-conclusion tables.

    python scripts/m3/make_m3_tables.py

Run after performance_summary.py and run_design_mission.py (reads
outputs/m3/m3_3_performance.json and m3_4_mission_summary.json).

Outputs (outputs/m3/):
  m3_1p2_final_design_table.md     Section 1.2 rotor, wing, empennage, propulsion, mass, fuel, control parameters
  m3_1p3_design_evolution.md       Section 1.3 changes after Milestone 2 and reasons
  m3_1p4_compliance.md             Section 1.4 status against the Milestone 1 targets
  m3_2p1_assumptions.md            Section 2.1 new / modified assumptions after Milestone 2
  m3_3p2_restrictive_condition.md  Section 3.2 tightest constraint during conversion / reconversion
  m3_3p4_comparison.md / .png      Section 3.4 comparison with XV-15, AW609, V-22 (normalized metrics)
"""
import json
import os

import numpy as np

from _common import CFG, plt, save_figure, write_text, md_table, OUT_DIR
import m3.final_design as FD

G = CFG.G
M1 = CFG.M1


def load(name):
    p = os.path.join(OUT_DIR, name)
    if not os.path.exists(p):
        raise SystemExit(f"{name} not found -- run performance_summary.py and run_design_mission.py first")
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def design_table():
    ac = CFG.get_default_aircraft()
    R, w, t, v = CFG.ROTOR, ac.wing, ac.htail, ac.vtail
    lim, mix = ac.limits, ac.mixing
    A = R.disk_area_m2()
    W = CFG.GROSS_MASS_KG * G
    P_inst = 2 * CFG.POWER_PER_ENGINE_SL_W / 1e3
    empty = sum(it.mass_kg for it in ac.mass_items if it.category == 'empty')
    cg_h, cg_a = ac.cg_ref_m(90.0), ac.cg_ref_m(0.0)
    sec = [
        ("Proprotors (x2, interconnected)", [
            ("Radius / diameter", f"{R.radius_m:.2f} m / {2 * R.radius_m:.1f} m"),
            ("Blades", f"{R.num_blades}"),
            ("Chord root / tip (linear taper)", f"{R.chord_fn(R.root_cutout_m / R.radius_m):.2f} m / {R.chord_fn(1.0):.2f} m "
                                                f"(taper {M1.TAPER_RATIO:.3f})"),
            ("Twist", f"linear, {CFG.TWIST_DESC} ('{CFG.ROTOR_VARIANT}')"),
            ("Root cut-out", f"{R.root_cutout_m:.2f} m ({R.root_cutout_m / R.radius_m:.3f} R)"),
            ("Solidity (thrust-weighted)", f"{R.solidity():.3f}"),
            ("Airfoil model", CFG.AIRFOIL_NAME),
            ("Disk loading at MTOW", f"{W / (2 * A):.0f} N/m2 ({CFG.GROSS_MASS_KG / (2 * A):.1f} kg/m2)"),
            ("RPM schedule", f"{CFG.HOVER_RPM:.0f} hover / conversion; airplane mode {CFG.LONG_RANGE_RPM:.0f} "
                             f"(long range), {CFG.AIRPLANE_RPM:.0f} (to 100 m/s), {CFG.DASH_RPM:.0f} (dash)"),
            ("Tip speed hover / long-range cruise", f"{R.tip_speed_mps(CFG.HOVER_OMEGA):.0f} / "
                                                    f"{R.tip_speed_mps(CFG.rpm_to_omega(CFG.LONG_RANGE_RPM)):.0f} m/s"),
            ("Rotation", "right rotor CCW, left rotor CW (seen from above)"),
        ]),
        ("Wing", [
            ("Area / span / AR", f"{w.S_m2:.2f} m2 / {w.span_m:.2f} m / {w.AR:.1f}"),
            ("Mean chord / incidence", f"{w.chord_m:.2f} m / {w.i_w_deg:.1f} deg"),
            ("Lift model", f"CL_alpha {w.CL_alpha:.2f} /rad (e = {w.e_oswald}), stall {w.alpha_stall_deg:.0f} deg, "
                           f"CD0 {w.CD0}"),
            ("Wing loading at MTOW", f"{W / w.S_m2:.0f} N/m2 ({CFG.GROSS_MASS_KG / w.S_m2:.0f} kg/m2)"),
            ("Flaperons", f"{w.aileron_eta[0]:.2f}-{w.aileron_eta[1]:.2f} of semi-span, +/-{w.aileron_limit_deg:.0f} deg"),
        ]),
        ("Empennage", [
            ("H-tail area / AR / incidence", f"{t.S_m2:.1f} m2 / {t.AR:.1f} / {t.i_t_deg:.0f} deg; tail arm "
                                             f"{cg_h[0] - ac.htail_ac_ref_m[0]:.2f} m"),
            ("Elevator", f"{100 * t.elevator_chord_frac:.0f} % chord, +/-{t.elevator_limit_deg:.0f} deg"),
            ("V-tail area / AR", f"{v.S_m2:.1f} m2 / {v.AR:.1f}; rudder {100 * v.rudder_chord_frac:.0f} % chord, "
                                 f"+/-{v.rudder_limit_deg:.0f} deg"),
        ]),
        ("Propulsion", [
            ("Engines", f"2 x {CFG.ENGINE_NAME} turboshaft, one per tilting nacelle, cross-shafted"),
            ("Take-off / max-continuous power", f"{CFG.POWER_PER_ENGINE_SL_W / 1e3:.0f} / "
                                                f"{CFG.MCP_FRACTION * CFG.POWER_PER_ENGINE_SL_W / 1e3:.0f} kW each, SL ISA"),
            ("Installed power loading", f"{CFG.GROSS_MASS_KG / P_inst:.2f} kg/kW"),
            ("Power lapse / drivetrain", f"(rho/rho0)^{M1.DENSITY_RATIO_EXPONENT}, efficiency {M1.DRIVETRAIN_EFFICIENCY}"),
            ("SFC", f"{CFG.ENGINE_SFC_KG_PER_J * 3.6e9:.0f} g/kWh (constant)"),
        ]),
        ("Mass and fuel", [
            ("MTOW", f"{CFG.GROSS_MASS_KG:.0f} kg"),
            ("Empty mass incl. crew", f"{empty:.0f} kg ({empty / CFG.GROSS_MASS_KG:.3f} of MTOW)"),
            ("Payload", f"{M1.PAYLOAD_KG:.0f} kg (10 passengers)"),
            ("Fuel capacity / reserve", f"{CFG.FUEL_CAPACITY_KG:.0f} kg / {M1.RESERVE_FUEL_KG:.0f} kg (wing tanks)"),
            ("CG at MTOW, helicopter / airplane mode", f"x {cg_h[0]:+.2f}, z {cg_h[2]:+.2f} m / x {cg_a[0]:+.2f}, "
                                                       f"z {cg_a[2]:+.2f} m from wing-root c/4"),
        ]),
        ("Controls and limits", [
            ("Collective", f"{lim.collective_deg[0]:.0f} to {lim.collective_deg[1]:.0f} deg (on top of twist)"),
            ("Cyclic theta1c / theta1s", f"+/-{lim.theta_1c_deg[1]:.0f} / +/-{lim.theta_1s_deg[1]:.0f} deg"),
            ("Stick mixing (faded with sin^2 i_n)", f"pitch: theta1c {mix.K_cyc_deg:.0f} deg + elevator {mix.K_e_deg:.0f} deg; "
                                                    f"roll: diff. collective {mix.K_dcol_deg:.0f} deg + flaperon "
                                                    f"{mix.K_a_deg:.0f} deg; yaw: diff. theta1s {mix.K_dcyc_deg:.0f} deg + "
                                                    f"rudder {mix.K_r_deg:.0f} deg"),
            ("Nacelle angle / rate", f"{lim.nacelle_deg[0]:.0f}-{lim.nacelle_deg[1]:.0f} deg, {lim.nacelle_rate_deg_s:.0f} deg/s"),
            ("Rotor RPM range", f"{lim.rpm[0]:.0f}-{lim.rpm[1]:.0f}"),
            ("Feasibility limits", f"tip Mach <= {lim.max_tip_mach}, stalled area <= {100 * lim.max_stall_fraction:.0f} %, "
                                   f"reverse flow <= {100 * lim.max_reverse_flow_fraction:.0f} %, power margin >= "
                                   f"{100 * lim.min_power_margin_frac:.0f} %, wing alpha < stall"),
        ]),
    ]
    out = ["# Section 1.2 -- final design table", "",
           "All values are read from src/m2/aircraft_input_m2.py (frozen Milestone 2 configuration).", ""]
    for name, rows in sec:
        out += [f"## {name}", "", md_table(["Parameter", "Value"], rows), ""]
    write_text("m3_1p2_final_design_table.md", "\n".join(out))


def evolution():
    out = ["# Section 1.3 -- changes since Milestone 2", "",
           "Earlier changes (M1 -> M2) are in src/m2/aircraft_input_m2.py DESIGN_CHANGES / m2_5_design_tables.md.", "",
           md_table(["#", "Change after Milestone 2", "Quantitative / physical reason"],
                    [[i + 1, c, r] for i, (c, r) in enumerate(FD.FINAL_CHANGES)])]
    write_text("m3_1p3_design_evolution.md", "\n".join(out) + "\n")
    out = ["# Section 2.1 -- new or modified assumptions after Milestone 2", "",
           "Unchanged assumptions (rigid disk, linear airfoil with stall flag, annular-Glauert inflow, airframe "
           "model, limits) are not repeated; see docs/milestone2/Milestone_2_Architecture.md.", "",
           md_table(["Area", "Assumption (new or modified)"], FD.NEW_ASSUMPTIONS)]
    write_text("m3_2p1_assumptions.md", "\n".join(out) + "\n")


def status(value, target, sense, key=""):
    if value is None or not np.isfinite(value):
        return "not evaluated"
    ok = value >= target if sense == ">=" else value <= target
    near = abs(value - target) <= FD.MARGINAL_BAND * abs(target) and key not in FD.DEFINITIONAL
    if ok:
        return "MARGINAL" if near else "ACHIEVED"
    return "MARGINAL" if near else "NOT ACHIEVED"


def compliance(perf, mis):
    hover_pad = [h for h in perf['hover'] if h['dT'] > 0][0]
    usable = CFG.FUEL_CAPACITY_KG - M1.RESERVE_FUEL_KG
    endurance = usable / hover_pad['fuel_kg_h'] * 60
    vm = perf['max_speed']
    vmax_mcp = np.nanmax(vm['MCP']['V'])
    vmax_to = np.nanmax(vm['take-off rating']['V'])
    m = {r['constraint']: r for r in mis['margins']}
    pk = lambda key: [r for k, r in m.items() if k.startswith(key)][0]          # noqa: E731
    tip = pk("Advancing-tip Mach")['peak'] * M1.MAX_TIP_MACH
    cr = [sg for sg in mis['segments'] if sg['segment'] == "Cruise"][0]
    cr_kgkm = cr['fuel_kg'] / cr['dist_km']
    extra_fuel = mis['fuel_landing_kg'] - mis['reserve_kg']
    extra_km = extra_fuel / cr_kgkm
    ok_mission = mis['violations'] == 0 and extra_fuel >= 0
    range_cap = mis['distance_km'] + extra_km if ok_mission else np.nan
    stall = pk("Rotor stall")['peak'] * 100 * M1.MAX_STALL_FRACTION
    values = {
        "payload": (M1.PAYLOAD_KG, "carried over the whole design mission"),
        "mtow": (CFG.get_default_aircraft().mass_kg(), "mass breakdown at full fuel and payload"),
        "hover_pad": (perf['max_hover_mass_pad_kg'], f"max OGE hover mass at the pads ({hover_pad['margin']:.0f} % "
                                                     "power margin at MTOW)"),
        "range": (range_cap, f"{mis['distance_km']:.0f} km design mission flown with 0 violations, "
                             f"{extra_fuel:.0f} kg above reserve at landing = +{extra_km:.0f} km at the cruise rate "
                             f"({cr_kgkm:.3f} kg/km incl. 5 m/s headwind)"),
        "cruise_speed": (mis['cruise']['V_mps'], "design-mission cruise TAS"),
        "max_speed": (vmax_mcp, f"MCP, best altitude ({vmax_to:.0f} m/s with take-off rating)"),
        "hover_endurance": (endurance, f"{usable:.0f} kg usable / {hover_pad['fuel_kg_h']:.0f} kg/h at the pads"),
        "reserve": (mis['fuel_landing_kg'], "fuel remaining at the end of the design mission"),
        "power_margin": (mis['min_power_margin_pct'], "minimum over the design mission"),
        "tip_mach": (tip, "maximum over the design mission"),
        "rotor_stall": (stall, "maximum over the design mission"),
    }
    rows, res = [], {}
    for key, desc, target, unit, sense in FD.REQUIREMENTS:
        val, how = values[key]
        st = status(val, target, sense, key)
        res[key] = (val, st)
        rows.append([desc, f"{sense} {target:g} {unit}", f"{val:.4g} {unit}" if np.isfinite(val) else "-", st, how])
    out = ["# Section 1.4 -- status against the Milestone 1 targets", "",
           f"Requirements / targets adopted in Milestone 1 (src/aircraft_input.py). MARGINAL = within "
           f"{100 * FD.MARGINAL_BAND:.0f} % of the target.", "",
           md_table(["Requirement", "Target", "Final design", "Status", "Evidence"], rows)]
    write_text("m3_1p4_compliance.md", "\n".join(out) + "\n")
    return res


def restrictive(mis):
    import csv
    with open(os.path.join(OUT_DIR, "m3_4_mission_log.csv"), encoding='utf-8') as f:
        log = list(csv.DictReader(f))
    import m3.design_mission as DM
    num = lambda e: {k: (float(v) if k not in ('segment', 'kind', 'flags', 'trim_status', 'feasible')   # noqa: E731
                         else v) for k, v in e.items()}
    log = [num(e) for e in log]
    with open(os.path.join(OUT_DIR, "..", "..", "inputs", "m3_design_mission.json"), encoding='utf-8') as f:
        M = json.load(f)
    out = ["# Section 3.2 -- tightest constraint during conversion / reconversion (design mission)", ""]
    for seg in ("Conversion", "Reconversion"):
        L = [e for e in log if e['segment'] == seg]
        U = DM.utilisation(L, M)
        U.pop("Usable fuel used (above reserve)", None)
        mt = DM.margin_table(L, U)
        rows = [[r['constraint'], f"{r['peak']:.3f}", f"{r['margin_pct']:.1f} %", f"{r['V']:.0f}",
                 f"{r['nacelle']:.0f}"] for r in mt]
        out += [f"## {seg}", "", md_table(["Constraint", "Peak utilisation", "Margin", "V [m/s]", "Nacelle [deg]"],
                                         rows), "",
                f"Tightest: **{mt[0]['constraint']}**, {mt[0]['margin_pct']:.1f} % margin at "
                f"V = {mt[0]['V']:.0f} m/s, nacelle {mt[0]['nacelle']:.0f} deg.", ""]
    write_text("m3_3p2_restrictive_condition.md", "\n".join(out))


def comparison(perf, mis):
    ac = CFG.get_default_aircraft()
    empty = sum(it.mass_kg for it in ac.mass_items if it.category == 'empty')
    vmax = np.nanmax(perf['max_speed']['take-off rating']['V']) * 3.6
    ours = dict(mtow=CFG.GROSS_MASS_KG, empty=empty, rotor_d=2 * CFG.ROTOR.radius_m, wing_area=ac.wing.S_m2,
                power=2 * CFG.POWER_PER_ENGINE_SL_W / 1e3, v_max=vmax, range=mis['distance_km'], pax=10,
                source="this design (Milestone 3 analysis; range = design mission with reserve intact)")
    data = dict(FD.REFERENCE_AIRCRAFT)
    data["Team 6 design"] = ours

    def metrics(d):
        W = d['mtow'] * G
        A = np.pi * (d['rotor_d'] / 2) ** 2
        return dict(DL=W / (2 * A), WL=(W / d['wing_area']) if d['wing_area'] else np.nan,
                    PL=d['mtow'] / d['power'], PW=d['power'] / d['mtow'], UL=1 - d['empty'] / d['mtow'],
                    v=d['v_max'], R=d['range'])
    met = {k: metrics(d) for k, d in data.items()}
    rows = [[k, f"{d['mtow']:.0f}", f"{d['rotor_d']:.2f}", f"{met[k]['DL']:.0f}",
             f"{met[k]['WL']:.0f}" if np.isfinite(met[k]['WL']) else "n/a", f"{met[k]['PL']:.2f}",
             f"{met[k]['UL']:.2f}", f"{d['v_max']:.0f}", f"{d['range']:.0f}", d['source']] for k, d in data.items()]
    out = ["# Section 3.4 -- comparison with relevant tiltrotors", "",
           md_table(["Aircraft", "MTOW [kg]", "Rotor dia. [m]", "Disk loading [N/m2]", "Wing loading [N/m2]",
                     "Power loading MTOW/P_TO [kg/kW]", "Useful-load fraction 1-OEW/MTOW", "Max speed [km/h]",
                     "Range [km]", "Source"], rows), "",
           "Max speed of this design: level flight, take-off rating, best altitude analysed. Range: published ranges "
           "are standard-fuel ranges (reserve rules differ); ours is the 1000 km design mission with 450 kg reserve "
           "remaining."]
    write_text("m3_3p4_comparison.md", "\n".join(out) + "\n")
    keys = [("DL", "Disk loading [N/m2]"), ("WL", "Wing loading [N/m2]"), ("PL", "Power loading [kg/kW]"),
            ("UL", "Useful-load fraction [-]"), ("v", "Max speed [km/h]")]
    fig, axs = plt.subplots(1, len(keys), figsize=(17, 4.6))
    names = list(data)
    cols = ['0.6', '0.45', '0.3', 'tab:red']
    for ax, (k, lab) in zip(axs, keys):
        vals = [met[n][k] for n in names]
        bars = ax.bar(range(len(names)), [0 if not np.isfinite(v) else v for v in vals], color=cols)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), "n/a" if not np.isfinite(v) else
                    (f"{v:.2f}" if v < 10 else f"{v:.0f}"), ha='center', va='bottom', fontsize=8)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=35, ha='right', fontsize=8)
        ax.set_title(lab, fontsize=9.5)
    fig.suptitle("Section 3.4 -- Final design vs published tiltrotors (normalized metrics at MTOW)", fontsize=12)
    fig.tight_layout()
    save_figure(fig, "m3_3p4_comparison", "3.4",
                "Disk loading W/(2A), wing loading W/S, installed power loading MTOW / total take-off power, "
                "useful-load fraction 1 - OEW/MTOW and maximum speed of the final design vs the Bell XV-15, Leonardo "
                "AW609 and Bell Boeing V-22 (published data, sources in m3_3p4_comparison.md; AW609 wing area not "
                "published in the cited source). Our max speed: 6-DOF trim, take-off rating, level flight.")


def main():
    perf, mis = load("m3_3_performance.json"), load("m3_4_mission_summary.json")
    design_table()
    evolution()
    compliance(perf, mis)
    restrictive(mis)
    comparison(perf, mis)


if __name__ == "__main__":
    main()
