# Section 2.1 -- new or modified assumptions after Milestone 2

Unchanged assumptions (rigid disk, linear airfoil with stall flag, annular-Glauert inflow, airframe model, limits) are not repeated; see docs/milestone2/Milestone_2_Architecture.md.

| Area | Assumption (new or modified) |
|---|---|
| Propulsion | Power available = 86 % of the take-off rating (max-continuous) in airplane-mode climb / cruise / descent; full take-off rating only in helicopter mode and conversion (< 5 min). Same density lapse, drivetrain efficiency and constant SFC (280 g/kWh) as M2. |
| Mission planning | One continuous mission from vertical take-off to vertical landing (M2: two separate legs with an arbitrary start). Climb, cruise and vertical-descent durations are sized at run time from the current state so the mission reaches the cruise altitude, flies the specified ground range and lands on the pad. |
| Mission planning | Constant ISA deviation (ISA+15) over the whole route; constant 5 m/s headwind aloft, calm at the pads; payload fixed (no pickup / drop). |
| Mission planning | Longer time steps where the state changes slowly: 30 s in climb / descent, 120 s in cruise (5 s helicopter mode, 2 s conversion as in M2); explicit Euler update of fuel, mass, altitude and distance as in M2. |
| Feasibility | Limits unchanged from M2; every limit is also reported as a utilisation (fraction of the allowable used) so the smallest margin and its location are read off directly. |
| Interaction | Unchanged: no rotor-wake / wing interference and no hover download. Side-by-side rotors do not overlap, so rotor-rotor interference (studied for tandem rotors in the modeling project, edgewise_bemt `external_inflow`) is also neglected. Download is the main omitted effect (typically ~10 % of thrust for tiltrotors, Section 5.2). |
