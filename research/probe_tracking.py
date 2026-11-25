"""Probe (11/25): does NBA.com's stats site answer from this machine?
Pulls this season's player tracking tables (Passing, Rebounding) with nba_api.
Writes research/tracking_probe.md (status of every try) and, when it works,
research/tracking_probe_passing.csv / tracking_probe_rebounding.csv.
Never touches the card or the model."""
import sys, time, datetime as dt, traceback
import pandas as pd
from nba_api.stats.endpoints import leaguedashptstats

SEASON = sys.argv[1] if len(sys.argv) > 1 else '2026-27'
log = [f'# NBA.com tracking probe {dt.datetime.now():%Y-%m-%d %H:%M %Z}', '', f'season {SEASON}', '']
ok = 0
for measure, keep in (('Passing', ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', 'PASSES_MADE', 'POTENTIAL_AST', 'AST', 'AST_POINTS_CREATED']),
                      ('Rebounding', ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', 'REB', 'REB_CHANCES', 'REB_CONTEST', 'REB_CHANCE_PCT'])):
    for attempt in (1, 2, 3):
        t0 = time.time()
        try:
            df = leaguedashptstats.LeagueDashPtStats(season=SEASON, pt_measure_type=measure, player_or_team='Player',
                                                    per_mode_simple='PerGame', timeout=60).get_data_frames()[0]
            cols = [c for c in keep if c in df.columns]
            df[cols].to_csv(f'research/tracking_probe_{measure.lower()}.csv', index=False)
            log.append(f'- {measure}: OK on try {attempt} in {time.time()-t0:.1f}s, {len(df)} players, columns: {", ".join(cols)}')
            log.append('')
            log.append(df[cols].sort_values(cols[-1] if measure == 'Rebounding' else 'POTENTIAL_AST', ascending=False).head(5).to_markdown(index=False) if hasattr(df, 'to_markdown') else '')
            log.append('')
            ok += 1
            break
        except Exception as e:
            log.append(f'- {measure}: try {attempt} FAILED after {time.time()-t0:.1f}s: {type(e).__name__}: {str(e)[:200]}')
            time.sleep(10)
log.append('')
log.append(f'RESULT: {"WORKS" if ok == 2 else ("PARTIAL" if ok else "BLOCKED")} ({ok}/2 tables)')
open('research/tracking_probe.md', 'w').write('\n'.join(log) + '\n')
print('\n'.join(log))
