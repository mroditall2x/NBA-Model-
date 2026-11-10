import pandas as pd, numpy as np, sys
sys.path.insert(0,'.'); from slate_names import norm
R=sys.argv[1]   # folder with one repo copy per version (old/new/fast/role), each with rebuilt slate/MMDD/board_all.csv
pb=pd.read_parquet('/home/claude/nba/repo/nba/player_box/parquet/player_box_2027.parquet')
c3=[c for c in pb.columns if 'three_point_field_goals_made' in c][0]
for c in ['minutes','points','rebounds','assists',c3,'steals','blocks']: pb[c]=pd.to_numeric(pb[c],errors='coerce')
pb=pb[pb.minutes>0]; pb['k']=pb.athlete_display_name.map(norm); pb['d']=pb.game_date.astype(str).str[:10]
def act(r):
    P,Rb,A=r.points,r.rebounds,r.assists
    return {'PTS':P,'REB':Rb,'AST':A,'PA':P+A,'PR':P+Rb,'RA':Rb+A,'PRA':P+Rb+A,'3PM':r[c3],'STL':r.steals,'BLK':r.blocks,'Stl+Blk':r.steals+r.blocks}
DAYS=['1028','1030','1031','1101','1102','1104','1105','1106','1107','1108']
ROLE=False
def card_rules(B):
    B=B.copy(); B['flags']=B['flags'].fillna(''); B['adj']=0.5+0.6*(B.model-0.5)
    ok=(B['gap'].abs()<=4)&~B['flags'].str.contains('new team|small|unclear')
    ok&=~((B.side=='Less')&(B['gap']>2))&~((B.side=='More')&(B['gap']<-2))
    if ROLE: ok&=~((B.side=='Less')&B['flags'].str.contains('role up'))&~((B.side=='More')&B['flags'].str.contains('role down'))
    std=B[ok&B.type.isin(['PP standard','book line'])&~B.stat.isin(['STL','BLK','STL+BLK'])]
    std=std[(std.adj>=0.58)&(std.edge>=0.05)&~((std['min']>=35)&(std.side=='Less')&(std.adj<0.62))]
    std=std[~((std.stat=='PTS')&(std.side=='Less')&(std.adj<0.60))]
    gob=B[ok&(B.type=='goblin')&(B.model>=0.84)]
    card=pd.concat([std.assign(tier='standard',p=std.adj),gob.assign(tier='goblin',p=gob.model)])
    card=card.sort_values('p',ascending=False).drop_duplicates(['player','stat'])
    return card, card.head(10)
allrows=[]; pools=[]; cards=[]
for v in ('old','new','fast','role'):
    for d in DAYS:
        date=f'2026-{d[:2]}-{d[2:]}'
        A={k:act(r) for k,r in pb[pb.d==date].drop_duplicates('k').set_index('k').iterrows()}
        B=pd.read_csv(f'{R}/{v}/slate/{d}/board_all.csv')
        B['actual']=[A.get(norm(p),{}).get(s) for p,s in zip(B.player,B.stat)]
        B=B.dropna(subset=['actual']); B=B[B.actual!=B.line]
        B['over']=(B.actual>B.line).astype(int); B['win']=np.where(B.side=='More',B.over==1,B.over==0).astype(int)
        B['v']=v; B['d']=d
        ROLE=(v=="role")
        pool,card=card_rules(B); pools.append(pool.assign(v=v,d=d)); cards.append(card.assign(v=v,d=d,top10=True))
        allrows.append(B)
A=pd.concat(allrows); P=pd.concat(pools); C=pd.concat(cards)
def rec(x): return f"{x.win.sum()}-{len(x)-x.win.sum()} ({x.win.mean():.1%}, n={len(x)})"
for v in ('old','new','fast','role'):
    print(f'\n===== {v.upper()} =====')
    a=A[(A.v==v)&A.type.isin(['PP standard','book line'])]
    po=a.p_over.clip(.01,.99); mk=np.where(a.side=='More',a.market,1-a.market)
    print('Brier model (all std lines):',round(((po-a.over)**2).mean(),4),' market:',round(((mk-a.over)**2).mean(),4),' n=',len(a))
    c=C[C.v==v]; print('Top-10 card:',rec(c)); print('  Unders',rec(c[c.side=='Less']),' Overs',rec(c[(c.side=='More')]))
    p=P[P.v==v]; print('Full qualifying pool:',rec(p))
    print('  standard Unders',rec(p[(p.tier=='standard')&(p.side=='Less')]),'\n  standard Overs',rec(p[(p.tier=='standard')&(p.side=='More')]),'\n  goblins',rec(p[p.tier=='goblin']))
    print('  by day (card):',' '.join(f"{d}:{x.win.sum()}-{len(x)-x.win.sum()}" for d,x in c.groupby('d')))
    for st in ['AST','3PM','REB','PTS','RA']:
        q=c[c.stat==st]
        if len(q): print(f'  card {st}:',rec(q))
# example players
for who in ['Franz Wagner','Draymond Green','Kyshawn George','Myles Turner']:
    x=A[(A.player==who)&(A.stat=='AST')&A.type.isin(['PP standard','book line'])][['v','d','line','mean','side','model','actual']]
    print('\n',who,'AST'); print(x.pivot_table(index=['d','line','actual'],columns='v',values='mean').to_string())
