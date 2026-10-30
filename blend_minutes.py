"""After pass 1: market-implied minutes from each player's PRA (else PTS) line -> min_override.json (50/50) + min_gap.json"""
import sys, json, pandas as pd
from slate_names import norm
D=sys.argv[1]; B=pd.read_csv(f'{D}/board.csv'); B=B[B['mean'].notna()]
ov,gap={},{}
for k,g in B.groupby(B.player.map(norm)):
    r=g[g.stat=='PRA']; r=r if len(r) else g[g.stat=='PTS']
    if not len(r): continue
    r=r.iloc[0]; imp=r.exp_min*r.line/max(r['mean'],0.1)
    gap[k]=round(imp-r.exp_min,1); ov[k]=round(0.5*r.exp_min+0.5*min(imp,40),1)
json.dump(ov,open(f'{D}/min_override.json','w')); json.dump(gap,open(f'{D}/min_gap.json','w'))
print(sorted(gap.items(),key=lambda x:-abs(x[1]))[:12])
