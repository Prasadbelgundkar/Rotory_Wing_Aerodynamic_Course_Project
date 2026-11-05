# Section 1.2 -- final design table

All values are read from src/m2/aircraft_input_m2.py (frozen Milestone 2 configuration).

## Proprotors (x2, interconnected)

| Parameter | Value |
|---|---|
| Radius / diameter | 3.80 m / 7.6 m |
| Blades | 3 |
| Chord root / tip (linear taper) | 0.83 m / 0.35 m (taper 0.389) |
| Twist | linear, 12 deg root, -30 deg/R ('refined') |
| Root cut-out | 0.50 m (0.132 R) |
| Solidity (thrust-weighted) | 0.148 |
| Airfoil model | Linear (a0=5.75, Cd=0.0113+1.25*alpha^2) |
| Disk loading at MTOW | 778 N/m2 (79.4 kg/m2) |
| RPM schedule | 550 hover / conversion; airplane mode 250 (long range), 350 (to 100 m/s), 420 (dash) |
| Tip speed hover / long-range cruise | 219 / 99 m/s |
| Rotation | right rotor CCW, left rotor CW (seen from above) |

## Wing

| Parameter | Value |
|---|---|
| Area / span / AR | 39.24 m2 / 18.79 m / 9.0 |
| Mean chord / incidence | 2.09 m / 4.0 deg |
| Lift model | CL_alpha 4.92 /rad (e = 0.8), stall 15 deg, CD0 0.015 |
| Wing loading at MTOW | 1799 N/m2 (183 kg/m2) |
| Flaperons | 0.45-0.95 of semi-span, +/-20 deg |

## Empennage

| Parameter | Value |
|---|---|
| H-tail area / AR / incidence | 8.0 m2 / 4.5 / 0 deg; tail arm 6.14 m |
| Elevator | 30 % chord, +/-25 deg |
| V-tail area / AR | 6.0 m2 / 1.5; rudder 30 % chord, +/-20 deg |

## Propulsion

| Parameter | Value |
|---|---|
| Engines | 2 x GE CT7-8A turboshaft, one per tilting nacelle, cross-shafted |
| Take-off / max-continuous power | 1893 / 1628 kW each, SL ISA |
| Installed power loading | 1.90 kg/kW |
| Power lapse / drivetrain | (rho/rho0)^1.0, efficiency 0.95 |
| SFC | 280 g/kWh (constant) |

## Mass and fuel

| Parameter | Value |
|---|---|
| MTOW | 7200 kg |
| Empty mass incl. crew | 4530 kg (0.629 of MTOW) |
| Payload | 1200 kg (10 passengers) |
| Fuel capacity / reserve | 1470 kg / 450 kg (wing tanks) |
| CG at MTOW, helicopter / airplane mode | x -0.16, z +0.35 m / x -0.04, z +0.47 m from wing-root c/4 |

## Controls and limits

| Parameter | Value |
|---|---|
| Collective | -10 to 65 deg (on top of twist) |
| Cyclic theta1c / theta1s | +/-10 / +/-10 deg |
| Stick mixing (faded with sin^2 i_n) | pitch: theta1c 10 deg + elevator 25 deg; roll: diff. collective 3 deg + flaperon 20 deg; yaw: diff. theta1s 8 deg + rudder 20 deg |
| Nacelle angle / rate | 0-95 deg, 8 deg/s |
| Rotor RPM range | 250-900 |
| Feasibility limits | tip Mach <= 0.85, stalled area <= 5 %, reverse flow <= 3 %, power margin >= 5 %, wing alpha < stall |
