# Evaluation Guide (for TAs)

Team 6 tiltrotor project: BEMT rotor tool, 6-DOF trim, conversion corridor and Mission Planners v1/v2
(Milestones 1 and 2). **Every graded figure and table is already committed under `outputs/`**, so the results
can be checked without running anything; the commands below regenerate them.

All commands are run from the repository root.

---

## 1. Setup (≈ 2 min)

```bash
git clone https://github.com/Prasadbelgundkar/Rotory_Wing_Aerodynamic_Course_Project.git
cd Rotory_Wing_Aerodynamic_Course_Project
pip install -r requirements.txt      # or: setup.bat (Windows) / ./setup.sh (macOS, Linux)
```

Python 3.10 or newer (tested on 3.13). Any 64-bit laptop with 2+ cores and 4 GB RAM is enough.

---

## 2. Five-minute check

| # | Do this | Expected |
|---|---|---|
| 1 | `python -m pytest` | `105 passed` (≈ 70 s): M1 solver + M2 regression tests on the design rotor |
| 2 | open `outputs/m1/knight_hefner_multi_blade_validation.png` | BEMT vs Knight & Hefner (1937), 2/3/4 blades; regenerate with `python src/validation.py` (≈ 6 s) |
| 3 | open `outputs/m2/rotor_refined/FIGURES.md` | index of every Milestone 2 figure → report section → caption (flight condition + assumptions) |
| 4 | `python bonus_simulation_transition_analysis/run_transition_simulation.py`, then open the printed HTML file in a browser and press **Play** | interactive 3D replay of the hover → airplane conversion (bonus) |

---

## 3. Full reproduction

### Milestone 2 — one command

```bash
python scripts/m2/run_all_m2.py                          # tests + every M2 figure/table, design rotor (≈ 10 min)
python scripts/m2/run_all_m2.py --variants refined M1    # also the Milestone 1 blade for Section 9.2 (≈ 20 min)
python scripts/m2/run_all_m2.py --recompute-corridor     # also re-solve the 273-point corridor map (+ 5–11 min)
```

Results go to `outputs/m2/rotor_<variant>/`; file names start with the report section
(`m2_6p2_trim_table.md` = Section 6.2). The M2 tests on the Milestone 1 blade:
`M2_ROTOR=M1 python -m pytest tests/m2` (bash) or `$env:M2_ROTOR="M1"; python -m pytest tests/m2`
(PowerShell) → `40 passed` (≈ 45 s).

### Milestone 1 — one script per figure group

Each script writes to `outputs/m1/`; they take between 1 s and ≈ 80 s each (≈ 10 min for the whole list), and
reproduce the committed figures.

```bash
python src/validation.py                          # Section 3: Knight & Hefner validation
python scripts/m1/plot_design_study.py            # Section 4: chord/solidity, blade number, taper, twist, root cut-out
python scripts/m1/solidity_physics_study.py
python scripts/m1/taper_ratio_study.py
python scripts/m1/twist_study.py
python src/aircraft_sizing.py                     # Section 5: sizing / constraint analysis
python scripts/m1/standalone_hover_plots.py       # Section 6.1: hover maps and ceiling
python scripts/m1/plot_hover_maps.py
python scripts/m1/plot_hover_envelope.py
python scripts/m1/plot_axial_flight.py            # Section 6.2: airplane-mode (axial) performance
python scripts/m1/plot_efficiency_map.py
python scripts/m1/fm_vs_ct_tiltrotor.py           # Section 6.3: comparison with other rotors
python scripts/m1/plot_benchmarking.py
python scripts/m1/verify_mission_planner.py       # Section 7.1: Mission Planner v1 verification
python scripts/m1/plot_mission_verification.py
python scripts/m1/mission_tests/run_all_evaluations.py
python scripts/m1/plot_hover_fuel_burn.py         # Section 7.2
python scripts/m1/plot_hover_endurance.py         # Section 7.3
python scripts/m1/plot_cruise_range.py            # Section 7.4
python scripts/m1/plot_mission_analysis.py        # Sections 7.2-7.4 from full mission runs
```

