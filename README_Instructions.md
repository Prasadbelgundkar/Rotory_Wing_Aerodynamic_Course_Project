# Milestone 1 — Code Submission Guide

**BEMT_TEAM6 | Tiltrotor Rotor Design & Mission Planning**

---

This file is for whoever is grading our submission. It covers setup, how the code is organised, and how to reproduce every plot from our report. We've tried to make everything self-contained — it should mostly just work.

---

## Setup

Install the three dependencies from the project root:

```bash
pip install -r requirements.txt
```

Or use the setup scripts we included:
- Windows: `setup.bat`
- Mac/Linux: `bash setup.sh`

No virtual environment needed unless you prefer one.

---

## Folder Layout

```
BEMT_TEAM6/
├── src/                        <- all source code
│   ├── aircraft_input.py       <- start here — our tiltrotor design parameters
│   ├── bemt.py                 <- BEMT solver
│   ├── mission.py              <- mission planner
│   ├── rotor.py                <- blade geometry
│   ├── airfoil.py              <- airfoil models
│   ├── environment.py          <- ISA atmosphere
│   └── data/                   <- Knight & Hefner validation CSVs
├── scripts/                    <- plotting scripts (reproduce report figures)
├── tests/                      <- pytest test suite
├── requirements.txt
└── README_Instructions.md      <- this file
```

---

## Submission Checklist

### Modular source code

We split everything into separate modules — the solver doesn't know about the aircraft, the mission planner doesn't know about the airfoil model, etc. Here's exactly what each file in `src/` does:

---

#### The Backbone — these three files are the core of the whole project

