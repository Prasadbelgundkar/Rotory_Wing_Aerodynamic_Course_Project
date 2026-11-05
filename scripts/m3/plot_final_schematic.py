"""
Milestone 3 -- Section 1.1: final aircraft schematic (labelled, approximately
dimensioned).

Reuses the Milestone 2 drawing (scripts/m2/plot_aircraft_schematic.py: rotors,
wing, flaperons, tails, nacelles, CG in both modes, all from
src/m2/aircraft_input_m2.py) and adds further layout detail:
landing gear, payload (cabin) region, cockpit, wing fuel tanks, engines /
proprotor gearboxes / interconnect drive, and a component-location table.

Output: outputs/m3/m3_1p1_final_schematic.png
"""
import importlib.util
import os

import numpy as np
from matplotlib.patches import Rectangle, Circle

from _common import CFG, plt, save_figure, ROOT

_spec = importlib.util.spec_from_file_location(
    "m2_schematic", os.path.join(ROOT, "scripts", "m2", "plot_aircraft_schematic.py"))
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)          # its `_common` import resolves to this (M3) _common: same CFG / plt

CABIN = (-2.7, 1.7)          # payload cabin x-range from the reference point [m] (payload centroid -0.5 m)
COCKPIT = (2.0, 4.6)
NOSE_GEAR_X, MAIN_GEAR_X = 4.0, -0.9
TANK_ETA = (0.12, 0.62)      # wing fuel tanks, fraction of the semi-span


def add_top(ax, ac):
    Y = lambda y: -y                                                     # noqa: E731
    w = ac.wing
    b2, c = w.span_m / 2, w.chord_m
    ax.add_patch(Rectangle((CABIN[0], -0.75), CABIN[1] - CABIN[0], 1.5, fc='#ffe0b2', ec='tab:orange', lw=1.4,
                           hatch='..', zorder=6))
    ax.text(np.mean(CABIN), 0, f"payload cabin\n10 pax, {CFG.M1.PAYLOAD_KG:.0f} kg", ha='center', va='center',
            fontsize=7.5, zorder=9)
    ax.add_patch(Rectangle((COCKPIT[0], -0.6), COCKPIT[1] - COCKPIT[0], 1.2, fc='#e1bee7', ec='tab:purple', lw=1.2,
                           zorder=6))
    ax.text(np.mean(COCKPIT), 0, "cockpit\n2 crew", ha='center', va='center', fontsize=7, zorder=9)
    for s in (1, -1):
        y1, y2 = TANK_ETA[0] * b2, TANK_ETA[1] * b2
        ax.add_patch(Rectangle((-0.6 * c, Y(s * y2) if s > 0 else Y(s * y1)), 0.7 * c, y2 - y1, fc='#c8e6c9',
                               ec='tab:green', lw=1.2, hatch='xx', alpha=0.9, zorder=4.5))
    ax.text(-0.25 * c, Y(0.37 * b2), f"wing fuel tanks\n{CFG.FUEL_CAPACITY_KG:.0f} kg", ha='center', va='center',
            fontsize=7, color='darkgreen', zorder=9)
    ax.plot([-0.3, -0.3], [-ac.nacelle_pivot_ref_m[1], ac.nacelle_pivot_ref_m[1]], color='tab:brown', lw=1.4,
            ls='-.', zorder=4.6)
    ax.text(-0.45, Y(-0.55 * b2), "interconnect\ndrive shaft", ha='right', fontsize=7, color='tab:brown')
    pv = ac.nacelle_pivot_ref_m
    ax.annotate(f"tilting nacelle:\n{CFG.ENGINE_NAME} engine\n+ proprotor gearbox", xy=(pv[0] - 0.5, Y(pv[1])),
                xytext=(pv[0] - 6.2, Y(pv[1]) - 2.6), fontsize=7, arrowprops=dict(arrowstyle='->', lw=0.8))
    for x, lab in ((NOSE_GEAR_X, "nose gear"), (MAIN_GEAR_X, "main gear (sponsons)")):
        for yy in ((0.0,) if x == NOSE_GEAR_X else (1.15, -1.15)):
            ax.add_patch(Rectangle((x - 0.25, yy - 0.12), 0.5, 0.24, fc='k', zorder=9))
        ax.text(x, -1.55 if x == MAIN_GEAR_X else 0.35, lab, ha='center', fontsize=6.5, zorder=9)


