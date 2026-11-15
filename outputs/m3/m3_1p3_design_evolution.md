# Section 1.3 -- changes since Milestone 2

Earlier changes (M1 -> M2) are in src/m2/aircraft_input_m2.py DESIGN_CHANGES / m2_5_design_tables.md.

| # | Change after Milestone 2 | Quantitative / physical reason |
|---|---|---|
| 1 | Rotor, wing, empennage, fuselage, nacelles, engines, mass breakdown, CG and control limits: NO CHANGE (Milestone 2 configuration frozen) | The M2 corridor map, trim matrix and both transition missions closed with no limit violation; the M3 design mission (hover at 1500 m ISA+15, 1000 km) also closes with every constraint below its limit (Section 4.3), so no analysis result supports a geometry or mass change. |
| 2 | Engine rating per flight phase: take-off rating in hover / vertical / conversion, max-continuous (86 %) in airplane mode | M2 used the take-off rating everywhere; a multi-hour mission must use the continuous rating in cruise. Cruise power (~650 kW) is far below MCP (~1760 kW at 5000 m ISA+15), so no design change follows. |
| 3 | Cruise schedule fixed for the design mission: 5000 m ISA+15, 75 m/s, 250 RPM | Best fuel per km of the final aircraft at the M1 long-range RPM (Section 3.1); 250 RPM keeps the M1 / M2 RPM schedule unchanged. |
| 4 | Reserve fuel stated consistently as 450 kg | The code has always used 450 kg; the Milestone 1 report text quoted 150 kg. 450 kg = about 50 min at MTOW hover power or ~1.2 h of cruise. |
