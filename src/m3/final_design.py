"""
final_design.py -- MILESTONE 3 DESIGN-CONCLUSION DATA (single source)
=====================================================================
The final aircraft is the Milestone 2 configuration, frozen:
src/m2/aircraft_input_m2.py (rotor 'refined', 2 x GE CT7-8A, wing / tails,
mass items, control limits, conversion paths). This file only adds what the
Milestone 3 report needs on top of it:

  REQUIREMENTS        the project requirements / targets adopted in Milestone 1
                      (src/aircraft_input.py), checked in report Section 1.4
  FINAL_CHANGES       changes after Milestone 2 (report Section 1.3)
  NEW_ASSUMPTIONS     new or modified assumptions after Milestone 2 (Section 2.1)
  REFERENCE_AIRCRAFT  published data of comparable tiltrotors (Section 3.4)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import m2.aircraft_input_m2 as CFG          # noqa: E402

M1 = CFG.M1

# ---------------------------------------------------------------------------
# Requirements / targets (Milestone 1, src/aircraft_input.py SECTION 5-6)
#   key, description, target value, unit, sense ('>=' target is a minimum, '<=' a maximum)
# ---------------------------------------------------------------------------
REQUIREMENTS = [
    ("payload", "Design payload (2 crew + 10 passengers)", M1.PAYLOAD_KG, "kg", ">="),
    ("mtow", "Maximum take-off mass", M1.GROSS_MASS_KG, "kg", "<="),
    ("hover_pad", f"OGE hover at MTOW, {M1.HOVER_REQ_ALTITUDE_M:.0f} m ISA+{M1.HOVER_REQ_DISA_K:.0f} "
                  "(max hover mass)", M1.GROSS_MASS_KG, "kg", ">="),
    ("range", "Range with design payload, fuel reserve intact", M1.RANGE_TARGET_KM, "km", ">="),
    ("cruise_speed", "Design cruise speed", M1.CRUISE_SPEED_MPS, "m/s", ">="),
    ("max_speed", "Maximum speed target (450 km/h)", M1.MAX_SPEED_TARGET_MPS, "m/s", ">="),
    ("hover_endurance", "Hover endurance at MTOW on usable fuel (above reserve)", M1.HOVER_ENDURANCE_MIN, "min",
     ">="),
    ("reserve", "Fuel reserve at landing", M1.RESERVE_FUEL_KG, "kg", ">="),
    ("power_margin", "Power margin (every mission step)", 100 * M1.MIN_POWER_MARGIN_FRAC, "%", ">="),
    ("tip_mach", "Advancing / helical tip Mach (every mission step)", M1.MAX_TIP_MACH, "-", "<="),
    ("rotor_stall", "Stalled rotor area (every mission step)", 100 * M1.MAX_STALL_FRACTION, "%", "<="),
]
MARGINAL_BAND = 0.05     # within 5 % of the target (either side) -> "marginal"
# Targets met by definition of the design point (no performance margin to judge): never "marginal"
DEFINITIONAL = ("payload", "mtow", "cruise_speed")

# ---------------------------------------------------------------------------
# Changes after Milestone 2 (report Section 1.3): (change, reason)
# ---------------------------------------------------------------------------
FINAL_CHANGES = [
    ("Rotor, wing, empennage, fuselage, nacelles, engines, mass breakdown, CG and control limits: NO CHANGE "
     "(Milestone 2 configuration frozen)",
     "The M2 corridor map, trim matrix and both transition missions closed with no limit violation; the M3 design "
     "mission (hover at 1500 m ISA+15, 1000 km) also closes with every constraint below its limit (Section 4.3), "
     "so no analysis result supports a geometry or mass change."),
    ("Engine rating per flight phase: take-off rating in hover / vertical / conversion, max-continuous "
     f"({100 * CFG.MCP_FRACTION:.0f} %) in airplane mode",
     "M2 used the take-off rating everywhere; a multi-hour mission must use the continuous rating in cruise. "
     "Cruise power (~650 kW) is far below MCP (~1760 kW at 5000 m ISA+15), so no design change follows."),
    (f"Cruise schedule fixed for the design mission: {5000:.0f} m ISA+15, 75 m/s, {CFG.LONG_RANGE_RPM:.0f} RPM",
     "Best fuel per km of the final aircraft at the M1 long-range RPM (Section 3.1); 250 RPM keeps the M1 / M2 RPM "
     "schedule unchanged."),
    (f"Reserve fuel stated consistently as {M1.RESERVE_FUEL_KG:.0f} kg",
     "The code has always used 450 kg; the Milestone 1 report text quoted 150 kg. 450 kg = about 50 min at "
     "MTOW hover power or ~1.2 h of cruise."),
]

# ---------------------------------------------------------------------------
# New or modified assumptions after Milestone 2 (report Section 2.1)
# ---------------------------------------------------------------------------
NEW_ASSUMPTIONS = [
    ("Propulsion", f"Power available = {100 * CFG.MCP_FRACTION:.0f} % of the take-off rating (max-continuous) in "
                   "airplane-mode climb / cruise / descent; full take-off rating only in helicopter mode and "
                   "conversion (< 5 min). Same density lapse, drivetrain efficiency and constant SFC "
                   f"({CFG.ENGINE_SFC_KG_PER_J * 3.6e9:.0f} g/kWh) as M2."),
    ("Mission planning", "One continuous mission from vertical take-off to vertical landing (M2: two separate legs "
                         "with an arbitrary start). Climb, cruise and vertical-descent durations are sized at run "
                         "time from the current state so the mission reaches the cruise altitude, flies the "
                         "specified ground range and lands on the pad."),
    ("Mission planning", "Constant ISA deviation (ISA+15) over the whole route; constant 5 m/s headwind aloft, "
                         "calm at the pads; payload fixed (no pickup / drop)."),
    ("Mission planning", "Longer time steps where the state changes slowly: 30 s in climb / descent, 120 s in "
                         "cruise (5 s helicopter mode, 2 s conversion as in M2); explicit Euler update of fuel, "
                         "mass, altitude and distance as in M2."),
    ("Feasibility", "Limits unchanged from M2; every limit is also reported as a utilisation (fraction of the "
                    "allowable used) so the smallest margin and its location are read off directly."),
    ("Interaction", "Unchanged: no rotor-wake / wing interference and no hover download. Side-by-side rotors do not "
                    "overlap, so rotor-rotor interference (studied for tandem rotors in the modeling project, "
                    "edgewise_bemt `external_inflow`) is also neglected. Download is the main omitted effect "
                    "(typically ~10 % of thrust for tiltrotors, Section 5.2)."),
]

# ---------------------------------------------------------------------------
# Published data of comparable tiltrotors (report Section 3.4)
#   mtow / empty [kg], rotor_d [m], wing_area [m2] (None = not found in the cited source),
#   power [kW, total installed take-off], v_max [km/h], range [km], pax
# ---------------------------------------------------------------------------
REFERENCE_AIRCRAFT = {
    "Bell XV-15": dict(mtow=5897, empty=4354, rotor_d=7.62, wing_area=15.7, power=2 * 1156, v_max=615, range=825,
                       pax=None,
                       source="helis.com Bell XV-15 database (MTOW, empty, rotor, max speed, range); Maisel et al., "
                              "NASA SP-2000-4517 (wing 169 ft2, 2 x Lycoming LTC1K-4K 1550 shp)"),
    "Leonardo AW609": dict(mtow=7620, empty=4765, rotor_d=7.9, wing_area=None, power=2 * 1447, v_max=509,
                           range=1389, pax=9,
                           source="GlobalSecurity.org AW609 specifications (MTOW, empty, rotor, 2 x PT6C-67A "
                                  "1447 kW, 275 kt, 700 nm, 9 pax)"),
    "Bell Boeing V-22": dict(mtow=24030, empty=15060, rotor_d=11.58, wing_area=35.49, power=9172, v_max=628,
                             range=935, pax=24,
                             source="aerospaceweb.org V-22 Osprey data (VTO mass, empty, rotor, wing 382 ft2, "
                                    "12,300 shp, 390 mph, 505 nm); 24 troops (Bell Boeing)"),
}
