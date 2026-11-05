"""
Milestone 3 -- end-to-end design mission built on Mission Planner v2.

No new aerodynamics: every step is the Milestone 2 online 6-DOF trim
(m2.mission_v2.MissionPlannerV2). This module only
  * reads the mission definition from a JSON input file (inputs/*.json),
  * builds the M2Segment list from it (take-off hover -> vertical climb ->
    conversion along the Milestone 2 corridor path -> airplane-mode
    acceleration / RPM reduction -> climb -> cruise -> descent -> deceleration
    -> reconversion -> hover -> vertical descent -> landing hover),
  * sizes the climb, cruise and vertical-descent durations at run time from
    the current altitude / ground distance, so the mission reaches the cruise
    altitude, flies exactly `range_km` and lands on the pad,
  * turns every logged limit into a "fraction of the allowable used"
    (utilisation; <= 1 is feasible) so the smallest margin and its location
    can be read off one table.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import m2.aircraft_input_m2 as CFG                      # noqa: E402
from m2.mission_v2 import MissionPlannerV2, M2Segment, schedule, ramp_schedule  # noqa: E402


_trapz = getattr(np, "trapezoid", None) or np.trapz      # numpy >= 2.0 / 1.x


def load_mission(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _path_fn(path):
    v, n = zip(*path)
    return lambda V: float(np.interp(V, v, n))


NAC_CONV = _path_fn(CFG.CONVERSION_PATH)
NAC_RECONV = _path_fn(CFG.RECONVERSION_PATH)
V_CONV_END = CFG.CONVERSION_PATH[-1][0]          # 70 m/s: nacelles at 0 deg


def rating(M, kind):
    r = M["engine_ratings"]["airplane" if kind in ("airplane", "climb", "cruise", "descent")
                            else "hover_vertical_conversion"]
    return CFG.MCP_FRACTION if r == "MCP" else float(r)


def plateau(rate, edge=0.05):
    """Climb-rate schedule 0 -> rate -> 0 with short linear ramps."""
    return schedule([(0, 0.0), (edge, rate), (1 - edge, rate), (1, 0.0)])


def sized_plateau(dh, rate, dt):
    """Duration and climb schedule that change the altitude by exactly dh with
    the planner's explicit-Euler update (left-point samples k*dt, k < n): the
    rate ramps over one time step at each end, so n-1 samples sit on the
    plateau and the altitude change is rate*(T - dt)."""
    T = abs(dh / rate) + dt
    return T, plateau(rate, edge=dt / T)


def seg_integral(seg, key, n=2001):
    """Integral over the segment of a state quantity ('climb' -> altitude change,
    'ground' -> ground distance)."""
    tau = np.linspace(0, 1, n)
    if key == 'ground':
        y = [seg.state(t)['V_h'] - seg.state(t)['wind'] for t in tau]
    else:
        y = [seg.state(t)[key] for t in tau]
    return float(_trapz(y, tau) * seg.duration_s)


# ---------------------------------------------------------------------------
# segment builders (each returns one M2Segment)
# ---------------------------------------------------------------------------
def departure_segments(M):
    ts, w = M["time_steps"], M["wind"]["headwind_aloft_mps"]
    tk, cv, at = M["takeoff"], M["conversion"], M["airplane_transition"]
    rpm_h = cv["rpm"]
    R = lambda k: rating(M, k)                                           # noqa: E731
    cl = tk["vertical_climb_mps"]
    return [
        M2Segment("Take-off hover", "hover", tk["hover_s"], ts["hover_s"], schedule(0.0), schedule(0.0),
                  schedule(90.0), schedule(rpm_h), headwind_mps=0.0, power_rating=R("hover")),
        M2Segment("Vertical climb", "vertical", tk["vertical_climb_s"], ts["hover_s"], schedule(0.0),
                  schedule([(0, 0.0), (0.15, cl), (0.85, cl), (1, 0.0)]), schedule(90.0), schedule(rpm_h),
                  headwind_mps=0.0, power_rating=R("vertical")),
        M2Segment("Conversion", "conversion", cv["duration_s"], ts["conversion_s"],
                  ramp_schedule(0.0, V_CONV_END),
                  schedule([(0, 0.0), (0.45, 0.0), (0.65, cv["climb_after_mps"]), (1, cv["climb_after_mps"])]),
                  schedule(90.0), schedule(rpm_h), nacelle_of_speed=NAC_CONV,
                  headwind_mps=schedule([(0, 0.0), (0.4, w), (1, w)]), power_rating=R("conversion")),
        M2Segment("Accel. + RPM reduction", "airplane", at["duration_s"], ts["airplane_s"],
                  ramp_schedule(V_CONV_END, at["speed_mps"]), schedule([(0, cv["climb_after_mps"]), (1, 0.0)]),
                  schedule(0.0), schedule([(0, rpm_h), (0.6, at["rpm"]), (1, at["rpm"])]), headwind_mps=w,
                  power_rating=R("airplane")),
    ]


def climb_segment(M, h_now):
    c, cr, w = M["climb"], M["cruise"], M["wind"]["headwind_aloft_mps"]
    dh = cr["altitude_m"] - h_now
    if dh <= 0:
        raise ValueError(f"cruise altitude {cr['altitude_m']} m is below the current altitude {h_now:.0f} m")
    T, clb = sized_plateau(dh, c["rate_mps"], c["dt_s"])
    return M2Segment("Climb to cruise", "climb", T, c["dt_s"], schedule(c["speed_mps"]), clb,
                     schedule(0.0), schedule(c["rpm"]), headwind_mps=w, power_rating=rating(M, "climb"))


def rpm_change(M, name, V, rpm0, rpm1):
    cr = M["cruise"]
    return M2Segment(name, "cruise", cr["rpm_change_s"], M["time_steps"]["airplane_s"], schedule(V), schedule(0.0),
                     schedule(0.0), schedule([(0, rpm0), (0.8, rpm1), (1, rpm1)]),
                     headwind_mps=M["wind"]["headwind_aloft_mps"], power_rating=rating(M, "cruise"))


def cruise_segment(M, ground_km):
    cr, w = M["cruise"], M["wind"]["headwind_aloft_mps"]
    gs = cr["speed_mps"] - w
    if ground_km <= 0:
        raise ValueError("range_km is too short for the climb / descent / terminal segments")
    return M2Segment("Cruise", "cruise", ground_km * 1e3 / gs, cr["dt_s"], schedule(cr["speed_mps"]), schedule(0.0),
                     schedule(0.0), schedule(cr["rpm"]), headwind_mps=w, power_rating=rating(M, "cruise"))


def descent_segment(M):
    d, cr = M["descent"], M["cruise"]
    bottom = M["atmosphere"]["pad_altitude_m"] + d["bottom_above_pad_m"]
    T, clb = sized_plateau(cr["altitude_m"] - bottom, d["rate_mps"], d["dt_s"])
    return M2Segment("Descent", "descent", T, d["dt_s"], schedule(d["speed_mps"]), clb,
                     schedule(0.0), schedule(d["rpm"]), headwind_mps=M["wind"]["headwind_aloft_mps"],
                     power_rating=rating(M, "descent"))


def arrival_segments(M):
    ts, w = M["time_steps"], M["wind"]["headwind_aloft_mps"]
    rc, d, cv = M["reconversion"], M["descent"], M["conversion"]
    rpm_h = cv["rpm"]
    R = lambda k: rating(M, k)                                           # noqa: E731
    return [
        M2Segment("Decel. + RPM increase", "airplane", rc["decel_s"], ts["airplane_s"],
                  ramp_schedule(d["speed_mps"], V_CONV_END), schedule([(0, 0.0), (1, -1.5)]), schedule(0.0),
                  schedule([(0, d["rpm"]), (0.5, rpm_h), (1, rpm_h)]), headwind_mps=w, power_rating=R("airplane")),
        M2Segment("Reconversion", "conversion", rc["duration_s"], ts["conversion_s"], ramp_schedule(V_CONV_END, 0.0),
                  schedule([(0, -1.5), (0.25, 0.0), (0.65, 0.0), (0.8, -1.0), (0.95, -1.0), (1, 0.0)]),
                  schedule(90.0), schedule(rpm_h), nacelle_of_speed=NAC_RECONV,
                  headwind_mps=schedule([(0, w), (0.6, w), (1, 0.0)]), power_rating=R("conversion")),
        M2Segment("Hover", "hover", M["landing"]["hover_s"], ts["hover_s"], schedule(0.0), schedule(0.0),
                  schedule(90.0), schedule(rpm_h), headwind_mps=0.0, power_rating=R("hover")),
    ]


def vertical_descent(M, h_now):
    L, ts = M["landing"], M["time_steps"]
    rpm_h = M["conversion"]["rpm"]
    r = L["vertical_descent_mps"]
    dh = h_now - M["atmosphere"]["pad_altitude_m"]
    T = max(dh / (0.85 * abs(r)), 1.0)
    return M2Segment("Vertical descent", "vertical", T, ts["hover_s"], schedule(0.0),
                     schedule([(0, 0.0), (0.15, r), (0.85, r), (1, 0.0)]), schedule(90.0), schedule(rpm_h),
                     headwind_mps=0.0, power_rating=rating(M, "vertical"))


def landing_hover(M):
    return M2Segment("Landing hover", "hover", M["landing"]["landing_hover_s"], M["time_steps"]["hover_s"],
                     schedule(0.0), schedule(0.0), schedule(90.0), schedule(M["conversion"]["rpm"]),
                     headwind_mps=0.0, power_rating=rating(M, "hover"))


# ---------------------------------------------------------------------------
def fly(M, n_r=25, n_psi=36, verbose=True):
    """Fly the whole mission. Returns (log, violations, segments flown)."""
    a, ld, cr = M["atmosphere"], M["loading"], M["cruise"]
    mp = MissionPlannerV2(CFG.ROTOR, CFG.airfoil_provider, start_altitude_m=a["pad_altitude_m"],
                          fuel_kg=ld["fuel_kg"], payload_kg=ld["payload_kg"], dISA_K=a["dISA_K"],
                          reserve_fuel_kg=ld["reserve_fuel_kg"], stop_on_violation=False,
                          n_r=n_r, n_psi=n_psi, verbose=verbose)
    flown = []

    def go(seg):
        mp.run_segment(seg)
        flown.append(seg)

    for s in departure_segments(M):
        go(s)
    go(climb_segment(M, mp.h))
    V = cr["speed_mps"]
    go(rpm_change(M, "Cruise RPM reduction", V, M["climb"]["rpm"], cr["rpm"]))
    # cruise length so that the total ground distance equals range_km
    tail = [rpm_change(M, "Cruise RPM increase", V, cr["rpm"], M["descent"]["rpm"]), descent_segment(M)]
    tail += arrival_segments(M)
    rest_km = sum(seg_integral(s, 'ground') for s in tail) / 1e3
    go(cruise_segment(M, M["range_km"] - mp.x_ground / 1e3 - rest_km))
    for s in tail:
        go(s)
    go(vertical_descent(M, mp.h))
    go(landing_hover(M))
    return mp.log, mp.violations, flown


# ---------------------------------------------------------------------------
# constraint utilisation (fraction of the allowable used; <= 1 is feasible)
# ---------------------------------------------------------------------------
def utilisation(log, M):
    lim = CFG.ControlLimits()
    ac = CFG.get_default_aircraft()
    a_st = ac.wing.alpha_stall_deg
    fuel0, res = log[0]['fuel_kg'], M["loading"]["reserve_fuel_kg"]
    U = {
        "Power (P_req / (1-5 %) P_avail)":
            lambda e: e['P_req_kW'] / ((1 - lim.min_power_margin_frac) * e['P_avail_kW']),
        "Rotor stall (stalled area / 5 %)":
            lambda e: e['rotor_stall_pct'] / 100 / lim.max_stall_fraction,
        "Advancing-tip Mach (M / 0.85)":
            lambda e: e['tip_mach'] / lim.max_tip_mach,
        "Reverse flow (area / 3 %)":
            lambda e: e['reverse_pct'] / 100 / lim.max_reverse_flow_fraction,
        "Wing stall (|alpha_w| / alpha_stall)":
            lambda e: abs(e['wing_alpha_deg']) / a_st if e['V_mps'] > 10 else np.nan,
        "Collective (theta0 / limit)":
            lambda e: max(e['collective_deg'] / lim.collective_deg[1], e['collective_deg'] / lim.collective_deg[0]),
        "Pilot controls (max |stick|)":
            lambda e: max(abs(e['d_lon']), abs(e['d_lat']), abs(e['d_ped'])),
        "Nacelle rate (rate / 8 deg/s)":
            lambda e: abs(e['nacelle_rate_deg_s']) / lim.nacelle_rate_deg_s,
        "Usable fuel used (above reserve)":
            lambda e: (fuel0 - e['fuel_kg']) / (fuel0 - res),
    }
    return {k: np.array([f(e) for e in log], float) for k, f in U.items()}


def margin_table(log, U):
    """Per constraint: peak utilisation, where it occurs and the margin."""
    rows = []
    for k, u in U.items():
        if np.all(np.isnan(u)):
            continue
        i = int(np.nanargmax(u))
        e = log[i]
        rows.append(dict(constraint=k, peak=float(u[i]), margin_pct=100 * (1 - float(u[i])), t_s=e['t_s'],
                         segment=e['segment'], V=e['V_mps'], h=e['altitude_m'], nacelle=e['nacelle_deg'],
                         rpm=e['rpm']))
    rows.sort(key=lambda r: -r['peak'])
    return rows


def segment_summary(log):
    """Per segment: duration, distance, fuel, mean / peak power, mass, altitude change."""
    out, segs = [], []
    for e in log:
        if not segs or segs[-1] != e['segment']:
            segs.append(e['segment'])
    for s in segs:
        L = [e for e in log if e['segment'] == s]
        out.append(dict(segment=s, kind=L[0]['kind'], t0=L[0]['t_s'], dt=L[-1]['t_s'] - L[0]['t_s'],
                        dist_km=L[-1]['distance_km'] - L[0]['distance_km'],
                        fuel_kg=L[0]['fuel_kg'] - L[-1]['fuel_kg'],
                        P_mean=float(np.mean([e['P_req_kW'] for e in L])),
                        P_max=float(np.max([e['P_req_kW'] for e in L])),
                        P_av_min=float(np.min([e['P_avail_kW'] for e in L])),
                        h0=L[0]['altitude_m'], h1=L[-1]['altitude_m'],
                        V0=L[0]['V_mps'], V1=L[-1]['V_mps'], m0=L[0]['mass_kg'], m1=L[-1]['mass_kg'],
                        rotor_lift_pct=float(np.mean([e['rotor_lift_pct'] for e in L])),
                        feasible=all(e['feasible'] for e in L)))
    return out
