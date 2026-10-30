"""Defense-vs-position factors (G/F/C) for points, rebounds, assists.
Blend last season + this season (weight gm/(gm+10)); applied to sims at 50% strength.
Usage: python3 dvp.py slate/MMDD   -> writes dvp_pts.csv, dvp_reb.csv, dvp_ast.csv in that folder"""
import sys, pandas as pd
D=sys.argv[1]
def pos(p): return 'G' if p in ('PG','SG','G') else ('C' if p=='C' else 'F')
fr=[]
for yr in (2026,2027):
    b=pd.read_parquet(f'repo/nba/player_box/parquet/player_box_{yr}.parquet')
    b=b[pd.to_numeric(b.minutes,errors='coerce')>=10].copy(); b['min']=pd.to_numeric(b.minutes); b['yr']=yr; b['pos']=b.athlete_position_abbreviation.map(pos)
    fr.append(b[['yr','game_id','opponent_team_abbreviation','pos','min','points','rebounds','assists']])
b=pd.concat(fr)
for st,fn in (('points','pts'),('rebounds','reb'),('assists','ast')):
    def idx(x):
        g=x.groupby(['opponent_team_abbreviation','pos']).agg(s=(st,'sum'),m=('min','sum'),gm=('game_id','nunique'))
        lg=x.groupby('pos').apply(lambda y:y[st].sum()/y['min'].sum()); g['idx']=(g.s/g.m)/g.index.get_level_values(1).map(lg); return g
    a=idx(b[b.yr==2026]); c=idx(b[b.yr==2027]); J=a[['idx']].join(c[['idx','gm']],rsuffix='_n',how='outer'); J['gm']=J.gm.fillna(0); w=J.gm/(J.gm+10)
    J['dvp']=((1-w)*J.idx.fillna(1)+w*J.idx_n.fillna(1)).round(3); J[['dvp']].to_csv(f'{D}/dvp_{fn}.csv')
print('wrote dvp files to',D)
