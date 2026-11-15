# Section 3.2 -- tightest constraint during conversion / reconversion (design mission)

## Conversion

| Constraint | Peak utilisation | Margin | V [m/s] | Nacelle [deg] |
|---|---|---|---|---|
| Advancing-tip Mach (M / 0.85) | 0.909 | 9.1 % | 51 | 56 |
| Rotor stall (stalled area / 5 %) | 0.743 | 25.7 % | 61 | 26 |
| Power (P_req / (1-5 %) P_avail) | 0.699 | 30.1 % | 5 | 90 |
| Collective (theta0 / limit) | 0.569 | 43.1 % | 70 | 0 |
| Wing stall (|alpha_w| / alpha_stall) | 0.568 | 43.2 % | 70 | 0 |
| Pilot controls (max |stick|) | 0.398 | 60.2 % | 70 | 0 |
| Nacelle rate (rate / 8 deg/s) | 0.309 | 69.1 % | 51 | 56 |
| Reverse flow (area / 3 %) | 0.154 | 84.6 % | 47 | 65 |

Tightest: **Advancing-tip Mach (M / 0.85)**, 9.1 % margin at V = 51 m/s, nacelle 56 deg.

## Reconversion

| Constraint | Peak utilisation | Margin | V [m/s] | Nacelle [deg] |
|---|---|---|---|---|
| Advancing-tip Mach (M / 0.85) | 0.919 | 8.1 % | 52 | 60 |
| Rotor stall (stalled area / 5 %) | 0.907 | 9.3 % | 61 | 31 |
| Wing stall (|alpha_w| / alpha_stall) | 0.794 | 20.6 % | 10 | 90 |
| Power (P_req / (1-5 %) P_avail) | 0.606 | 39.4 % | 0 | 90 |
| Collective (theta0 / limit) | 0.562 | 43.8 % | 70 | 0 |
| Pilot controls (max |stick|) | 0.350 | 65.0 % | 23 | 92 |
| Nacelle rate (rate / 8 deg/s) | 0.317 | 68.3 % | 64 | 21 |
| Reverse flow (area / 3 %) | 0.260 | 74.0 % | 51 | 64 |

Tightest: **Advancing-tip Mach (M / 0.85)**, 8.1 % margin at V = 52 m/s, nacelle 60 deg.
