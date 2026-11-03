"""python3 grade_day.py 2026-10-30  -> grades slate/MMDD/card.csv (+ extra_props.csv if present) vs hoopR box scores,
appends graded_log.csv and prints record by tier/stat-group."""
import sys, pandas as pd
from slate_names import norm
DATE=sys.argv[1]; D=f'slate/{DATE[5:7]+DATE[8:10]}'
import os
E=None
if os.path.exists(f'{D}/espn_box.csv'):                    # same-night grading from ESPN (finished games only)
    E=pd.read_csv(f'{D}/espn_box.csv'); E['k']=E.player.map(norm); E=E.drop_duplicates('k').set_index('k')
    Q=E.rename(columns={'PTS':'points','REB':'rebounds','AST':'assists','BLK':'blocks','STL':'steals'}); f3='3PM'; done=set(E.game)
else:
    q=pd.read_parquet('repo/nba/player_box/parquet/player_box_2027.parquet'); q=q[q.game_date.astype(str)==DATE].copy()
    if q.empty: sys.exit('box scores not posted yet')
    q['k']=q.athlete_display_name.map(norm); Q=q.drop_duplicates('k').set_index('k'); f3=[c for c in q.columns if 'three_point_field_goals_made' in c][0]; done=None
def stat(n,s):
    k=norm(n)
    if k not in Q.index or not Q.loc[k].minutes: return None
    r=Q.loc[k]; P,R,A=r.points,r.rebounds,r.assists
    return {'PTS':P,'REB':R,'AST':A,'RA':R+A,'PR':P+R,'PA':P+A,'PRA':P+R+A,'3PM':r[f3],'BLK':r.blocks,'STL':r.steals,'SB':r.steals+r.blocks,'STL+BLK':r.steals+r.blocks}.get(s)
if os.path.exists(f'{D}/by_team.csv'):                      # grade the by-team list too (board + review)
    T=pd.read_csv(f'{D}/by_team.csv')
    if done is not None: T=T[T.game.isin(done)]
    T['actual']=[stat(p,s) for p,s in zip(T.player,T.stat)]
    T['result']=['DNP' if pd.isna(a) else 'Push' if a==l else 'Win' if ((a>l) if sd=='More' else (a<l)) else 'Loss' for a,l,sd in zip(T.actual,T.line,T.side)]
    T.to_csv(f'{D}/by_team_graded.csv',index=False); print(T[['game','team','player','stat','side','line','actual','result','grade']].to_string(index=False))
C=pd.read_csv(f'{D}/card.csv')
partial=done is not None and not set(C.game)<=done
if done is not None: C=C[C.game.isin(done)]
C['actual']=[stat(p,s) for p,s in zip(C.player,C.stat)]
C['result']=['DNP' if pd.isna(a) else'Push' if a==l else 'Win' if ((a>l) if sd=='More' else (a<l)) else 'Loss' for a,l,sd in zip(C.actual,C.line,C.side)]
C['group']=C.stat.map(lambda s:'points' if s in('PTS','PA','PR','PRA') else 'reb/ast' if s in('REB','AST','RA') else 'other')
C.to_csv(f'{D}/card_graded.csv',index=False)
print(C.groupby(['tier','group']).result.value_counts().unstack(fill_value=0))
G=C[C.result.isin(['Win','Loss','Push'])].copy(); G['call']=G.side; G['date']=DATE; G['model_p']=G.p
cols=open('graded_log.csv').readline().strip().split(',')
for c in cols:
    if c not in G: G[c]=''
if partial: print('partial day (games still to finish) -> not logged yet')
if '--no-log' not in sys.argv and not partial:
    L=pd.read_csv('graded_log.csv'); L=L[L.date.astype(str)!=DATE]; L.to_csv('graded_log.csv',index=False)   # re-grading a day replaces it, never duplicates
    G[cols].to_csv('graded_log.csv',mode='a',header=False,index=False)
    print(len(G),'picks logged for',DATE)

if os.path.exists(f'{D}/early_status.csv') or os.path.exists(f'{D}/card_early.csv'):
    X=pd.read_csv(f'{D}/early_status.csv') if os.path.exists(f'{D}/early_status.csv') else pd.read_csv(f'{D}/card_early.csv').assign(status='Hold')
    if done is not None: X=X[X.game.isin(done)]
    X['actual']=[stat(p_,s_) for p_,s_ in zip(X.player,X.stat)]
    X['result']=['DNP' if pd.isna(a) else'Push' if a==l else 'Win' if ((a>l) if sd=='More' else (a<l)) else 'Loss' for a,l,sd in zip(X.actual,X.line,X.side)]
    X['date']=DATE; X.to_csv(f'{D}/early_graded.csv',index=False)
    if '--no-log' not in sys.argv and not partial:
        EL=pd.read_csv('early_log.csv') if os.path.exists('early_log.csv') else pd.DataFrame()
        if len(EL): EL=EL[EL.date.astype(str)!=DATE]
        pd.concat([EL,X]).to_csv('early_log.csv',index=False)
    print(X.groupby('status').result.value_counts().unstack(fill_value=0))