---

## 4. Where each report section comes from

### Milestone 1

| Section | Code / input | Output (`outputs/m1/`) and write-up |
|---|---|---|
| 1 Starting assumptions | `src/environment.py` (ISA), `src/airfoil.py`, `src/aircraft_input.py`, `src/parameters.py` | `docs/milestone1/formulas.md` |
| 2 Algorithm and logic | `src/bemt.py`, `src/mission.py` | `docs/milestone1/algorithm_flow.md`, `bemt_flow.md`, `mission_planner_flow.md` |
| 3 BEMT validation | `src/validation.py`, data `src/data/knight_hefner_*.csv` | `knight_hefner_multi_blade_validation.png`; `docs/milestone1/Validation_Report.md` |
| 4 Design-variable study | `scripts/m1/plot_design_study.py`, `solidity_physics_study.py`, `taper_ratio_study.py`, `twist_study.py` | `design_study_*.png`, `solidity_physics_*.png`, `taper_study_*.png`, `twist_study_*.png` |
| 5 Tiltrotor aircraft | `src/aircraft_input.py`, `src/aircraft_sizing.py` | `constraint_analysis.png`; `docs/milestone1/Design_Sizing_Report.md` |
| 6.1 Hover | `standalone_hover_plots.py`, `plot_hover_maps.py`, `plot_hover_envelope.py` | `hover_map_*.png`, `hover_ceiling.png`, `hover_max_weight_vs_altitude.png`, `hover_operating_envelope.png` |
| 6.2 Axial flight | `plot_axial_flight.py`, `plot_efficiency_map.py` | `axial_flight_*.png`, `axial_efficiency_map.png` |
| 6.3 Comparable rotors | `fm_vs_ct_tiltrotor.py`, `plot_benchmarking.py` | `fm_vs_ct_tiltrotor.png`, `benchmarking_CT_CP_FM.png` |
| 7.1 Mission Planner v1 | `src/mission.py`, `verify_mission_planner.py`, `plot_mission_verification.py`, `mission_tests/` | `mission_verification_results.md`, `mission_verification_plots.png` |
| 7.2–7.4 Fuel burn, endurance, range | `plot_hover_fuel_burn.py`, `plot_hover_endurance.py`, `plot_cruise_range.py`, `plot_mission_analysis.py` | `hover_fuel_burn_rate.png`, `hover_endurance_vs_weight.png`, `cruise_range_vs_speed.png`, `mission_*.png` |
| 6–7 write-ups | — | `docs/milestone1/reports/` |

### Milestone 2 (`outputs/m2/rotor_refined/`; the `rotor_M1/` folder repeats it for the Milestone 1 blade)

