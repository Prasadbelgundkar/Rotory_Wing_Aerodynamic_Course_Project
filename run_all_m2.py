"""
Team 6 tiltrotor project -- ONE command that regenerates every Milestone 2 plot.

    python run_all_m2.py

Run it from the repository root (or anywhere: paths are resolved from this
file). It runs, in order:

  1. every Milestone 2 figure/table script,
     for both rotor variants ('refined', 'M1')  -> outputs/m2/rotor_<variant>/
  2. the bonus 3D transition simulation (HTML)  -> bonus_simulation_transition_analysis/output/

and finally prints which committed figures were regenerated. Nothing in the
existing code is changed: this file only calls the existing scripts, each in
its own process, exactly as listed in EVALUATION_GUIDE.md.

Runtime on a mid-range laptop: ~10 min per rotor variant (cached corridor
map), bonus ~1 min.

Optional flags:
    --only m2 | bonus           run one part only
    --variants refined          Milestone 2 for the design rotor only (halves M2 time)
    --recompute-corridor        also re-solve the 273-point corridor map (+5-11 min per variant)
    --jobs N                    worker processes for the corridor map
"""
import argparse
import glob
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))

BASE_ENV = dict(os.environ, MPLBACKEND="Agg", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8",
                OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


def run(label, cmd, env=BASE_ENV):
    """Run one script from the repository root; a non-zero exit is retried once."""
    print(f"\n=== {label}", flush=True)
    t0 = time.time()
    for attempt in range(2):
        rc = subprocess.run(cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL).returncode
        if rc == 0 or attempt == 1:
            break
        print(f"    exit code {rc} -- running it once more", flush=True)
    print(f"    exit code {rc} ({time.time() - t0:.0f} s)", flush=True)
    return rc


def figures():
    """All Milestone 2 figure files (PNG plots + bonus HTML animations)."""
    pats = ["outputs/m2/rotor_*/*.png",
            "bonus_simulation_transition_analysis/output/*.html"]
    return sorted(p for pat in pats for p in glob.glob(os.path.join(ROOT, pat)))


def main():
    ap = argparse.ArgumentParser(description="Regenerate every plot of the project in one go.")
    ap.add_argument("--only", choices=["m2", "bonus"], default=None)
    ap.add_argument("--variants", nargs="+", default=["refined", "M1"], choices=["refined", "M1"])
    ap.add_argument("--recompute-corridor", action="store_true")
    ap.add_argument("--jobs", type=int, default=None)
    a = ap.parse_args()

    t_start = time.time()
    failures = []

    if a.only in (None, "m2"):
        print("\n########## Milestone 2 figures and tables -> outputs/m2/rotor_<variant>/", flush=True)
        # The existing Milestone 2 pipeline runner, without its pytest step (plots only).
        cmd = [sys.executable, "scripts/m2/run_all_m2.py", "--skip-tests", "--variants", *a.variants]
        if a.recompute_corridor:
            cmd.append("--recompute-corridor")
        if a.jobs:
            cmd += ["--jobs", str(a.jobs)]
        if run(f"[M2] scripts/m2/run_all_m2.py for rotor variant(s) {', '.join(a.variants)}", cmd):
            failures.append("scripts/m2/run_all_m2.py")

    if a.only in (None, "bonus"):
        print("\n########## Bonus 3D transition simulation -> bonus_simulation_transition_analysis/output/",
              flush=True)
        script = "bonus_simulation_transition_analysis/run_transition_simulation.py"
        for leg in ("outbound", "inbound"):
            if run(f"[Bonus] {script} --leg {leg}", [sys.executable, script, "--leg", leg]):
                failures.append(f"{script} --leg {leg}")

    # Summary: which figure files were (re)written during this run.
    after = figures()
    fresh = [p for p in after if os.path.getmtime(p) >= t_start - 1]
    stale = [p for p in after if p not in fresh]
    print("\n" + "=" * 78)
    print(f"Figures written in this run: {len(fresh)}  ({(time.time() - t_start) / 60:.1f} min)")
    groups = {}
    for p in fresh:
        groups.setdefault(os.path.relpath(os.path.dirname(p), ROOT), []).append(p)
    for d, files in sorted(groups.items()):
        print(f"    {len(files):3d}  {d.replace(os.sep, '/')}/")
    if stale and a.only is None:
        print("Existing figures NOT regenerated in this run (left from before):")
        for p in stale:
            print("    " + os.path.relpath(p, ROOT).replace(os.sep, "/"))
    print("\nAll done, every script finished." if not failures else f"\nFAILED scripts: {failures}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