def add_side(ax, ac):
    Z = lambda z: -z                                                     # noqa: E731
    ax.add_patch(Rectangle((CABIN[0], Z(1.95)), CABIN[1] - CABIN[0], 1.55, fc='#ffe0b2', ec='tab:orange', lw=1.2,
                           hatch='..', alpha=0.85, zorder=3))
    ax.text(np.mean(CABIN), Z(1.15), "payload cabin", ha='center', fontsize=7.5, zorder=9)
    ax.add_patch(Rectangle((COCKPIT[0], Z(1.6)), COCKPIT[1] - COCKPIT[0], 1.2, fc='#e1bee7', ec='tab:purple',
                           alpha=0.85, zorder=3))
    ax.text(np.mean(COCKPIT), Z(1.0), "cockpit", ha='center', fontsize=7, zorder=9)
    for x, r in ((NOSE_GEAR_X, 0.28), (MAIN_GEAR_X, 0.38)):
        ax.plot([x, x], [Z(S.FUS_BOT_Z - 0.6), Z(S.FUS_BOT_Z + 0.35)], 'k-', lw=2, zorder=9)
        ax.add_patch(Circle((x, Z(S.FUS_BOT_Z + 0.35 + r)), r, fc='0.2', ec='k', zorder=9))
    ax.text(MAIN_GEAR_X, Z(S.FUS_BOT_Z + 1.35), "main gear", ha='center', fontsize=7)
    ax.text(NOSE_GEAR_X, Z(S.FUS_BOT_Z + 1.25), "nose gear", ha='center', fontsize=7)
    gd = S.FUS_BOT_Z + 0.35 + 2 * 0.38
    ax.axhline(Z(gd), color='0.5', lw=0.8, ls=':')
    h = ac.hub_ref_m(90.0)
    S.dim(ax, (7.8, Z(gd)), (7.8, Z(h[2])), f"hub height {gd - h[2]:.1f} m", off=(0.8, 0))
    hub_a = ac.hub_ref_m(0.0)
    clr = (gd - hub_a[2]) - CFG.ROTOR.radius_m
    note = (f"airplane-mode disk reaches {abs(clr):.1f} m below the ground line: no airplane-mode or rolling "
            "take-off / landing (as V-22)" if clr < 0 else f"airplane-mode ground clearance {clr:.1f} m")
    ax.text(-9.2, Z(gd) - 0.35, note, fontsize=7, color='tab:blue', va='top')


def location_table(ax, ac):
    rows = []
    for it in ac.mass_items:
        if it.tilts_with_nacelle:
            pos = f"nacelle, {it.shaft_offset_m:+.1f} m along shaft"
        else:
            pos = f"x {it.x_m:+.2f}, z {it.z_m:+.2f}"
        rows.append([it.name, f"{it.mass_kg:.0f}", pos])
    for n in (90.0, 0.0):
        cg = ac.cg_ref_m(n)
        rows.append([f"CG, nacelle {n:.0f} deg (MTOW)", f"{ac.mass_kg():.0f}", f"x {cg[0]:+.2f}, z {cg[2]:+.2f}"])
    cg = ac.cg_ref_m(0.0, fuel_kg=CFG.M1.RESERVE_FUEL_KG)
    rows.append(["CG, airplane mode, reserve fuel", f"{ac.mass_kg(fuel_kg=CFG.M1.RESERVE_FUEL_KG):.0f}",
                 f"x {cg[0]:+.2f}, z {cg[2]:+.2f}"])
    ax.axis('off')
    t = ax.table(cellText=rows, colLabels=["Component / mass item", "Mass [kg]", "Location from ref. point [m]"],
                 loc='center', cellLoc='left', colWidths=[0.5, 0.15, 0.35])
    t.auto_set_font_size(False)
    t.set_fontsize(7.2)
    t.scale(1, 1.35)
    ax.set_title("Component locations (x + fwd, z + down from the wing-root quarter chord)", fontsize=9)


def main():
    ac = CFG.get_default_aircraft()
    fig = plt.figure(figsize=(18, 13))
    ax1 = fig.add_axes([0.02, 0.36, 0.50, 0.58])
    ax2 = fig.add_axes([0.03, 0.03, 0.62, 0.30])
    ax3 = fig.add_axes([0.53, 0.42, 0.45, 0.50])
    S.top_view(ax1, ac)
    add_top(ax1, ac)
    S.side(ax2, ac)
    add_side(ax2, ac)
    ax2.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), fontsize=8)
    location_table(ax3, ac)
    for ax in (ax1, ax2):
        ax.grid(True, alpha=0.3)
    fig.suptitle(f"Section 1.1 -- Final (frozen) tiltrotor configuration, approximately to scale: MTOW "
                 f"{CFG.GROSS_MASS_KG:.0f} kg, 2 x {CFG.ENGINE_NAME}, rotor '{CFG.ROTOR_VARIANT}'; "
                 "'+' = reference point, circle/square = CG in helicopter/airplane mode", fontsize=11.5)
    save_figure(fig, "m3_1p1_final_schematic", "1.1",
                "Top and side views of the final design drawn from src/m2/aircraft_input_m2.py: proprotors "
                f"(R = {CFG.ROTOR.radius_m} m) at the wing-tip conversion pivots in helicopter and airplane mode, "
                "tilting nacelles with engine and proprotor gearbox, interconnect drive shaft, wing with flaperons "
                "and fuel tanks, fuselage with cockpit and payload cabin, nose and main landing gear, horizontal tail "
                "with elevator, vertical tail with rudder, CG in both modes; the table lists every mass item and its "
                "location. Dimensions in metres. Cabin, cockpit, tank and gear outlines are layout sketches "
                "consistent with the mass-item centroids (they do not enter the analysis).")


if __name__ == "__main__":
    main()
