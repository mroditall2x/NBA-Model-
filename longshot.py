"""Long-shot finder (kept separate from the main card).  python3 longshot.py slate/MMDD -> longshots.csv
Same-player alt combos (rebounds X+ AND assists Y+, and points X+ AND rebounds/assists Y+), priced straight from the game
sims, so the link between the two stats is built in. Focus on 'special case' players: big minutes jump vs. their season
(a star teammate out) or a team missing shooters. Shows the model's chance and fair odds; compare with the SGP price on
Novig / a sportsbook. Bet only if the app pays MORE than the fair odds, and keep it tiny (0.25u)."""
import sys, os, glob, json, pandas as pd, numpy as np
D = sys.argv[1]
gap = json.load(open(f'{D}/min_gap.json')) if os.path.exists(f'{D}/min_gap.json') else {}
def american(p): return f"+{round(100*(1-p)/p)}" if p < 0.5 else f"{-round(100*p/(1-p))}"
# 'the situation lines up': a teammate who takes 12+ shots a game is OUT tonight (vacated shots), or the player's minutes jump 3+
from slate_names import norm
outs = set()
for f in glob.glob('slate/*_out.json'):
    if f.endswith(f"{D[-4:-2]}-{D[-2:]}_out.json"): outs = {norm(x) for x in json.load(open(f))}
try:
    pb = pd.read_parquet(f"{os.environ.get('NBA_DATA', 'repo/nba')}/player_box/parquet/player_box_2027.parquet")
    pb = pb[pd.to_numeric(pb.minutes, errors='coerce') > 0]
    fga = pb.groupby(['athlete_display_name', 'team_abbreviation']).field_goals_attempted.mean().reset_index(); fga['k'] = fga.athlete_display_name.map(norm)
    star_out = fga[fga.k.isin(outs) & (fga.field_goals_attempted >= 12)].groupby('team_abbreviation').athlete_display_name.apply(lambda v: ', '.join(v)).to_dict()
except Exception: star_out = {}
rows = []
for f in glob.glob(f'{D}/sim_*.parquet'):
    g = os.path.basename(f)[4:-8]; S = pd.read_parquet(f)
    for k, x in S.groupby('key'):
        mins = x['min'].mean()
        if mins < 24: continue
        nm = x.player.iloc[0] if 'player' in x else k; tm = x.team.iloc[0]
        r, a, p = x.reb.values, x.ast.values, x.pts.values
        bump = gap.get(k, 0)
        why = (f'{star_out[tm]} out' if tm in star_out else '') + ('; ' if tm in star_out and bump >= 3 else '') + (f'+{bump:.0f} min' if bump >= 3 else '')
        if not why: continue                                   # only when the situation lines up                                   # model minutes vs market-implied (positive = more than expected)
        combos = []
        for R_ in range(int(np.percentile(r, 60)), int(np.percentile(r, 95)) + 1):
            for A_ in range(int(np.percentile(a, 60)), int(np.percentile(a, 95)) + 1):
                combos.append((f'{R_}+ reb & {A_}+ ast', ((r >= R_) & (a >= A_)).mean(), R_ + A_))
        for P_ in range(int(np.percentile(p, 70) // 5 * 5), int(np.percentile(p, 97)) + 1, 5):
            R2 = int(np.percentile(r, 70)); A2 = int(np.percentile(a, 70))
            combos.append((f'{P_}+ pts & {R2}+ reb', ((p >= P_) & (r >= R2)).mean(), P_ + R2))
            combos.append((f'{P_}+ pts & {A2}+ ast', ((p >= P_) & (a >= A2)).mean(), P_ + A2))
        for lab, pr, size in combos:
            if 0.06 <= pr <= 0.20:                             # the long-shot zone: about +400 to +2400
                rows.append(dict(game=g, team=tm, player=nm, combo=lab, chance=round(pr * 0.9, 3),   # 10% haircut: sims are a bit too confident in the tails
                                 fair_odds=american(pr * 0.9), min=round(mins, 1), min_bump=round(bump, 1), why=why,
                                 avg=f"{r.mean():.1f} reb / {a.mean():.1f} ast / {p.mean():.1f} pts", size=size))
L = pd.DataFrame(rows)
if len(L):
    # special-case first: players whose minutes jump (star teammate out), then the biggest combos at a decent chance
    L['special'] = True
    L = L.sort_values(['size', 'chance'], ascending=[False, False]).groupby('player').head(2)
    L = L.sort_values('chance', ascending=False).head(12)
L.to_csv(f'{D}/longshots.csv', index=False)
print(L.head(15).to_string(index=False) if len(L) else 'no situation lines up today - no long shots')
