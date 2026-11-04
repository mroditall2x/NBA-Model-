import pandas as pd, numpy as np, sys
sys.path.insert(0,'/home/claude/nba'); from slate_names import norm
S=sys.argv[1]
pb=pd.read_parquet('repo/nba/player_box/parquet/player_box_2027.parquet'); c3=[c for c in pb.columns if 'three_point_field_goals_made' in c][0]
for c in ['minutes','points','rebounds','assists',c3,'steals','blocks']: pb[c]=pd.to_numeric(pb[c],errors='coerce')
pb=pb[pb.minutes>0]; pb['k']=pb.athlete_display_name.map(norm); pb['d']=pb.game_date.astype(str)
def act(r):
    P,R,A=r.points,r.rebounds,r.assists
    return {'PTS':P,'REB':R,'AST':A,'PA':P+A,'PR':P+R,'RA':R+A,'PRA':P+R+A,'3PM':r[c3],'STL':r.steals,'BLK':r.blocks,'Stl+Blk':r.steals+r.blocks}
imp=lambda o:(-o)/(-o+100) if o<0 else 100/(o+100)
dec=lambda o:(o/100+1) if o>0 else (100/-o+1)
def rules(B):
    B=B.copy(); B['flags']=B['flags'].fillna(''); B['adj']=0.5+0.6*(B.model-0.5)
    ok=(B['gap'].abs()<=4)&~B['flags'].str.contains('new team|small|unclear'); ok&=~((B.side=='Less')&(B['gap']>2))&~((B.side=='More')&(B['gap']<-2))
    std=B[ok&B.type.isin(['PP standard','book line'])&~B.stat.isin(['STL','BLK','STL+BLK','Stl+Blk'])]
    std=std[(std.adj>=0.58)&(std.edge>=0.05)&~((std['min']>=35)&(std.side=='Less')&(std.adj<0.62))]
    std=std[~((std.stat=='PTS')&(std.side=='Less')&(std.adj<0.60))]
    return std.sort_values('adj',ascending=False).drop_duplicates(['player','stat']),ok
rows=[]; cards={'old':[],'new':[],'new10':[],'evp':[]}
for d in ['1023','1024','1025','1026','1027','1028','1029','1030']:
    date=f'2026-{d[:2]}-{d[2:]}'; A={k:act(r) for k,r in pb[pb.d==date].drop_duplicates('k').set_index('k').iterrows()}
    for ver in ('old','new'):
        B=pd.read_csv(f'{S}/{d}/board_{ver}.csv'); B=B[B.type.isin(['PP standard','book line'])].copy()
        B['actual']=[A.get(norm(p),{}).get(s) for p,s in zip(B.player,B.stat)]; B=B.dropna(subset=['actual'])
        B['p_over_']=np.where(B.side=='More',B.model,1-B.model)
        B=B[B.actual!=B.line]; B['over']=(B.actual>B.line).astype(int)
        B['ver']=ver; B['date']=d; rows.append(B)
        C,ok=rules(B); C['win']=np.where(C.side=='More',C.over==1,C.over==0); cards[ver].append(C)
        if ver=='new':
            # new ranking: top 10 by EV where a price exists (book odds of that side) else edge vs 54.5%
            def pr(r):
                if not ('o' in r and r.o==r.o): return None
                if r.o==-119 and r.u==-119: return None
                return r.o if r.side=='More' else r.u
            C=C.copy(); C['price']=[pr(r) for _,r in C.iterrows()]
            C['ev']=[None if p_ is None else c*dec(p_)-1 for c,p_ in zip(C.adj,C.price)]
            C['score']=[e if e is not None else a-0.545 for e,a in zip(C.ev,C.adj)]
            cards['new10'].append(C.sort_values('score',ascending=False).head(10))
            # EV+ props, both sides
            for _,r in B[ok.reindex(B.index,fill_value=False)].iterrows():
                if not (r.o==r.o) or (r.o==-119 and r.u==-119): continue
                for sd,q,p_ in (('More',r.p_over_,r.o),('Less',1-r.p_over_,r.u)):
                    if abs(p_)<100: continue
                    c=0.5+0.6*(q-0.5) if q>=0.5 else q*0.95; e=c*dec(p_)-1
                    if e>=(0.08 if p_>0 else 0.05) and c>=0.25:
                        cards['evp'].append(dict(date=d,player=r.player,stat=r.stat,line=r.line,side=sd,price=p_,ev=e,win=(r.over==1) if sd=='More' else (r.over==0)))
R=pd.concat(rows)
def ll(g): p=g.p_over_.clip(.02,.98); return -(g.over*np.log(p)+(1-g.over)*np.log(1-p)).mean()
print('ALL PROPS (both versions graded on the same lines)')
for ver in ('old','new'):
    g=R[R.ver==ver]; right=((g.p_over_>0.5)==(g.over==1)).mean()
    print(f"  {ver}: {len(g)} props | model picked the right side {right:.1%} | log-loss {ll(g):.4f} (lower = better)")
m=R[R.ver=='old'][['date','player','stat','line','p_over_','over']].merge(R[R.ver=='new'][['date','player','stat','line','p_over_']],on=['date','player','stat','line'],suffixes=('_o','_n'))
fl=m[(m.p_over__o>0.5)!=(m.p_over__n>0.5)]
print(f"  side flipped by the matchup factor: {len(fl)} props -> new side right {((fl.p_over__n>0.5)==(fl.over==1)).mean():.1%}")
for st in ['PTS','REB','AST','3PM','PRA','RA']:
    gg=m[m.stat==st]; o_=((gg.p_over__o>0.5)==(gg.over==1)).mean(); n_=((gg.p_over__n>0.5)==(gg.over==1)).mean()
    print(f"    {st:4s} n={len(gg):4d} old {o_:.1%}  new {n_:.1%}")
print('\nCARD (same card rules, 58% bar)')
for ver in ('old','new','new10'):
    C=pd.concat(cards[ver]); w=int(C.win.sum()); print(f"  {ver:6s}: {w}-{len(C)-w}  ({w/len(C):.1%})  picks/day {len(C)/8:.1f}")
E=pd.DataFrame(cards['evp'])
if len(E):
    E['profit']=[(1/(1+(100/-p if p<0 else p/100)) and ((p/100) if p>0 else 100/-p)) if w else -1 for p,w in zip(E.price,E.win)]
    print(f"\nEV+ PROPS (new, both sides, 1u each): {int(E.win.sum())}-{len(E)-int(E.win.sum())}, profit {E.profit.sum():+.1f}u on {len(E)} bets ({E.profit.sum()/len(E):+.1%} ROI); plus-money ones: {int(E[E.price>0].win.sum())}-{int((~E[E.price>0].win).sum())}, {E[E.price>0].profit.sum():+.1f}u")
