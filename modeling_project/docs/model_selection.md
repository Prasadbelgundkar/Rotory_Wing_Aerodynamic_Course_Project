# Model selection: why the free-vortex wake, not the prescribed-wake hybrid

*Team 6, tandem-rotor interference. Text for the Model Selection slide (10 marks). Written 18 Oct 2026.*

## Slide version (5 bullets)

- **The data decided it.** The only tandem data set we could obtain and digitise is Dingeldein, NACA TN-3236 Fig. 6: level forward flight, two rotors 1.03 D apart, **no disk overlap**. A model has to work in forward flight to be validated at all.
- **Overlap models miss the effect.** Coleman's overlap model predicts zero interference for that rig, yet the rear rotor needs 6–9 hp (60–70 %) more power than a single rotor. In forward flight the forward wake is swept back over the whole aft disk, not just the overlap lens.
- **A prescribed wake cannot do this either.** Landgrebe / Kocurek–Tangler wakes are hover fits for isolated rotors. Forward-flight prescribed wakes (Egolf & Landgrebe) are also isolated-rotor fits, so they leave out the mutual distortion of the two wakes, which is the phenomenon we are modelling.
- **The cost is paid offline.** The free-vortex wake runs once per advance ratio (minutes). The tool stores the forward rotor's downwash on the aft disk, Δv(r, ψ), and the BEMT reads it in a fraction of a second per trim, so the computational-cost criterion is met inside the design tool.
- **It plugs into the tool we already have.** The Milestone 2 edgewise BEMT is already resolved in azimuth, so Δv(r, ψ) enters through one optional `external_inflow` argument. With the switch off, the original tool runs bit for bit unchanged.

## Against each rubric criterion

| Criterion | Coleman cylinder (baseline) | Prescribed wake hybrid (survey's first choice) | **Free-vortex wake → Δv map (selected)** | Vortex particle method |
|---|---|---|---|---|
| Physical fidelity | Uniform Δv on overlap only; zero for separated disks | Contracted tip vortices; isolated-rotor geometry; hover | Both wakes free and mutually distorted; skewed forward-flight wake; correct sign above/below the disk | Highest; wake merging, viscous effects |
| Required inputs | v_i, overlap, stagger | Plus empirical wake constants (k₁, k₂, A) fitted to untapered blades | Same blade geometry/airfoil as BEMT; core model constants | Plus solver setup, particle parameters |
| Cost in the tool | ~0 | < 1 s per BEMT call | Minutes per μ offline, then < 1 s per trim | Hours per case |
| Validation data available to us | Gives 0 for TN-3236, so it fails the check | Hover only; we have no hover overlap data we can verify (TN D-534 figures not obtained) | TN-3236 Fig. 6, forward flight, digitised | No tandem forward-flight results we could obtain |
| Compatibility with our code | Already in | Needs per-station inflow in axial BEMT; hover only | Uses the azimuth-resolved M2 edgewise BEMT via `external_inflow` | External solver only |
| Fit to the CH-47 design question | Small hover effect (+2.7 %) | Hover only | Forward flight, where a CH-47 spends its mission (+29 to +34 % total power at μ 0.1–0.2) | Benchmark only |

## Why our plan changed after the survey

The survey (tandem_wake_models.md, Section 8) recommended a Coleman + prescribed-wake hybrid for **hover**. That assumed the overlap hover data in our CSV was real. Checking it showed the CSV cannot be from TN-3236 (wrong radius, wrong spacing, and the TN-3236 disks do not overlap), so it was removed. With no hover overlap data we could defend, the hover-only model could not be validated. The data we could defend was in forward flight, and that needed a forward-flight wake model. Of the survey's models, the free-vortex wake (Model C) was the lowest-fidelity one that captures the swept-back wake interacting with the aft rotor. The vortex particle method (Model D) would add wake merging, but costs hours per case, and we had no forward-flight tandem results to check it against.

## What it costs us (state this, examiners will ask)

- In the BEMT tool the coupling is one-way: forward wake on the aft rotor. The full FVW shows that the aft rotor also lowers the forward rotor's power by 6–8 %, so the tool slightly over-predicts the total.
- The Δv maps belong to one geometry. A different d/R or stagger needs new FVW runs (`python src/tandem_fvw.py ch47 <μ list>`).
- Against TN-3236 the integrated tool predicts rear-rotor power within about 7 % for μ ≤ 0.2, but under-predicts the interference increment by about a quarter. Above μ ≈ 0.2 the blade model (linear airfoil, no stall delay) over-predicts the single-rotor power, so results there are not trusted.
- Hover still uses Coleman (with the stagger sign corrected). The FVW was not run in hover.
