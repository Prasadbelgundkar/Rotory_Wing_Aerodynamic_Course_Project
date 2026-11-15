"""
Team 6 tiltrotor project -- ONE command that regenerates every Milestone 3 figure and table.

    python run_all_m3.py                 # everything (~20 min on a mid-range laptop)
    python run_all_m3.py --skip-mission  # re-plot the mission from the saved log (~10 min)
    python run_all_m3.py --mission inputs/my_mission.json

Run from the repository root (or anywhere: paths are resolved from this file).
Outputs go to outputs/m3/ with a FIGURES.md index (figure -> report section ->
caption with flight condition and assumptions). Order:

  1. scripts/m3/plot_final_schematic.py   Section 1.1  final schematic + component locations
  2. scripts/m3/plot_workflow.py          Section 2.2  integrated workflow diagram
  3. scripts/m3/performance_summary.py    Sections 3.1-3.3  operating points, limits, conversion summary
  4. scripts/m3/run_design_mission.py     Sections 4.1-4.4  end-to-end design mission (~7 min)
  5. scripts/m3/make_m3_tables.py         Sections 1.2-1.4, 2.1, 3.2, 3.4  tables, compliance, comparison

The aircraft is the frozen Milestone 2 configuration (src/m2/aircraft_input_m2.py,
rotor 'refined'); the mission is inputs/m3_design_mission.json. The Milestone 2
corridor map (outputs/m2/rotor_refined/corridor_grid.npz) is reused, not recomputed.
"""
import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
M3 = os.path.join(ROOT, "scripts", "m3")
ENV = dict(os.environ, MPLBACKEND="Agg", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8", M2_ROTOR="refined",
           OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


def run(label, cmd):
    print(f"\n=== {label}", flush=True)
    t0 = time.time()
    rc = subprocess.run(cmd, cwd=ROOT, env=ENV, stdin=subprocess.DEVNULL).returncode
    print(f"    exit code {rc} ({time.time() - t0:.0f} s)", flush=True)
    return rc


def main():
    ap = argparse.ArgumentParser(description="Regenerate every Milestone 3 figure and table.")
    ap.add_argument("--mission", default=None, help="mission input file (default inputs/m3_design_mission.json)")
    ap.add_argument("--skip-mission", action="store_true", help="re-plot the mission from the saved log")
    a = ap.parse_args()
    py = sys.executable
    mission = [py, os.path.join(M3, "run_design_mission.py")]
    if a.mission:
        mission += ["--mission", a.mission]
    if a.skip_mission:
        mission.append("--replot")
    steps = [
        ("Section 1.1: final schematic", [py, os.path.join(M3, "plot_final_schematic.py")]),
        ("Section 2.2: workflow diagram", [py, os.path.join(M3, "plot_workflow.py")]),
        ("Sections 3.1-3.3: performance summary and limits", [py, os.path.join(M3, "performance_summary.py")]),
        ("Sections 4.1-4.4: end-to-end design mission", mission),
        ("Sections 1.2-1.4, 2.1, 3.2, 3.4: tables, compliance, comparison", [py, os.path.join(M3, "make_m3_tables.py")]),
    ]
    t0 = time.time()
    failed = [lab for lab, cmd in steps if run(lab, cmd)]
    print(f"\nTotal {(time.time() - t0) / 60:.1f} min. Outputs: outputs/m3/ (index: outputs/m3/FIGURES.md)")
    print("All done." if not failed else f"FAILED: {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
