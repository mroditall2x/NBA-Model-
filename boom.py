"""Points ceiling finder: who can drop 25/30/35 tonight?
  python3 boom.py slate/MMDD   -> boom.csv
Uses the game sims (minutes + usage after injuries are already redistributed), scales each player's points by the
opponent's points-allowed-to-his-position (dvp_pts.csv, 50% strength) and adds a small bump when a teammate who takes
10+ shots a game is out (vacated shots). Compares ceilings with points lines and, if pulled, alt points ladders (pts_alt.json)."""
import sys, glob, os, json, pandas as pd
from slate_names import norm
D = sys.argv[1]
def pos(p): return 'G' if p in ('PG', 'SG', 'G') else ('C' if p == 'C' else 'F')
R = pd.read_parquet(f"{os.environ.get('NBA_DATA', 'repo/nba')}/rosters/parquet/rosters_2027.parquet")
pc = [c for c in R.columns if 'position' in c and 'abbrev' in c][0]
POS = {norm(n): pos(p) for n, p in zip(R.display_name, R[pc])}
DV = pd.read_csv(f'{D}/dvp_pts.csv').set_index(['opponent_team_abbreviation', 'pos']).dvp if os.path.exists(f'{D}/dvp_pts.csv') else {}
# vacated shots: season FGA/game of players ruled out tonight, per team
DATE = None
outs = set()
for f in glob.glob('slate/*_out.json'):
    if f.endswith(f"{D[-4:-2]}-{D[-2:]}_out.json"): outs = {norm(x) for x in json.load(open(f))}
pb = pd.read_parquet(f"{os.environ.get('NBA_DATA', 'repo/nba')}/player_box/parquet/player_box_2027.parquet")
pb = pb[pd.to_numeric(pb.minutes, errors='coerce') > 0]
fga = pb.groupby(['athlete_display_name', 'team_abbreviation']).field_goals_attempted.mean().reset_index()
fga['k'] = fga.athlete_display_name.map(norm)
vac = fga[fga.k.isin(outs) & (fga.field_goals_attempted >= 10)].groupby('team_abbreviation').field_goals_attempted.sum().to_dict()
lines = {}
if os.path.exists(f'{D}/pp_compact.json'):
    for r in json.load(open(f'{D}/pp_compact.json')):
        if r[2] == 'Points' and r[3]: lines[(r[0], norm(r[1]))] = float(r[3])
alts = {}
if os.path.exists(f'{D}/pts_alt.json'):
    for g, pl, L, pr, bk in json.load(open(f'{D}/pts_alt.json')): alts.setdefault((g, norm(pl)), []).append((L, pr, bk))
rows = []
for f in glob.glob(f'{D}/sim_*.parquet'):
    g = os.path.basename(f)[4:-8]; a, h = g.split('@'); S = pd.read_parquet(f)
    for k, x in S.groupby('key'):
        team = x.team.iloc[0]; opp = h if team == a else a
        dv = DV.get((opp, POS.get(k, 'F')), 1.0) if len(DV) else 1.0
        bump = 1 + min(vac.get(team, 0), 25) * 0.004            # ~+4% per 10 vacated shots, capped
        v = x.pts * (1 + 0.5 * (dv - 1)) * bump
        if v.mean() < 12: continue
        L = lines.get((g, k)); row = dict(game=g, player=x.player.iloc[0] if 'player' in x else k, team=team, opp=opp, mean=round(v.mean(), 1),
                                          p20=round((v >= 20).mean(), 3), p25=round((v >= 25).mean(), 3), p30=round((v >= 30).mean(), 3), p35=round((v >= 35).mean(), 3),
                                          dvp=round(dv, 3), vacated_fga=round(vac.get(team, 0), 1), line=L, p_over=round((v > L).mean(), 3) if L else None)
        best = None
        for AL, pr, bk in alts.get((g, k), []):
            p = 0.5 + 0.6 * ((v > AL).mean() - 0.5)                # calibrated
            ev = p * (1 + (pr / 100 if pr > 0 else 100 / -pr)) - 1
            if pr >= 150 and (best is None or ev > best[3]): best = (AL, pr, bk, round(ev, 2), round(p, 3))
        if best: row.update(alt_line=best[0], alt_odds=best[1], alt_book=best[2], alt_ev=best[3], alt_p=best[4])
        rows.append(row)
B = pd.DataFrame(rows).sort_values('p30', ascending=False)
B.to_csv(f'{D}/boom.csv', index=False)
print(B.head(15).to_string(index=False))
