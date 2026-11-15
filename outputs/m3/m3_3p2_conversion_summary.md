# Section 3.2 -- conversion summary (Milestone 2 corridor map, reused)

Map: 2000 m ISA (rho = 1.007 kg/m3, the same density as the 1500 m ISA+15 design pads to within 0.3 %), 7200 kg, 550 RPM, steady level flight, 6-DOF trim at every point. Not recomputed: the rotor, airframe and mass of the final design are those of Milestone 2.

| Nacelle [deg] | Min feasible V [m/s] | Max feasible V [m/s] | Limit just below V_min | Limit just above V_max | Infeasible speeds inside the band |
|---|---|---|---|---|---|
| 0.0 | 55 | 100 | no_physical_solution | - | - |
| 7.5 | 55 | 100 | excessive_residual | - | - |
| 15.0 | 50 | 100 | no_physical_solution | - | - |
| 22.5 | 50 | 85 | no_physical_solution | rotor_stall | - |
| 30.0 | 50 | 65 | no_physical_solution | rotor_stall | - |
| 37.5 | 50 | 60 | no_physical_solution | rotor_stall | - |
| 45.0 | 45 | 60 | no_physical_solution | rotor_stall | - |
| 52.5 | 45 | 65 | wing_stall | rotor_stall | - |
| 60.0 | 45 | 70 | wing_stall | rotor_stall | - |
| 67.5 | 0 | 65 | - | tip_mach | 15, 20, 25, 30, 35 |
| 75.0 | 0 | 65 | - | tip_mach | 15, 20 |
| 82.5 | 0 | 60 | - | tip_mach | - |
| 90.0 | 0 | 35 | - | rotor_stall | - |

Recommended conversion path (V [m/s], nacelle [deg]): (0, 90), (10, 90), (20, 85), (30, 80), (40, 75), (50, 60), (55, 45), (60, 30), (65, 15), (70, 0).
Recommended reconversion path: (0, 90), (12, 90), (25, 92), (35, 90), (42, 85), (48, 72), (54, 55), (60, 35), (65, 15), (70, 0) (nacelles tilted back earlier, slightly beyond vertical at 25-35 m/s, so the rotors decelerate the aircraft instead of a nose-up attitude that stalls the wing).

