"""Long-shot finder (kept separate from the main card).  python3 longshot.py slate/MMDD -> longshots.csv
Same-player alt combos (rebounds X+ AND assists Y+, and points X+ AND rebounds/assists Y+), priced straight from the game
sims, so the link between the two stats is built in. Focus on 'special case' players: big minutes jump vs. their season
(a star teammate out) or a team missing shooters. Shows the model's chance and fair odds; compare with the SGP price on
Novig / a sportsbook. Bet only if the app pays MORE than the fair odds, and keep it tiny (0.25u)."""
import sys, os, glob, json, pandas as pd, numpy as np
D = sys.argv[1]
gap = json.load(open(f'{D}/min_gap.json')) if os.path.exists(f'{D}/min_gap.json') else {}
def american(p): return f"+{round(100*(1-p)/p)}" if p < 0.5 else f"{-round(100*p/(1-p))}"
rows = []
for f in glob.glob(f'{D}/sim_*.parquet'):
    g = os.path.basename(f)[4:-8]; S = pd.read_parquet(f)
    for k, x in S.groupby('key'):
        mins = x['min'].mean()
        if mins < 24: continue
        nm = x.player.iloc[0] if 'player' in x else k; tm = x.team.iloc[0]
        r, a, p = x.reb.values, x.ast.values, x.pts.values
        bump = gap.get(k, 0)                                   # model minutes vs market-implied (positive = more than expected)
        combos = []
        for R_ in range(int(np.percentile(r, 60)), int(np.percentile(r, 95)) + 1):
            for A_ in range(int(np.percentile(a, 60)), int(np.percentile(a, 95)) + 1):
                combos.append((f'{R_}+ reb & {A_}+ ast', ((r >= R_) & (a >= A_)).mean(), R_ + A_))
        for P_ in range(int(np.percentile(p, 70) // 5 * 5), int(np.percentile(p, 97)) + 1, 5):
            R2 = int(np.percentile(r, 70)); A2 = int(np.percentile(a, 70))
            combos.append((f'{P_}+ pts & {R2}+ reb', ((p >= P_) & (r >= R2)).mean(), P_ + R2))
            combos.append((f'{P_}+ pts & {A2}+ ast', ((p >= P_) & (a >= A2)).mean(), P_ + A2))
        for lab, pr, size in combos:
            if 0.04 <= pr <= 0.20:                             # the long-shot zone: about +400 to +2400
                rows.append(dict(game=g, team=tm, player=nm, combo=lab, chance=round(pr * 0.9, 3),   # 10% haircut: sims are a bit too confident in the tails
                                 fair_odds=american(pr * 0.9), min=round(mins, 1), min_bump=round(bump, 1),
                                 avg=f"{r.mean():.1f} reb / {a.mean():.1f} ast / {p.mean():.1f} pts", size=size))
L = pd.DataFrame(rows)
if len(L):
    # special-case first: players whose minutes jump (star teammate out), then the biggest combos at a decent chance
    L['special'] = L.min_bump >= 2
    L = L.sort_values(['special', 'size', 'chance'], ascending=[False, False, False]).groupby('player').head(3)
    L = L.sort_values(['special', 'chance'], ascending=[False, False]).head(30)
L.to_csv(f'{D}/longshots.csv', index=False)
print(L.head(15).to_string(index=False) if len(L) else 'no long shots')
