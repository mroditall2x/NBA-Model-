# NBA Prop Model
Monte Carlo possession sim for NBA player props, spreads and totals (hoopR data) with calibration, minutes-gap rules, defense-vs-position, line-movement and EV+ tracking. See SKILL.md for every rule and lesson, graded_log.csv for the record.

Daily: GitHub Actions grades yesterday at 8:30 AM CT. To build a card: commit `slate/MMDD/lines.json` + `props_p1.txt` (+ `pp_compact.json`) then run the workflow with the date, or run `python3 run_day.py YYYY-MM-DD` locally.
Line movement: `python3 line_moves.py snap slate/MMDD` in the morning, `python3 line_moves.py check slate/MMDD` before tip.
