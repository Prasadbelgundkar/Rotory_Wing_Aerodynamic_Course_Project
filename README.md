# Tiltrotor BEMT + Mission Planner — Milestone 1

Our BEMT rotor-performance tool and Mission Planner for the tiltrotor design project. We tried to keep things modular so each part (atmosphere, airfoil, rotor, solver, mission planner) lives in its own file and can be run or tested on its own.

## Install

```bash
pip install -r requirements.txt
```

That gets you `numpy`, `scipy`, `matplotlib`, and `pytest`. Alternatively just run `setup.bat` on Windows or `setup.sh` on Linux/Mac — both do the same thing.

## What's in `src/`

| File | What it does |
|---|---|
| `aircraft_input.py` | **Start here** — all tiltrotor design parameters (rotor geometry, masses, RPM schedule, engine, limits) live in one place |
| `environment.py` | ISA atmosphere model — density, pressure, temperature, speed of sound vs. altitude |
| `airfoil.py` | Linear and tabulated Cl/Cd models, stall flagging, Prandtl-Glauert correction |
| `rotor.py` | Blade geometry helpers — chord/twist distributions, solidity, disk area, tip speed |
| `bemt.py` | Core BEMT solver: per-element induced-velocity solve (Brent's method), Prandtl tip loss, span integration |
| `validation.py` | Hover validation against Knight & Hefner (1937) experimental data |
| `mission.py` | Mission planner — time-steps through segments, tracks fuel and mass, checks design limits |
| `run_mission.py` | Runs a full mission with a live matplotlib display |

## Reproducing the figures

Run all scripts from the **project root** (not from inside `scripts/`):

```bash
# Validation against Knight & Hefner
python scripts/plot_validation.py

# Design variable studies
python scripts/solidity_physics_study.py
python scripts/taper_ratio_study.py
python scripts/twist_study.py

# Rotor operating maps
python scripts/plot_hover_maps.py
python scripts/plot_axial_flight.py
python scripts/plot_benchmarking.py

# Mission planner
python scripts/plot_mission_verification.py
python scripts/plot_hover_endurance.py
python scripts/plot_cruise_range.py

# ✨ For Fun: Live Mission Telemetry Dashboard ✨
python src/run_mission.py
```

Each script imports from `src/` and pops up a matplotlib window.

## Running the tests

```bash
python -m pytest tests/test_bemt.py -v
```

Covers ISA values, airfoil models, tip/root loss, hover and propeller-mode BEMT physics, all the mission planner failure modes, and rotor geometry. Should all pass.

## Modeling choices and limitations

- We used the linear airfoil model (`Cl = a0 * alpha`, quadratic Cd) because it matches the Knight & Hefner validation rotor reasonably well. Past stall (~14 deg for our design), Cl is clipped and Cd is inflated — it's a rough approximation but the design generally avoids heavy stall.
- Prandtl-Glauert correction is only applied below M = 0.7 — above that the correction breaks down, so we flag the tip Mach limit instead.
- BEMT assumes axisymmetric, steady inflow (no dynamic stall, no azimuthal variation, no blade flexibility), which is consistent with the scope of this milestone.
- The mission planner auto-trims collective at each time step using Brent's method to exactly hit the required thrust. RPM is fixed per segment per the schedule in `aircraft_input.py`.
