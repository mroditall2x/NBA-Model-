import json, numpy as np, pandas as pd, nba_sim as S
from slate_names import norm
import sys; D=sys.argv[1]
rows=json.load(open(f'{D}/pp_compact.json')); gap=json.load(open(f'{D}/min_gap.json'))
STAT={'Points':'pts','Rebounds':'reb','Assists':'ast','Points + Assists':'pa','Points + Rebounds':'pr','Rebounds + Assists':'ra','Pts + Reb + Ast':'pra','Steals':'stl','Blocks':'blk','Steals + Blocks':'stocks'}
AB={'Points':'PTS','Rebounds':'REB','Assists':'AST','Points + Assists':'PA','Points + Rebounds':'PR','Rebounds + Assists':'RA','Pts + Reb + Ast':'PRA','Steals':'STL','Blocks':'BLK','Steals + Blocks':'Stl+Blk'}
import glob,os; sims={os.path.basename(f)[4:-8]:pd.read_parquet(f) for f in glob.glob(f'{D}/sim_*.parquet')}
p,t=S.load((2025,2026)); last=p.sort_values('game_date').groupby('pid').tail(1)
lt={norm(n):tm for n,tm in zip(last.name,last.team)}; ng=p.groupby('name').size(); ngk={norm(k):v for k,v in ng.items()}
imp=lambda o:(-o)/(-o+100) if o<0 else 100/(o+100)
out=[]
for g,pl,st,l,o,u,pp,gob,dem in rows:
    k=norm(pl); x=sims.get(g); x=x[x.key==k] if x is not None else pd.DataFrame()
    if not len(x): continue
    v=x[STAT[st]].values; team=x.team.iloc[0] if 'team' in x else ''
    def pov(L): po,pu=(v>L).mean(),(v<L).mean(); return po/(po+pu) if po+pu else .5
    flags=[]
    gp=gap.get(k,0)
    if abs(gp)>4: flags.append(f'minutes unclear ({gp:+.0f})')
    if lt.get(k) and lt[k]!=team: flags.append('new team')
    if ngk.get(k,0)<60: flags.append('small sample')
    base=dict(game=g,team=team,player=pl,stat=AB[st],mean=round(v.mean(),2),min=round(x['min'].mean(),1),gap=gp,flags='; '.join(flags))
    if l:
        L=float(l); q=pov(L); side='More' if q>.5 else 'Less'; P=max(q,1-q)
        mk=imp(int(o))/(imp(int(o))+imp(int(u))); mk=mk if side=='More' else 1-mk
        out.append({**base,'type':'PP standard' if pp else 'book line','line':L,'side':side,'model':round(P,3),'market':round(mk,3),'edge':round(P-mk,3)})
    for L in [float(z) for z in gob.split(',') if z]:
        out.append({**base,'type':'goblin','line':L,'side':'More','model':round(pov(L),3),'market':None,'edge':round(pov(L)-.70,3)})
    for L in [float(z) for z in dem.split(',') if z]:
        out.append({**base,'type':'demon','line':L,'side':'More','model':round(pov(L),3),'market':None,'edge':round(pov(L)-.42,3)})
B=pd.DataFrame(out); B.to_csv(f'{D}/board_all.csv',index=False)
pd.set_option('display.width',230)
B['where']=B.type.map({'PP standard':'PrizePicks / Underdog','book line':'Kalshi / Underdog','goblin':'PrizePicks (goblin)','demon':'PrizePicks (demon)'})
B.to_csv(f'{D}/board_all.csv',index=False)
for ty in ['PP standard','book line','goblin','demon']:
    d=B[B.type==ty].sort_values('edge',ascending=False)
    print('\n==',ty); print(d.head(16)[['game','player','stat','line','side','model','market','edge','mean','min','gap','flags']].to_string(index=False))
