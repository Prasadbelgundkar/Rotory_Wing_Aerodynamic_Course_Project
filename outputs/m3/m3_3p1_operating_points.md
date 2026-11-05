# Section 3.1 -- hover and airplane-mode operating points (final design)

6-DOF trim of the complete aircraft; final design: rotor 'refined' (twist 12 deg root, -30 deg/R), 2 x GE CT7-8A; 6-DOF trim with rigid-disk azimuth-resolved BEMT (annular-Glauert inflow + K-factor, linear airfoil, stall 14 deg), no rotor-wake/wing interference or hover download. Fuel flow with SFC 280 g/kWh. Power available: take-off rating in hover, max-continuous (86 %) in airplane mode; drivetrain efficiency 0.95 and density lapse included.

| Hover (OGE, MTOW 7200 kg) | rho [kg/m3] | RPM | Collective [deg] | Thrust / rotor [kN] | P_req / P_avail (TO) [kW] | Power margin | Figure of merit | Power loading [kg/kW] | Tip Mach | Stalled area | Fuel flow [kg/h] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Sea level ISA | 1.225 | 550 | 22.9 | 35.3 | 1762 / 3597 | 51 % | 0.714 | 4.09 | 0.645 | 0.0 % | 493 |
| Design pads 1500 m ISA+15 | 1.004 | 550 | 25.0 | 35.3 | 1909 / 2948 | 35 % | 0.728 | 3.77 | 0.640 | 0.0 % | 535 |
| 2000 m ISA (M2 reference) | 1.006 | 550 | 24.9 | 35.3 | 1903 / 2955 | 36 % | 0.730 | 3.78 | 0.661 | 0.0 % | 533 |

| Airplane mode (7200 kg, nacelle 0) | Altitude | TAS [m/s] | RPM | Advance ratio J = V/(nD) | Collective [deg] | Total rotor thrust [kN] | Wing lift share | Wing alpha [deg] | P_req / P_avail (MCP) [kW] | Propulsive eff. TV/P | Effective L/D = WV/P | Fuel [kg/km, still air] | Helical tip Mach | Feasible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Long-range cruise (design mission) | 5000 m ISA+15 | 75 (270 km/h) | 250 | 2.37 | 62.5 | 7.37 | 90 % | 9.9 | 663 / 1756 | 0.835 | 8.0 | 0.687 | 0.398 | yes |
| Cruise, higher RPM | 5000 m ISA+15 | 85 (306 km/h) | 350 | 1.92 | 55.2 | 8.38 | 92 % | 8.0 | 900 / 1756 | 0.791 | 6.7 | 0.824 | 0.511 | yes |
| High-speed cruise | 3000 m ISA+15 | 100 (360 km/h) | 350 | 2.26 | 59.9 | 12.27 | 96 % | 5.1 | 1501 / 2174 | 0.817 | 4.7 | 1.168 | 0.514 | yes |
| Dash | 3000 m ISA+15 | 110 (396 km/h) | 420 | 2.07 | 57.0 | 14.43 | 98 % | 4.4 | 2002 / 2174 | 0.793 | 3.9 | 1.416 | 0.596 | yes |

Best-range (minimum fuel per km, still air) speed at the cruise altitude, mid-cruise mass 6800 kg:

* 250 RPM: 60 m/s, 0.624 kg/km; highest feasible speed 80 m/s (above: collective at its limit)
* 300 RPM: 60 m/s, 0.652 kg/km; highest feasible speed 100 m/s (above: collective at its limit)
* 350 RPM: 60 m/s, 0.680 kg/km; highest feasible speed 110 m/s (above: power limitation (1746 kW required, 1756 kW available))
