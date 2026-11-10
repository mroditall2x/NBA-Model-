"""Blend this-season minutes (player_box 2027 before DATE) with last-season defaults. Usage: rot_blend.py DATE W_SEASON

11/10 returning players. A starter who missed games looked like a part-timer when he came back, because this-season
minutes are averaged over every TEAM game (Dejounte Murray 11/04: given 24, played 45; Max Strus 11/02: 13 vs 23;
Jalen Johnson 11/07: 28 vs 36). Now:
- Returning player = active today (not on the out list) after missing 2+ straight team games (no box row or an injury
  DNP). If his game has props, he needs a line of his own (no line = still out); if the game has no props at all, only
  regulars (20+ min, played this season) count. He gets his normal minutes (average of games he was available for,
  blended with last season) x RET_F (0.9) and is written to slate/DATE_returning.json. card_slate.py flags him
  'minutes unclear' (off the card) and flags teammates whose recent bump came while he was out ('teammate back': no Overs).
- Everyone else keeps the original per-team-game rule (AVAIL=0). Replay 10/28-11/08: availability-based minutes for
  everyone (AVAIL=1) had better minutes error but a worse card (63% vs 71%), so it is off; DROP_OUT=1 (drop players
  missing 2+ games with no line today) did not help either. Returner minutes error: bias -4.9 -> +2.0 min (13 cases).
"""
import sys,os,json,numpy as np,pandas as pd
from slate_names import norm
D=sys.argv[1]; W=float(sys.argv[2]) if len(sys.argv)>2 else 0.6
RECENT=8          # available games used for this-season minutes
RET_F=float(os.environ.get('RET_F',0.9))   # first game back: share of normal minutes
AVAIL=int(os.environ.get('AVAIL',0)); DROP_OUT=int(os.environ.get('DROP_OUT',0))   # both off: see replay note above
last=json.load(open(f'slate/{D}_rot_last.json')); out={norm(x) for x in json.load(open(f'slate/{D}_out.json'))}
q=pd.read_parquet('repo/nba/player_box/parquet/player_box_2027.parquet'); q=q[q.game_date.astype(str)<D].copy()
q['min']=pd.to_numeric(q.minutes,errors='coerce').fillna(0); q['d']=q.game_date.astype(str).str[:10]
q['k']=q.athlete_display_name.map(norm)
q['coach_dnp']=(q['min']<=0)&(q.reason.fillna('').str.upper()=="COACH'S DECISION")
q['avail']=(q['min']>0)|q.coach_dnp
# who has a prop line today (props pull + PrizePicks) = expected to play; used to tell a real return from a player
# who is still out but missing from the injury feed (inactive, G League, long-term injury not listed)
import glob,os
MMDD=D[5:7]+D[8:10]; HASPROP=set(); PROPGAMES=set()
for f in glob.glob(f'slate/{MMDD}/props_p*.txt'):
    for l in open(f):
        if l.count('|')>=5: HASPROP.add(norm(l.split('|')[1])); PROPGAMES.add(l.split('|')[0])
if os.path.exists(f'slate/{MMDD}/pp_compact.json'):
    for r in json.load(open(f'slate/{MMDD}/pp_compact.json')): HASPROP.add(norm(r[1])); PROPGAMES.add(r[0])
has_props=lambda tm: any(tm in g.split('@') for g in PROPGAMES)
res,ret={},{}
for tm,lm in last.items():
    t=q[q.team_abbreviation==tm]; glist=t[['game_id','d']].drop_duplicates().sort_values('d').game_id.tolist(); ng=len(glist)
    lk={norm(k):v for k,v in lm.items()}
    tk=sorted(set(t.k)); names={**{norm(n):n for n in t.athlete_display_name}, **{norm(n):n for n in lm}}
    av={k:t[(t.k==k)&t.avail].set_index('game_id') for k in tk}
    def streak(k):                      # team games missed in a row, counting back from the latest
        a=av.get(k); s=0
        for g in reversed(glist):
            if a is not None and g in a.index: break
            s+=1
        return s
    def season_min(k,games=None):
        a=av.get(k)
        if a is None or not len(a): return None,0
        a=a[a.index.isin(games)] if games is not None else a
        a=a.loc[[g for g in glist if g in a.index]].tail(RECENT)
        return (float(a['min'].mean()),len(a)) if len(a) else (None,0)
    def blend(k,games=None):
        s,n=season_min(k,games); l=lk.get(k)
        if ng==0 or s is None: return l
        if l is None: return s
        w=W*min(n,5)/5                   # few games -> lean on last season
        return w*s+(1-w)*l
    tot=t.groupby('k')['min'].sum()/max(ng,1)
    def old_blend(k):                    # original rule: this-season minutes per TEAM game
        s=tot.get(k); l=lk.get(k)
        if ng==0: return l or 0
        if s is None: return (1-W)*(l or 0)
        if l is None: return s
        return W*s+(1-W)*l
    # returning players: active today (not OUT), missed 2+ straight team games
    R={}; still_out=set()
    if ng>=2:
        for k in names:
            if k in out: continue
            mstreak=streak(k); base=blend(k)
            if mstreak<2 or not base: continue
            if has_props(tm):
                if k not in HASPROP: still_out.add(k); continue  # game has props but he has none -> treat as still out
            elif mstreak>=ng or base<20: still_out.add(k); continue   # no props for this game: only real regulars count as back
            if base>=12:
                R[k]=dict(player=names[k],missed=mstreak if mstreak<ng else 'all season',normal_min=round(base,1),
                          proj_min=round(base*RET_F,1))
    m={}
    for k,n in names.items():
        if k in out or (DROP_OUT and k in still_out): continue
        v=R[k]['proj_min'] if k in R else (blend(k) if AVAIL else old_blend(k))
        if v and v>=6: m[n]=v
    df=pd.Series(m,dtype=float).sort_values(ascending=False).head(10)
    for _ in range(30):
        df=np.minimum(df*240/df.sum(),38.0)
        if abs(df.sum()-240)<0.5: break
    res[tm]={k:round(float(v),1) for k,v in df.items()}
    if R: ret[tm]=[{**r,'final_min':res[tm].get(r['player'])} for r in R.values()]
    print(tm,ng,' | '.join(f"{k} {v:.0f}{' (back)' if norm(k) in R else ''}" for k,v in res[tm].items()))
json.dump(res,open(f'slate/{D}_rotations.json','w'),indent=1)
json.dump(ret,open(f'slate/{D}_returning.json','w'),indent=1)
if ret: print('returning:',json.dumps(ret))
