# Team 6 Modeling Project: Tandem-Rotor Interference (CH-47 class)

How the forward rotor's wake raises the power of the aft rotor of a tandem helicopter, modelled with a
free-vortex wake and plugged into the team's BEMT tool from Milestones 1 and 2.

## What to look at

| Item | File |
|---|---|
| Slide deck (graded) | [`submission/Team6_Tandem_Rotor_Interference.pptx`](submission/Team6_Tandem_Rotor_Interference.pptx) |
| Conceptual questions (separate Word document) | [`submission/Team6_Conceptual_Questions_TandemSet.docx`](submission/Team6_Conceptual_Questions_TandemSet.docx) |
| One-file runner (regenerates every result in the deck) | [`../run_all_mp.py`](../run_all_mp.py) |
| Wake-model survey (literature, model comparison) | [`docs/Tandem_Wake_Model_Survey.docx`](docs/Tandem_Wake_Model_Survey.docx) |
| Model selection against the rubric criteria | [`docs/model_selection.md`](docs/model_selection.md) |

## Run it (one command)

From the repository root:

```bash
pip install -r requirements.txt
python run_all_mp.py
```

This runs the tandem-interference unit tests, then every figure script, and writes all outputs to
`outputs/mp/`. It takes about 2 to 4 minutes on a laptop and needs no internet access. At the end it prints
each deck output with the slide it belongs to and whether it was regenerated; the exit code is 0 only if
the tests pass and every output was written.

Options: `--skip-tests` (figures only); `--recompute-fvw` (re-run the free-vortex wake cases themselves
before plotting, about an hour, needs `numba`; by default the cached runs in `src/data/fvw/` are used).

## Which output goes on which slide

| Slide | Output in `outputs/mp/` | Script in `scripts/mp/` |
|---|---|---|
| Validation (1/3): code verification | `ch47_convergence.png` + unit tests printed by the runner | `plot_fvw_standalone.py`, `tests/test_tandem_*.py` |
| Validation (2/3): standalone free wake vs TN-3236 | `dingeldein_validation.png` | `plot_fvw_standalone.py` |
| Validation (3/3): integrated tool vs TN-3236 | `tandem_validation_dingeldein.png`, `tandem_validation_table.md` | `plot_tandem_validation.py` |
| Assessment (1/4): forward flight | `tandem_forward_flight.png`, `tandem_forward_flight_table.md` | `plot_tandem_forward_flight.py` |
| Assessment (2/4): why the aft rotor pays | `ch47_aft_inflow.png` | `plot_fvw_standalone.py` |
| Assessment (3/4): tool vs two-way free wake | `ch47_power.png` | `plot_fvw_standalone.py` |
| Assessment (4/4): hover and layout study | `tandem_hover_assessment.png`, `tandem_parameter_study.png` | `plot_tandem_hover_assessment.py`, `plot_tandem_parameter_study.py` |

`plot_fvw_standalone.py` also writes the wake side views (`*_wake_mu*.png`), `dingeldein_power.png`,
`dingeldein_aft_inflow.png` and `*_table.json`, which back numbers quoted in the text of the deck.

## Where the model lives in the code

| File | Content |
|---|---|
| `src/tandem_fvw.py` | free-vortex wake solver for two rotors (lifting-line blades, trailed and shed vortex lattice, Vatistas core, each rotor trimmed); run offline to produce the interference maps |
| `src/data/fvw/` | cached free-vortex wake runs: CH-47 at μ = 0.05 to 0.25, TN-3236 rig at μ = 0.11 to 0.295 |
| `src/tandem_forward_flight.py` | forward flight: interference switch `model="none" / "coleman" / "fvw"`, trims both rotors |
| `src/m2/edgewise_bemt.py` | Milestone 2 edgewise BEMT, with the new optional `external_inflow(r, ψ)` term for the aft rotor |
| `src/tandem_interference.py` | hover: overlap geometry and Coleman vortex-cylinder interference |
| `src/tandem_rotor_config.py` | CH-47 class baseline (R 9.14 m, d 13.60 m = 1.487R, 14.94 % overlap, 22 680 kg, 3 + 3 blades, 220 m/s tip speed) |
| `src/data/dingeldein_tn3236_fig6.csv` | validation data digitised from Dingeldein, NACA TN-3236 (1954), Figure 6 |
| `tests/test_tandem_interference.py`, `tests/test_tandem_forward_flight.py` | verification tests |

With the switch off (`model="none"`, `external_inflow=None`, `include_interference=False`) the original
BEMT tool runs unchanged; a regression test checks this bit for bit.

## Validation data

The only validation data used is Dingeldein, NACA TN-3236, Figure 6 (wind-tunnel tandem, forward flight),
digitised to `src/data/dingeldein_tn3236_fig6.csv` with the source noted in the file header.

## Verification tests (run by `run_all_mp.py`)

* Overlap geometry: zero overlap, full overlap, analytical lens area at d = R, unequal radii.
* Coleman limits: Δv = v_i coplanar, 2v_i far below, 0 far above; raising the aft pylon lowers Δv.
* Baseline recovery: interference off gives two isolated rotors, bit for bit.
* Limiting case: a uniform imposed Δv in hover equals an axial climb at that speed.
* Physical direction: aft power none < Coleman < FVW; aft collective rises; forward rotor unchanged.
* Convergence: radial grid (hover), trim residual below 1e-3 (forward flight), free-wake revolution scatter.
* Input checks: non-positive radii, wrong-shape or non-finite external inflow, μ outside the cached maps.
