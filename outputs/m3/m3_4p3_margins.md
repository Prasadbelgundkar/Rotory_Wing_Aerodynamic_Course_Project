# Section 4.3 -- limit margins along the mission

392 trimmed time steps, 0 limit violations. Utilisation = fraction of the allowable value used (<= 1 feasible); margin = 1 - utilisation.

| Constraint | Peak utilisation | Minimum margin | Segment | Time [min] | V [m/s] | Altitude [m] | Nacelle [deg] | RPM |
|---|---|---|---|---|---|---|---|---|
| Collective (theta0 / limit) | 0.961 | 3.9 % | Cruise RPM reduction | 16.9 | 75 | 4998 | 0 | 250 |
| Advancing-tip Mach (M / 0.85) | 0.919 | 8.1 % | Reconversion | 240.8 | 52 | 1714 | 60 | 550 |
| Rotor stall (stalled area / 5 %) | 0.907 | 9.3 % | Reconversion | 240.6 | 61 | 1716 | 31 | 550 |
| Wing stall (|alpha_w| / alpha_stall) | 0.794 | 20.6 % | Reconversion | 241.9 | 10 | 1706 | 90 | 550 |
| Usable fuel used (above reserve) | 0.777 | 22.3 % | Landing hover | 245.7 | 0 | 1500 | 90 | 550 |
| Power (P_req / (1-5 %) P_avail) | 0.729 | 27.1 % | Vertical climb | 1.1 | 1 | 1500 | 90 | 550 |
| Pilot controls (max |stick|) | 0.484 | 51.6 % | Climb to cruise | 15.5 | 75 | 4852 | 0 | 350 |
| Nacelle rate (rate / 8 deg/s) | 0.317 | 68.3 % | Reconversion | 240.5 | 64 | 1718 | 21 | 550 |
| Reverse flow (area / 3 %) | 0.260 | 74.0 % | Reconversion | 240.8 | 51 | 1714 | 64 | 550 |

**Minimum margin:** Collective (theta0 / limit) -- 3.9 % margin in segment 'Cruise RPM reduction' at t = 16.9 min (V = 75 m/s, h = 4998 m, nacelle 0 deg, 250 RPM).
