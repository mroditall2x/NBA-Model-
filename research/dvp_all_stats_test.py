"""Does 'what this defense allows to this position' predict a player's stat beyond his own average? (out-of-sample, rolling)"""
import pandas as pd, numpy as np
out=[]
for yr in (2025,2026):
    p=pd.read_parquet(f'repo/nba/player_box/parquet/player_box_{yr}.parquet')
    p=p[p.season_type==2].copy()
    c3=[c for c in p.columns if 'three_point_field_goals_made' in c][0]
    p=p.rename(columns={c3:'tpm'})
    for c in ['minutes','points','rebounds','assists','tpm','steals','blocks','offensive_rebounds']: p[c]=pd.to_numeric(p[c],errors='coerce')
    p=p[p.minutes>=10].copy()
    pos=p.athlete_position_abbreviation.fillna('')
    p['pos']=np.where(pos.str.contains('C'),'C',np.where(pos.str.contains('G'),'G','F'))
    p['game_date']=pd.to_datetime(p.game_date); p=p.sort_values('game_date')
    stats=['points','rebounds','assists','tpm','steals','blocks','offensive_rebounds']
    for s in stats: p[s+'_pm']=p[s]/p.minutes
    # player's own prior per-minute rate (expanding, prior games only)
    g=p.groupby('athlete_id')
    for s in stats: p[s+'_own']=g[s+'_pm'].transform(lambda x:x.shift().expanding().mean())
    p['n_own']=g.cumcount()
    # what the opponent allowed to this position, per minute, relative to league, prior games only
    for s in stats:
        lg=p.groupby('pos')[s+'_pm'].transform('mean')
        p[s+'_rel']=p[s+'_pm']/lg
        p[s+'_dvp']=p.groupby(['opponent_team_id','pos'])[s+'_rel'].transform(lambda x:x.shift().expanding().mean())
    p['n_dvp']=p.groupby(['opponent_team_id','pos']).cumcount()
    p['season']=yr; out.append(p)
P=pd.concat(out); P=P[(P.n_own>=10)&(P.n_dvp>=20)]
rows=[]
for s,name in [('points','Points'),('rebounds','Rebounds'),('assists','Assists'),('tpm','3-pointers'),('steals','Steals'),('blocks','Blocks'),('offensive_rebounds','Off. rebounds')]:
    x=P.dropna(subset=[s+'_own',s+'_dvp']); x=x[x[s+'_own']>0]
    actual=x[s]; base=x[s+'_own']*x.minutes          # what his own average says (given the minutes he played)
    d=x[s+'_dvp']-1
    best=None
    for w in (0,0.25,0.5,0.75,1.0):
        pred=base*(1+w*d); err=((actual-pred)**2).mean()
        if best is None or err<best[1]: best=(w,err)
    e0=((actual-base)**2).mean()
    soft=x[d>0.15]; tough=x[d<-0.15]
    rows.append(dict(stat=name, best_strength=best[0], error_cut=f"{(1-best[1]/e0)*100:.1f}%",
        soft_D_vs_own_avg=round((soft[s]/(soft[s+'_own']*soft.minutes)).mean()-1,3), tough_D_vs_own_avg=round((tough[s]/(tough[s+'_own']*tough.minutes)).mean()-1,3),
        n=len(x)))
print(pd.DataFrame(rows).to_string(index=False))
# by position for reb/ast/3pm
for s in ['rebounds','assists','tpm']:
    x=P.dropna(subset=[s+'_own',s+'_dvp']); x=x[x[s+'_own']>0]; d=x[s+'_dvp']-1
    r=x.assign(soft=d>0.15,tough=d<-0.15,ratio=x[s]/(x[s+'_own']*x.minutes)-1)
    print(s, r.groupby('pos').apply(lambda g: f"soft D {g[g.soft].ratio.mean():+.3f} (n={g.soft.sum()}) | tough D {g[g.tough].ratio.mean():+.3f} (n={g.tough.sum()})").to_dict())
