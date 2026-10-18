"""
Team 6 Modeling Project (tandem-rotor interference) -- ONE command that regenerates every
figure, table and validation result shown in the slide deck.

    python run_all_mp.py

Run it from the repository root (or anywhere: paths are resolved from this file). It runs, in order:

  1. the tandem-interference unit tests (verification: limits, baseline recovery, convergence)
  2. the integrated tool figures (BEMT + interference switch none / coleman / fvw)
  3. the standalone free-vortex wake figures (two-way FVW cross-check)

and writes everything to outputs/mp/. modeling_project/README.md says which output goes on
which slide. Runtime on a laptop: about 2-4 min, from the cached free-vortex wake maps.

Optional flags:
    --skip-tests        figures only
    --recompute-fvw     first re-run the free-vortex wake cases themselves (needs numba, ~1 h),
                        overwriting the cached maps in src/data/fvw/
"""
import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
MP = os.path.join(ROOT, "scripts", "mp")
OUT = os.path.join(ROOT, "outputs", "mp")

BASE_ENV = dict(os.environ, MPLBACKEND="Agg", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")

TESTS = ["tests/test_tandem_interference.py", "tests/test_tandem_forward_flight.py"]
FVW_CASES = [("ch47", "0.05,0.10,0.15,0.20,0.25"), ("dingeldein", "0.11,0.145,0.19,0.24,0.295")]
PIPELINE = [
    ("plot_tandem_validation.py", "Validation: integrated tool vs Dingeldein NACA TN-3236 Fig. 6"),
    ("plot_tandem_forward_flight.py", "Assessment: CH-47 forward-flight sweep, baseline vs Coleman vs FVW"),
    ("plot_tandem_hover_assessment.py", "Assessment: CH-47 hover, SL ISA and hot-and-high"),
    ("plot_tandem_parameter_study.py", "Assessment: hover parameter study"),
    ("plot_fvw_standalone.py", "Standalone free-vortex wake: convergence, TN-3236 check, aft inflow, power"),
]
# file -> slide of Team6_Tandem_Rotor_Interference.pptx it appears on
DECK = [
    ("ch47_convergence.png", "Validation (1/3): code verification"),
    ("dingeldein_validation.png", "Validation (2/3): standalone free-vortex wake vs TN-3236"),
    ("tandem_validation_dingeldein.png", "Validation (3/3): integrated tool vs TN-3236"),
    ("tandem_validation_table.md", "Validation (3/3): numbers quoted on the slide"),
    ("tandem_forward_flight.png", "Rotorcraft assessment (1/4): forward flight"),
    ("tandem_forward_flight_table.md", "Rotorcraft assessment (1/4): numbers quoted on the slide"),
    ("ch47_aft_inflow.png", "Rotorcraft assessment (2/4): why the aft rotor pays"),
    ("ch47_power.png", "Rotorcraft assessment (3/4): tool vs standalone two-way free wake"),
    ("tandem_hover_assessment.png", "Rotorcraft assessment (4/4): hover"),
    ("tandem_parameter_study.png", "Rotorcraft assessment (4/4): layout study"),
]


def run(label, cmd):
    print(f"\n=== {label}", flush=True)
    t0 = time.time()
    rc = subprocess.run(cmd, cwd=ROOT, env=BASE_ENV, stdin=subprocess.DEVNULL).returncode
    print(f"    exit code {rc} ({time.time() - t0:.0f} s)", flush=True)
    return rc


def main():
    ap = argparse.ArgumentParser(description="Regenerate every Modeling Project figure and table.")
    ap.add_argument("--skip-tests", action="store_true")
    ap.add_argument("--recompute-fvw", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    t_start = time.time()
    failures = []

    if not a.skip_tests:
        if run("pytest: tandem interference, hover + forward flight", [sys.executable, "-m", "pytest", "-q"] + TESTS):
            failures.append("pytest")
    if a.recompute_fvw:
        for cfg, mus in FVW_CASES:
            if run(f"free-vortex wake: {cfg} at mu = {mus}",
                   [sys.executable, os.path.join(ROOT, "src", "tandem_fvw.py"), cfg, mus]):
                failures.append(f"tandem_fvw.py {cfg}")
    for script, what in PIPELINE:
        if run(f"{script}: {what}", [sys.executable, os.path.join(MP, script)]):
            failures.append(script)

    print("\n=== Deck outputs (outputs/mp/)")
    for f, where in DECK:
        p = os.path.join(OUT, f)
        fresh = os.path.exists(p) and os.path.getmtime(p) >= t_start
        print(f"  [{'regenerated' if fresh else 'MISSING / stale':>15}] {f:34s} -> {where}")
        if not fresh:
            failures.append(f)
    print(f"\nTotal time {time.time() - t_start:.0f} s")
    print("All done." if not failures else f"FAILED: {', '.join(failures)}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
