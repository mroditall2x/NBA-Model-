import json, numpy as np, pandas as pd, nba_sim as S
from slate_names import norm
import sys; D=sys.argv[1]
rows=json.load(open(f'{D}/pp_compact.json')); gap=json.load(open(f'{D}/min_gap.json'))
STAT={'Points':'pts','Rebounds':'reb','Assists':'ast','Points + Assists':'pa','Points + Rebounds':'pr','Rebounds + Assists':'ra','Pts + Reb + Ast':'pra','Steals':'stl','Blocks':'blk','Steals + Blocks':'stocks','Three Pointers':'fg3m'}
AB={'Points':'PTS','Rebounds':'REB','Assists':'AST','Points + Assists':'PA','Points + Rebounds':'PR','Rebounds + Assists':'RA','Pts + Reb + Ast':'PRA','Steals':'STL','Blocks':'BLK','Steals + Blocks':'Stl+Blk','Three Pointers':'3PM'}
import glob,os; sims={os.path.basename(f)[4:-8]:pd.read_parquet(f) for f in glob.glob(f'{D}/sim_*.parquet')}
p,t=S.load((2025,2026,2027)); last=p.sort_values('game_date').groupby('pid').tail(1)
lt={norm(n):tm for n,tm in zip(last.name,last.team)}; ng=p.groupby('name').size(); ngk={norm(k):v for k,v in ng.items()}
imp=lambda o:(-o)/(-o+100) if o<0 else 100/(o+100)
# matchup (defense vs position) at the strength the 2-season backtest supported (research/dvp: pts .5 reb .25 ast .5 3pm .25 stl .5 blk .5)
W={'pts':.5,'reb':.25,'ast':.5,'fg3m':.25,'stl':.5,'blk':.5}
# 11/03 replay of 10/23-10/30 (same sims, matchup factors from prior games only): with the factor ON the card went 98-96 (50.5%)
# vs 84-68 (55.3%) OFF, and the right-side rate dropped on PTS/REB/AST. Kept OFF (strength 0) until a bigger sample says otherwise.
W={k:0.0 for k in W}
DV={}
for fn in W:
    f=f'{D}/dvp_{fn}.csv'
    if os.path.exists(f): DV[fn]=pd.read_csv(f).set_index(['opponent_team_abbreviation','pos']).dvp.to_dict()
R=pd.read_parquet(f"{S.ROOT}/rosters/parquet/rosters_2027.parquet"); _pc=[c for c in R.columns if 'position' in c and 'abbrev' in c][0]
_pos=lambda q:'G' if q in ('PG','SG','G') else ('C' if q=='C' else 'F'); POS={norm(n):_pos(q) for n,q in zip(R.display_name,R[_pc])}
def stat_vals(x,stn,opp,k):
    f=lambda c:x[c].values*(1+W[c]*(DV.get(c,{}).get((opp,POS.get(k,'F')),1.0)-1)) if c in W and c in x else x[c].values
    combo={'pa':('pts','ast'),'pr':('pts','reb'),'ra':('reb','ast'),'pra':('pts','reb','ast'),'stocks':('stl','blk')}
    if stn in combo and all(c in x for c in combo[stn]): return sum(f(c) for c in combo[stn])
    return f(stn)
# role-change check (added 11/10): this season's last few games vs the model's average. The model learns slowly
# (30-game half-life), so a player whose role just grew (Wagner/Draymond AST in early Nov) still projects low.
# 'role up' blocks Unders and 'role down' blocks Overs on that stat (see run_day card rules).
RECENT_N=8
_md=D.rstrip('/')[-4:]; _slate_date=pd.Timestamp(f"{2026 if int(_md[:2])>=9 else 2027}-{_md[:2]}-{_md[2:]}")
_cur=p[(p.season==p.season.max())&(p.game_date<_slate_date)].copy(); _cur['k']=_cur.name.map(norm)
_cur['pa']=_cur.pts+_cur.ast; _cur['pr']=_cur.pts+_cur.reb; _cur['ra']=_cur.reb+_cur.ast; _cur['pra']=_cur.pts+_cur.reb+_cur.ast; _cur['stocks']=_cur.stl+_cur.blk
# 11/13: a player whose starter/bench role flipped is judged only on games in his current role once that streak is 4+
# games (Ayo Dosunmu 11/12: 7 straight starts, PR 27.0 vs model 21.7, but the flat last 8 still held a bench game and
# missed the 25% bar). Replay 10/28-11/11 (research/replay_role_streak.py): card 58-37 vs 59-37, i.e. neutral; shipped
# as a safety rule. 'started last N' / 'bench last N' is informational (no card rule reads it).
def _window(x):
    s=x.starter.astype(bool).values[::-1]; n=1
    while n<len(s) and s[n]==s[0]: n+=1
    return (x.tail(min(n,RECENT_N)) if n>=4 else x.tail(RECENT_N)), n, bool(s[0])