| Section | Script (`scripts/m2/`) | Outputs |
|---|---|---|
| 2 Algorithms and logic | — | `docs/milestone2/Milestone_2_Architecture.md` |
| 3.1–3.4 Edgewise BEMT verification | `verify_edgewise.py` | `m2_3p*_*.png`, `m2_3_summary.md`, `m2_3p1_m1_recovery_table.md`, `m2_3p3_boundaries_table.md`, `m2_3p4_grid_sensitivity.md` |
| 4 Rotor control sweeps | `demo_rotor_control_sweep.py` | `m2_4p1`–`m2_4p3_*.png`, `m2_4_control_derivatives.md` |
| 5.1 Aircraft schematic | `plot_aircraft_schematic.py` | `m2_5p1_aircraft_schematic.png` |
| 5.2 Engine selection | `engine_selection.py` | `m2_5_engine_selection.md`, `m2_5p2_engine_selection.png` |
| 5.2–5.5 Design tables | `make_design_tables.py` | `m2_5_design_tables.md`, `m2_5p3_blade_distributions.png` |
| 6.1, 6.2, 6.4 Trim matrix | `demo_trim_matrix.py` | `m2_6p2_trim_table.md` / `.csv`, `m2_6p4_trim_trends.png`, `m2_6p4_lift_sharing.png` |
| 6.3 Failed trim cases | `demo_failed_trim.py` | `m2_6p3_failed_trim.md`, `m2_6p3_failed_trim.png` |
| 7.1, 7.2 Conversion corridor | `demo_corridor_map.py` | `m2_7p1_conversion_corridor.png`, `m2_7p2_constraint_boundaries.png`, `m2_7_corridor_summary.md` |
| 8.1, 8.2 Transition missions | `demo_transition_mission.py` | `m2_8p1_mission_definition.md`, `m2_8p2_*.png`, `m2_8_mission_summary.md`, `m2_8_*_log.csv` |
| 9.1, 9.2 Comparison with M1 | `compare_m1_m2.py` | `m2_9_comparison.md`, `m2_9p1_power_comparison.png` |
| 10.1 Figure index | — | `FIGURES.md` (captions with flight condition and assumptions) |
| Bonus | `bonus_simulation_transition_analysis/run_transition_simulation.py` | interactive HTML in `bonus_simulation_transition_analysis/output/` |

---

## 5. Submission-requirement checklist

| Requirement (assignment brief) | Where |
|---|---|
| README instructions | `README.md`, this guide |
| Environment / dependency file | `requirements.txt`, `setup.bat`, `setup.sh` |
| Aircraft configuration file | `src/aircraft_input.py` (M1), `src/m2/aircraft_input_m2.py` (M2: single source of truth) |
| Input examples | `examples/`, mission segments in `scripts/m2/demo_transition_mission.py` and `scripts/m1/mission_tests/` |
| Validation data | `src/data/knight_hefner_*.csv` |
| Scripts reproducing all graded plots and tables | Section 3 above (`scripts/m1/`, `scripts/m2/run_all_m2.py`) |
| Captions with flight condition and assumptions | `outputs/m2/rotor_<variant>/FIGURES.md` |
| Modular functions / classes | atmosphere `environment.py`; airfoil `airfoil.py`; blade geometry `rotor.py`; inflow, blade-element loads and rotor integration `bemt.py`, `m2/edgewise_bemt.py`; trim `m2/trim_6dof.py`; propulsion `PowerAvailableModel` / `FuelModel` in `mission.py`; mission segments `mission.py`, `m2/mission_v2.py` |
| Sign conventions and reference frames | `README.md` (Conventions), `src/m2/frames.py`, `docs/milestone2/Milestone_2_Architecture.md` |
| Checks for non-physical inputs / failed convergence | `ValueError` on out-of-range altitude (`environment.isa`) and degenerate rotor geometry (`Rotor.solidity`); `converged` flag per element and rotor (`bemt.py`); trim status and limit flags (`m2/trim_6dof.py`, classified in Section 6.3); `MissionInfeasibleError` with the first violated constraint (`mission.py`) |
| No hard-coded aircraft or mission | geometry, operating condition, controls and mission segments are inputs (configuration files above; `M2Segment` schedules) |
| References and acknowledgement | in the reports (Milestone 1: Section 8); `README.md` (Acknowledgement) |

---

## 6. Assumptions and limitations

Summarised in `README.md` → *Conventions and assumptions*; full detail in
`docs/milestone2/Milestone_2_Architecture.md` and `docs/milestone1/Validation_Report.md`. Main ones: rigid
rotor disk (no flapping), quasi-steady linear airfoil with a stall flag, no dynamic stall, no rotor-wake /
wing interference and no hover download.

## 7. Rotor variant

Milestone 2 uses the refined blade by default. Set `M2_ROTOR=M1` (bash `export`, PowerShell `$env:`, cmd
`set`) to run any Milestone 2 script or test on the Milestone 1 blade; results go to `outputs/m2/rotor_M1/`.