**`bemt.py`** — this is the heart of everything. It takes a rotor, an airfoil, RPM, collective angle, atmospheric conditions, and an axial velocity, then solves for the induced velocity at each blade element using a root-finding loop (Brent's method). It integrates thrust and torque across the span and returns CT, CQ, CP, figure of merit for hover, and propulsive efficiency for propeller mode. One solver handles both hover and airplane-mode cruise — the only difference is what you pass in as `v_axial`. Everything in the scripts/ folder ultimately calls this.

**`mission.py`** — the mission planner engine. It steps through a list of mission segments (hover, climb, descent, cruise, loiter, payload drop), calls the BEMT solver at each time step to get the power required, burns fuel, tracks mass, and checks design limits at every step. If anything goes out of limits it stops and throws a `MissionInfeasibleError` with the segment name, mission time, and the exact reason — so we don't get silent failures.

**`rotor.py`** — defines the `Rotor` class. Stores blade radius, root cutout, number of blades, and the chord/twist distributions (as callable functions of r/R). Has helpers for solidity, disk area, tip speed, and tip Mach. By making chord and twist functions rather than fixed numbers, you can pass in anything — constant, linearly tapered, ideal twist — without changing the solver.

---

#### Supporting physics modules

**`environment.py`** — implements the ISA (International Standard Atmosphere) model. You give it altitude and a temperature offset (for hot-day checks), it gives back density, pressure, temperature, and speed of sound. Every script calls this before running BEMT.

**`airfoil.py`** — defines two airfoil models. `LinearAirfoil` uses the classic `Cl = a0 * alpha` with a quadratic Cd — this is what we validated against Knight & Hefner. `TableAirfoil` lets you load a full polar from tabulated data if you need measured stall behaviour. Also has the Prandtl-Glauert compressibility correction which gets applied inside the BEMT loop for elements below M = 0.7.

---

#### Configuration / input files

**`aircraft_input.py`** — this is the master configuration file for our tiltrotor design. Every design decision (rotor radius, blade count, chord and twist distributions, RPM schedule for hover vs. cruise, gross mass, fuel, power model, SFC, and design limits) lives here. None of these are hardcoded inside the solver — they all get passed in through this file. The scripts in `scripts/` import from here.

**`parameters.py`** — an alternative/earlier configuration file we used during development that still works. Defines the V-22 Osprey-inspired geometry (R = 3.8 m, extreme -45°/R twist, blended airfoils), engine data from the GE CT7-8A, and a full mission profile. Used by `run_mission.py` for the live-telemetry demo.

---

#### Runner / output scripts (inside `src/`)

**`validation.py`** — standalone validation script. Builds the Knight & Hefner test rotor (R = 0.762 m, 0 twist, constant chord), sweeps collective from 0 to 12°, compares BEMT predictions against the digitized experimental data in `src/data/`, and saves a six-panel comparison plot.

✨ **FOR FUN / BONUS: The Live Telemetry Dashboard** ✨
**`run_mission.py`** — runs a full multi-segment mission with **live matplotlib updates**. We highly recommend running this! It uses `parameters.py` for the aircraft and shows a real-time dark-mode dashboard tracking the mission segment, fuel burn, and how the auto-trimmer adjusts collective pitch on the fly as the simulation runs. It's a great way to see the physics engine working dynamically.

**`run_plots.py`** — quick sanity-check script that sweeps collective from 2 to 20° and plots CT, CQ, CP vs. collective. Useful for checking that a new rotor geometry makes physical sense before running the full mission.

**`aircraft_sizing.py`** — generates the constraint analysis (T/W vs. W/S) plot used for airplane-mode wing/power sizing. Plots the design space boundaries for cruise, climb, turn, ceiling, stall, and glide conditions and marks our chosen design point.



### Aircraft configuration file
**`src/aircraft_input.py`** is the single place where the tiltrotor is defined — radius, number of blades, chord/twist distributions, RPM schedule, masses, power plant, design limits. We didn't hardcode any of these inside the solver; they all flow in as function arguments.

### Validation data
The digitized Knight & Hefner (1937) data we used to validate the hover model is in `src/data/`:
- `knight_hefner_2blade.csv` — 2-blade rotor test points
- `knight_hefner_3blade.csv` — 3-blade rotor test points
- `knight_hefner_4blade.csv` — 4-blade rotor test points

### Scripts reproduce all plots / tables
Every figure in the report comes from one of these scripts. Run them from the project root directory:

| Report Section | Script to run |
|---|---|
| §3 — Hover validation vs. K&H | `python scripts/plot_validation.py` |
| §4.1 — Solidity study | `python scripts/solidity_physics_study.py` |
| §4.2 — Taper ratio study | `python scripts/taper_ratio_study.py` |
| §4.3 — Twist study | `python scripts/twist_study.py` |
| §6.1 — Hover operating maps | `python scripts/plot_hover_maps.py` |
| §6.2 — Axial / propeller mode | `python scripts/plot_axial_flight.py` |
| §6.3 — Benchmarking vs. XV-15/V-22 | `python scripts/plot_benchmarking.py` |
| §7.1 — Mission planner verification | `python scripts/plot_mission_verification.py` |
| §7.2 — Hover fuel burn | `python scripts/plot_hover_fuel_burn.py` |
| §7.3 — Hover endurance vs. fuel | `python scripts/plot_hover_endurance.py` |
| §7.4 — Cruise range vs. airspeed | `python scripts/plot_cruise_range.py` |

Each script is self-contained — it imports from `src/`, does its computation, and opens a matplotlib window.

### Convergence / non-physical input checks
Two places where this matters:

1. **BEMT solver (`src/bemt.py`)** — the BET/momentum residual is non-monotonic so a simple two-point bracket fails sometimes. We scan across a range of induced velocities first to find an actual sign change, then hand that bracket to Brent's method. If no root is found the element sets `converged=False` and the rotor result does the same, so the caller knows not to trust that operating point.

2. **Mission planner (`src/mission.py`)** — at every time step we check: tip Mach < 0.85, stalled blade fraction < 5%, power margin > 5%, RPM within limits, collective within limits, fuel above reserve. If any of these is violated it raises a `MissionInfeasibleError` that tells you which segment failed, at what mission time, and why.

### Run the test suite
```bash
python -m pytest tests/test_bemt.py -v
```
The tests cover ISA accuracy, airfoil models (linear and tabulated), tip/root loss factors, hover and propeller-mode BEMT physics, all the mission planner failure modes, and rotor geometry helpers. Should be ~30+ tests all passing green.

---

## If Something Doesn't Work

Most likely cause: running the scripts from inside the `scripts/` folder instead of the project root. Always `cd` to the top-level folder first, then `python scripts/plot_validation.py` etc.

If you get a missing module error, make sure you ran `pip install -r requirements.txt` from the same Python interpreter you're running the scripts with.