_byk,_role={},{}; _ngames=_cur.groupby('k').size().to_dict()
for k,x in _cur.sort_values('game_date').groupby('k'):
    _byk[k],n,st=_window(x); _role[k]=(n,st)
# returning players (rot_blend.py, 11/10): the returner's own minutes are a guess first game back -> 'minutes unclear';
# teammates' recent bump came while he was out -> 'teammate back' (blocks Overs, replaces role up)
_rf=f"slate/{_slate_date.date()}_returning.json"
_RET=json.load(open(_rf)) if os.path.exists(_rf) else {}
RET_K={tm:{norm(r['player']):r for r in rs} for tm,rs in _RET.items()}
RET_REG={tm:[r['player'] for r in rs if r['normal_min']>=20] for tm,rs in _RET.items()}
def recent_avg(k,stn):
    x=_byk.get(k)
    if x is None or len(x)<4 or stn not in x or _ngames.get(k,0)<5: return None
    return float(x[stn].mean())
out=[]
for g,pl,st,l,o,u,pp,gob,dem in rows:
    k=norm(pl); x=sims.get(g); x=x[x.key==k] if x is not None else pd.DataFrame()
    if not len(x): continue
    team=x.team.iloc[0] if 'team' in x else ''; _a,_h=g.split('@'); opp=_h if team==_a else _a
    v=stat_vals(x,STAT[st],opp,k)
    def pov(L): po,pu=(v>L).mean(),(v<L).mean(); return po/(po+pu) if po+pu else .5
    flags=[]
    gp=gap.get(k,0)
    if abs(gp)>4: flags.append(f'minutes unclear ({gp:+.0f})')
    if lt.get(k) and lt[k]!=team: flags.append('new team')
    if ngk.get(k,0)<60: flags.append('small sample')
    rv=recent_avg(k,STAT[st]); mv=float(v.mean())
    if k in _role and _role[k][0]>=3: flags.append(f"{'started' if _role[k][1] else 'bench'} last {_role[k][0]}")
    if k in RET_K.get(team,{}): flags.append(f"returning (missed {RET_K[team][k]['missed']}) - minutes unclear")
    elif RET_REG.get(team) and rv is not None and mv>0 and rv>=1.15*mv:
        flags.append(f"teammate back ({', '.join(RET_REG[team])}; last {RECENT_N}: {rv:.1f})")
    elif rv is not None and mv>0:
        dmin={'pts':4,'pa':4,'pr':4,'pra':5,'ra':2}.get(STAT[st],1.0)
        if rv>=1.25*mv and rv-mv>=dmin: flags.append(f'role up (last {RECENT_N}: {rv:.1f})')
        elif rv<=0.75*mv and mv-rv>=dmin: flags.append(f'role down (last {RECENT_N}: {rv:.1f})')
    base=dict(game=g,team=team,player=pl,stat=AB[st],mean=round(v.mean(),2),lo=int(np.percentile(v,20)),hi=int(np.percentile(v,80)),min=round(x['min'].mean(),1),gap=gp,flags='; '.join(flags))
    if l:
        L=float(l); q=pov(L); side='More' if q>.5 else 'Less'; P=max(q,1-q)
        mk=imp(int(o))/(imp(int(o))+imp(int(u))); mk=mk if side=='More' else 1-mk
        out.append({**base,'type':'PP standard' if pp else 'book line','line':L,'side':side,'model':round(P,3),'market':round(mk,3),'edge':round(P-mk,3),'p_over':round(q,3),'o':int(o),'u':int(u)})
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
