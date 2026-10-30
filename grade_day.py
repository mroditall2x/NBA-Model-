"""python3 grade_day.py 2026-10-30  -> grades slate/MMDD/card.csv (+ extra_props.csv if present) vs hoopR box scores,
appends graded_log.csv and prints record by tier/stat-group."""
import sys, pandas as pd
from slate_names import norm
DATE=sys.argv[1]; D=f'slate/{DATE[5:7]+DATE[8:10]}'
q=pd.read_parquet('repo/nba/player_box/parquet/player_box_2027.parquet'); q=q[q.game_date.astype(str)==DATE].copy()
if q.empty: sys.exit('box scores not posted yet')
q['k']=q.athlete_display_name.map(norm); Q=q.drop_duplicates('k').set_index('k'); f3=[c for c in q.columns if 'three_point_field_goals_made' in c][0]
def stat(n,s):
    k=norm(n)
    if k not in Q.index or not Q.loc[k].minutes: return None
    r=Q.loc[k]; P,R,A=r.points,r.rebounds,r.assists
    return {'PTS':P,'REB':R,'AST':A,'RA':R+A,'PR':P+R,'PA':P+A,'PRA':P+R+A,'3PM':r[f3],'BLK':r.blocks,'STL':r.steals,'SB':r.steals+r.blocks,'STL+BLK':r.steals+r.blocks}.get(s)
C=pd.read_csv(f'{D}/card.csv')
C['actual']=[stat(p,s) for p,s in zip(C.player,C.stat)]
C['result']=['DNP' if a is None else 'Push' if a==l else 'Win' if ((a>l) if sd=='More' else (a<l)) else 'Loss' for a,l,sd in zip(C.actual,C.line,C.side)]
C['group']=C.stat.map(lambda s:'points' if s in('PTS','PA','PR','PRA') else 'reb/ast' if s in('REB','AST','RA') else 'other')
C.to_csv(f'{D}/card_graded.csv',index=False)
print(C.groupby(['tier','group']).result.value_counts().unstack(fill_value=0))
G=C[C.result.isin(['Win','Loss','Push'])].copy(); G['call']=G.side; G['date']=DATE; G['model_p']=G.p
cols=open('graded_log.csv').readline().strip().split(',')
for c in cols:
    if c not in G: G[c]=''
if '--no-log' not in sys.argv: G[cols].to_csv('graded_log.csv',mode='a',header=False,index=False)
