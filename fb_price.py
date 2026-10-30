import json, numpy as np, pandas as pd
import nba_sim as S, first_basket as F
from slate_names import norm
D='slate/1022'
p,t=S.load((2025,2026)); fbm=F.fit(F.build(),p)
R=pd.read_parquet(f'{S.ROOT}/rosters/parquet/rosters_2027.parquet'); R['pid']=R.athlete_id.astype('int64')
rt={norm(n):(pid,tm) for n,pid,tm in zip(R.display_name,R.pid,R.team_abbreviation)}
last=p.sort_values('game_date').groupby('pid').tail(1); hist={norm(n):pid for n,pid in zip(last.name,last.pid)}
cur=p[p.season==p.season.max()]; srate=cur.groupby('pid').starter.mean(); smin=cur.groupby('pid')['min'].mean()
rpm=p.groupby('pid').reb.sum()/p.groupby('pid')['min'].sum(); tipn=fbm['tip'].tips
# rookies: no first-FG history -> treat as a low-usage starter
for k,(pid,_) in rt.items():
    if pid not in fbm['share'].index: fbm['share'].loc[pid]=dict(starts=0,team_firsts=0,fbs=0,fga_share=0.17,share=0.17)
# temper tiny samples harder (Jerome/Hunter/Allen problem): extra shrink to 0.2 below 40 starts
sh=fbm['share']; w=np.clip(sh.starts/60,0,1); sh['share']=np.where(sh.starts<60, w*sh.share+(1-w)*sh.fga_share.fillna(0.2), sh.share)
odds=json.load(open(f'{D}/fb_odds.json')); lines={f"{g['away']}@{g['home']}":g for g in json.load(open(f'{D}/lines.json'))['games']}
out=[]
BENCH=set(); FORCE=set()
for gk,lst in odds.items():
    g=lines[gk]; home,away=g['home'],g['away']
    team={}
    for n,o in lst:
        k=norm(n); pid,tm=rt.get(k,(hist.get(k),None))
        if tm not in (home,away): tm=None
        team[n]=(pid,tm,o)
    st={}
    for tm in (home,away):
        c=[(n,v[0]) for n,v in team.items() if v[1]==tm]
        c.sort(key=lambda x:(x[0] in BENCH, x[0] not in FORCE, -(smin.get(x[1],22)*(0.4+srate.get(x[1],0.6)))))
        st[tm]=c[:5]
    hs=[x[1] for x in st[home]]; as_=[x[1] for x in st[away]]
    jh=max(hs,key=lambda x:(tipn.get(x,0),rpm.get(x,0))); ja=max(as_,key=lambda x:(tipn.get(x,0),rpm.get(x,0)))
    names={pid:n for n,(pid,_,_) in team.items()}
    r=F.price(fbm,hs,as_,jh,ja,names=names); tb=r['table']
    imp=lambda o:100/(o+100)
    s=sum(imp(o) for _,(_,_,o) in team.items())
    tb['team']=np.where(tb.side=='home',home,away); tb.insert(0,'game',gk)
    tb['book']=tb.player.map(lambda n:team[n][2]); tb['book_novig']=tb.book.map(lambda o:imp(o)/s)
    tb['edge']=tb.p_first_fg-tb.book_novig; tb['ev']=tb.p_first_fg*(tb.book/100+1)-1
    tb['jumper']=tb.pid.isin([jh,ja]); tb['p_team_first']=np.where(tb.side=='home',r['p_home_first'],1-r['p_home_first'])
    extra=[n for n in team if n not in tb.player.values]
    tb['bench_listed']=', '.join(extra)
    out.append(tb)
    print(f"{gk} jumpers {names[ja]} v {names[jh]} P({home} 1st)={r['p_home_first']} hold={s-1:.0%} not-starting:{extra}")
A=pd.concat(out); A.to_csv(f'{D}/fb_priced.csv',index=False)
pd.set_option('display.width',200)
print(A.sort_values('ev',ascending=False)[['game','player','p_first_fg','fair_odds','book','ev','starts_sample']].head(25).to_string(index=False))
