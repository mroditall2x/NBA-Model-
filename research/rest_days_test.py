import pandas as pd, numpy as np
rows=[]
for yr in (2024,2025,2026):
    t=pd.read_parquet(f'repo/nba/team_box/parquet/team_box_{yr}.parquet',columns=['game_id','season_type','game_date','team_id','team_abbreviation','team_home_away','team_score','opponent_team_id','opponent_team_score'])
    t=t[t.season_type==2].copy(); t['game_date']=pd.to_datetime(t.game_date)
    t=t.sort_values('game_date'); t['rest']=t.groupby('team_id').game_date.diff().dt.days-1
    t['margin']=t.team_score-t.opponent_team_score; t['home']=(t.team_home_away=='home').astype(int)*2-1
    # season ratings by least squares: margin = r_team - r_opp + h*home
    teams=sorted(t.team_id.unique()); ix={k:i for i,k in enumerate(teams)}
    h=t[t.home==1]; X=np.zeros((len(h),len(teams)+1)); 
    for k,(a,b) in enumerate(zip(h.team_id,h.opponent_team_id)): X[k,ix[a]]=1; X[k,ix[b]]=-1
    X[:,-1]=1; X=np.vstack([X,np.r_[np.ones(len(teams)),0]]); y=np.r_[h.margin.values,0]
    beta=np.linalg.lstsq(X,y,rcond=None)[0]; r={k:beta[ix[k]] for k in teams}; hca=beta[-1]
    t['exp']=[r[a]-r[b]+hca*hm/1 if hm==1 else r[a]-r[b]-hca for a,b,hm in zip(t.team_id,t.opponent_team_id,t.home)]
    t['resid']=t.margin-t.exp
    o=t[['game_id','team_id','rest']].rename(columns={'team_id':'opponent_team_id','rest':'opp_rest'})
    t=t.merge(o,on=['game_id','opponent_team_id'],how='left'); t['season']=yr; t['total']=t.team_score+t.opponent_team_score
    rows.append(t)
T=pd.concat(rows).dropna(subset=['rest','opp_rest'])
T['rest_c']=T.rest.clip(upper=7).astype(int)
def tab(g):
    return pd.Series(dict(games=len(g), vs_expected=round(g.resid.mean(),2), beat_expect=round((g.resid>0).mean(),3)))
print('BY OWN DAYS OFF (0 = back-to-back, 7 = a week or more)\n', T.groupby('rest_c').apply(tab).to_string())
T['edge']=(T.rest.clip(upper=4)-T.opp_rest.clip(upper=4)).clip(-3,3).astype(int)
print('\nBY REST ADVANTAGE vs opponent (+ = more rest)\n', T.groupby('edge').apply(tab).to_string())
print('\nBACK-TO-BACK by home/road\n', T[T.rest==0].groupby('home').apply(tab).rename(index={1:'home',-1:'road'}).to_string())
# totals: game total residual vs expected (season avg of both teams' games)
G=T[T.home==1].copy(); avg=pd.concat([T.groupby(['season','team_id']).total.mean()]).to_dict()
G['exp_tot']=[ (avg[(s,a)]+avg[(s,b)])/2 for s,a,b in zip(G.season,G.team_id,G.opponent_team_id)]
G['tres']=G.total-G.exp_tot; G['b2b']=(G.rest==0).astype(int)+(G.opp_rest==0).astype(int)
print('\nGAME TOTAL vs expected, by # of teams on a back-to-back\n', G.groupby('b2b').apply(lambda g: pd.Series(dict(games=len(g),total_vs_expected=round(g.tres.mean(),2),under_rate=round((g.tres<0).mean(),3)))).to_string())
T.to_parquet('/tmp/claude-0/-home-claude/13d65212-cf7e-5127-9f97-0d56f50f8429/scratchpad/rest_team.parquet')
