"""
Milestone 3 -- Section 2.2: integrated workflow / logic diagram.

Shows the information exchanged between atmosphere, rotor model, aircraft
aerodynamics, trim, propulsion / power and the mission planner, colour-coded
by the milestone each module comes from.

Output: outputs/m3/m3_2p2_workflow.png
"""
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from _common import plt, save_figure

C = {"M1": "#bbdefb", "M2": "#c8e6c9", "M3": "#ffe0b2", "IO": "#eeeeee"}


def box(ax, x, y, w, h, title, body, kind):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=C[kind], ec='k',
                                lw=1.2))
    ax.text(x + w / 2, y + h - 0.12, title, ha='center', va='top', fontsize=9.5, fontweight='bold')
    ax.text(x + w / 2, y + h - 0.42, body, ha='center', va='top', fontsize=7.6, linespacing=1.25)
    return (x, y, w, h)


def arrow(ax, p, q, label="", rad=0.0, off=(0, 0), color='k'):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=14, lw=1.3, color=color,
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], label, fontsize=7.2, ha='center',
                va='center', color=color, bbox=dict(fc='white', ec='none', pad=0.6, alpha=0.9))


def main():
    fig, ax = plt.subplots(figsize=(17, 11))
    ax.set_xlim(0, 17)
    ax.set_ylim(0, 11)
    ax.axis('off')
    box(ax, 0.3, 8.3, 4.9, 2.2, "Inputs (user files)",
        "src/aircraft_input.py  [M1]: rotor, airfoil, RPM,\nmasses, power lapse, requirements\n"
        "src/m2/aircraft_input_m2.py  [M2]: wing, tails,\nmass items / CG, engines, limits, paths\n"
        "inputs/m3_design_mission.json  [M3]", "IO")
    box(ax, 6.3, 8.3, 4.4, 2.2, "Atmosphere  [M1]", "environment.isa(h, dISA)\n-> rho, a, T, p", "M1")
    box(ax, 11.8, 8.3, 4.9, 2.2, "Propulsion / power  [M1 + M2 + M3]",
        "P_avail = P_TO (rho/rho0)^n eta_drive  [M1]\n2 x CT7-8A selected  [M2]\n"
        "rating per segment: TO / MCP 86 %  [M3]\nfuel flow = SFC x P_req  [M1]", "M3")
    box(ax, 0.9, 4.3, 4.3, 2.8, "Rotor model  [M1 -> M2]",
        "rotor.py, airfoil.py  [M1]\nbemt.py: axial BEMT  [M1]\nedgewise_bemt.py: azimuth-resolved\n"
        "BEMT, cyclic, annular-Glauert + K,\nreverse flow, stall, tip Mach  [M2]", "M2")
    box(ax, 6.3, 4.3, 4.4, 2.8, "6-DOF trim  [M2]",
        "trim_6dof.py: unknowns theta, phi,\ntheta0, d_lon, d_lat, d_ped\nFX..MZ about CG(i_n, fuel) -> 0\n"
        "bounded least squares\nstatus + limit flags\n(masses, CG(i_n, fuel), limits\nfrom the input files)", "M2")
    box(ax, 11.8, 4.3, 4.9, 2.8, "Aircraft aerodynamics  [M2]",
        "aero_models.py: wing + flaperons,\nH-tail + elevator (downwash),\nV-tail + rudder, fuselage drag\n"
        "frames.py: frames, moment\ntransfer to the CG\n(geometry, CG from the input files)", "M2")
    box(ax, 0.9, 0.3, 11.0, 2.6, "Mission Planner v2  [M2]  +  design mission  [M3]",
        "mission_v2.py: segments with speed / climb / nacelle / RPM / wind schedules, online trim every step, limit and "
        "continuity checks,\nexplicit-Euler fuel / mass / altitude / distance update  [M2]\n"
        "m3/design_mission.py: JSON mission -> segments, run-time sizing of climb / cruise / descent to the range, "
        "\nconstraint utilisation and minimum margins  [M3]", "M3")
    box(ax, 12.6, 0.3, 4.1, 2.6, "Outputs  outputs/m3/",
        "performance_summary.py\nrun_design_mission.py\nmake_m3_tables.py\n(+ M2 corridor map reused)", "IO")
    arrow(ax, (5.2, 9.4), (6.3, 9.4), "dISA")
    arrow(ax, (10.7, 9.4), (11.8, 9.4), "rho")
    arrow(ax, (3.0, 8.3), (3.0, 7.1), "rotor geometry, airfoil", off=(0, 0))
    arrow(ax, (8.5, 8.3), (8.5, 7.1), "rho, a at h", off=(0, 0))
    arrow(ax, (13.0, 8.3), (10.0, 7.1), "P_avail per rotor", off=(0.2, 0.25))
    arrow(ax, (0.55, 8.3), (0.55, 2.9), "", color='k')
    ax.text(0.65, 5.6, "mission\nJSON", fontsize=7.2, rotation=90, va='center')
    arrow(ax, (6.3, 6.4), (5.2, 6.4), "", color='tab:blue')
    ax.text(5.75, 6.75, "V, alpha_shaft, RPM,\ntheta0, theta1c, theta1s", fontsize=7, ha='center', color='tab:blue')
    arrow(ax, (5.2, 5.0), (6.3, 5.0), "")
    ax.text(5.75, 4.45, "hub F, M, P_req,\nstall, Mach, reverse", fontsize=7, ha='center')
    arrow(ax, (10.7, 6.4), (11.8, 6.4), "", color='tab:blue')
    ax.text(11.25, 6.75, "V, alpha, beta,\nde, da, dr", fontsize=7, ha='center', color='tab:blue')
    arrow(ax, (11.8, 5.0), (10.7, 5.0), "")
    ax.text(11.25, 4.45, "airframe F, M\nat CG, alpha_w", fontsize=7, ha='center')
    arrow(ax, (7.4, 2.9), (7.4, 4.3), "", color='tab:blue')
    ax.text(7.3, 3.6, "V, gamma, accel, i_n,\nRPM, mass, fuel, h", fontsize=7, ha='right', va='center', color='tab:blue')
    arrow(ax, (9.6, 4.3), (9.6, 2.9), "")
    ax.text(9.7, 3.6, "attitude, controls, P_req,\nP_avail, margins, feasible", fontsize=7, ha='left', va='center')
    arrow(ax, (11.9, 1.6), (12.6, 1.6), "")
    for i, (k, lab) in enumerate((("M1", "Milestone 1 module"), ("M2", "Milestone 2 module"),
                                  ("M3", "Milestone 3 addition"), ("IO", "inputs / outputs"))):
        ax.add_patch(FancyBboxPatch((1.0 + 2.9 * i, 10.65), 0.4, 0.22, boxstyle="round,pad=0.01", fc=C[k], ec='k'))
        ax.text(1.5 + 2.9 * i, 10.76, lab, va='center', fontsize=8.5)
    ax.set_title("Section 2.2 -- Integrated analysis workflow of the final design (blue arrows: inputs to each "
                 "call, black: results returned; repeated at every mission time step)", fontsize=12)
    save_figure(fig, "m3_2p2_workflow", "2.2",
                "Flow of information between the modules used for the final aircraft and mission analysis, with the "
                "milestone each module originates from (blue M1, green M2, orange M3 additions). At every mission "
                "time step the planner passes the flight state to the 6-DOF trim, which calls the rotor and "
                "airframe models with the ISA atmosphere and returns controls, power required and limit flags; power "
                "available and fuel burn come from the propulsion model.")


if __name__ == "__main__":
    main()
