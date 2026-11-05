# Section 4.1 -- design mission definition: Hot-and-high 1000 km passenger transport

10 passengers (1200 kg) from a 1500 m elevation pad to another 1500 m pad 1000 km away, ISA+15 (the Milestone 1 hover-sizing day), constant headwind aloft, calm at the pads.

| Item | Value |
|---|---|
| Aircraft | final design (frozen M2 configuration), rotor 'refined', 2 x GE CT7-8A |
| Take-off mass | 7200 kg (MTOW 7200 kg) |
| Payload | 1200 kg (10 passengers), carried throughout |
| Fuel at take-off / reserve | 1470 kg / 450 kg (must remain at landing) |
| Pads (take-off and landing) | 1500 m, ISA+15 K |
| Wind | 5 m/s headwind aloft (whole route), calm at the pads |
| Range (ground distance) | 1000 km |
| Cruise | 5000 m ISA+15, 75 m/s TAS, 250 RPM (long-range) |
| Climb / descent | +5 / -5 m/s at 75 m/s, 350 RPM |
| Conversion schedule | 0 -> 70 m/s in 100 s along [(0.0, 90.0), (10.0, 90.0), (20.0, 85.0), (30.0, 80.0), (40.0, 75.0), (50.0, 60.0), (55.0, 45.0), (60.0, 30.0), (65.0, 15.0), (70.0, 0.0)] (V, i_n), 550 RPM |
| Reconversion schedule | 70 -> 0 m/s in 130 s along [(0.0, 90.0), (12.0, 90.0), (25.0, 92.0), (35.0, 90.0), (42.0, 85.0), (48.0, 72.0), (54.0, 55.0), (60.0, 35.0), (65.0, 15.0), (70.0, 0.0)] |
| Engine rating | take-off rating in hover / vertical / conversion; max-continuous (86 %) in airplane mode |
| Controls | online 6-DOF trim at every time step (no scheduled controls) |

Segments as flown (climb, cruise and vertical-descent durations sized at run time):

| # | Segment | Type | Duration [s] | dt [s] | Airspeed [m/s] | Altitude change [m] | Nacelle [deg] | RPM | Headwind [m/s] | Engine rating |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Take-off hover | hover | 60 | 5 | 0 -> 0 | +0 | 90 -> 90 | 550 -> 550 | 0 | TO |
| 2 | Vertical climb | vertical | 60 | 5 | 0 -> 0 | +128 | 90 -> 90 | 550 -> 550 | 0 | TO |
| 3 | Conversion | conversion | 100 | 2 | 0 -> 70 | +68 | conversion path n(V) | 550 -> 550 | 5 | TO |
| 4 | Accel. + RPM reduction | airplane | 60 | 5 | 70 -> 75 | +45 | 0 -> 0 | 550 -> 350 | 5 | MCP (86 %) |
| 5 | Climb to cruise | climb | 682 | 30 | 75 -> 75 | +3259 | 0 -> 0 | 350 -> 350 | 5 | MCP (86 %) |
| 6 | Cruise RPM reduction | cruise | 60 | 5 | 75 -> 75 | +0 | 0 -> 0 | 350 -> 250 | 5 | MCP (86 %) |
| 7 | Cruise | cruise | 12593 | 120 | 75 -> 75 | +0 | 0 -> 0 | 250 -> 250 | 5 | MCP (86 %) |
| 8 | Cruise RPM increase | cruise | 60 | 5 | 75 -> 75 | +0 | 0 -> 0 | 250 -> 350 | 5 | MCP (86 %) |
| 9 | Descent | descent | 674 | 30 | 75 -> 75 | -3220 | 0 -> 0 | 350 -> 350 | 5 | MCP (86 %) |
| 10 | Decel. + RPM increase | airplane | 60 | 5 | 75 -> 70 | -45 | 0 -> 0 | 350 -> 550 | 5 | MCP (86 %) |
| 11 | Reconversion | conversion | 130 | 2 | 70 -> 0 | -57 | reconversion path n(V) | 550 -> 550 | 5 | TO |
| 12 | Hover | hover | 30 | 5 | 0 -> 0 | +0 | 90 -> 90 | 550 -> 550 | 0 | TO |
| 13 | Vertical descent | vertical | 143 | 5 | 0 -> 0 | -182 | 90 -> 90 | 550 -> 550 | 0 | TO |
| 14 | Landing hover | hover | 30 | 5 | 0 -> 0 | +0 | 90 -> 90 | 550 -> 550 | 0 | TO |
