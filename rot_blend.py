"""Blend this-season minutes (player_box 2027 before DATE) with last-season defaults. Usage: rot_blend.py DATE W_SEASON"""
import sys,json,numpy as np,pandas as pd
from slate_names import norm
D=sys.argv[1]; W=float(sys.argv[2]) if len(sys.argv)>2 else 0.6
last=json.load(open(f'slate/{D}_rot_last.json')); out={norm(x) for x in json.load(open(f'slate/{D}_out.json'))}
q=pd.read_parquet('repo/nba/player_box/parquet/player_box_2027.parquet'); q=q[q.game_date.astype(str)<D]
q['min']=pd.to_numeric(q.minutes,errors='coerce').fillna(0)
res={}
for tm,lm in last.items():
    t=q[q.team_abbreviation==tm]; ng=t.game_id.nunique()
    seas=(t.groupby('athlete_display_name')['min'].sum()/max(ng,1)).to_dict() if ng else {}
    names={norm(n):n for n in list(lm)+list(seas)}
    sk={norm(k):v for k,v in seas.items()}; lk={norm(k):v for k,v in lm.items()}
    m={}
    for k,n in names.items():
        if k in out: continue
        s=sk.get(k); l=lk.get(k)
        if ng==0: v=l or 0
        elif s is None: v=(1-W)*(l or 0)
        elif l is None: v=s
        else: v=W*s+(1-W)*l
        if v>=6: m[n]=v
    df=pd.Series(m).sort_values(ascending=False).head(10)
    for _ in range(30):
        df=np.minimum(df*240/df.sum(),38.0)
        if abs(df.sum()-240)<0.5: break
    res[tm]={k:round(float(v),1) for k,v in df.items()}
    print(tm,ng,' | '.join(f'{k} {v:.0f}' for k,v in res[tm].items()))
json.dump(res,open(f'slate/{D}_rotations.json','w'),indent=1)
