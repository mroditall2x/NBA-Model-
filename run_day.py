"""One command for a slate.  python3 run_day.py 2026-10-30 [--games MEM@POR,...]
Steps: hoopR pull -> ESPN injuries -> rotations (auto_minutes + rot_blend) -> sim pass1 -> market-implied blend -> pass2
-> board -> card (calibrated, rule-filtered) saved to slate/MMDD/card.csv with model p for grading.
Needs slate/MMDD/lines.json + props_p1.txt (+ pp_compact.json) from the lines source (Outlier scraper or odds API)."""
import sys, os, json, subprocess, urllib.request
import pandas as pd
DATE=sys.argv[1]; MMDD=DATE[5:7]+DATE[8:10]; D=f'slate/{MMDD}'
def sh(c): print('$',c); subprocess.run(c,shell=True,check=True)
if os.path.isdir('repo/.git') and not os.environ.get('CI'): sh('cd repo && git pull -q')
os.makedirs(D, exist_ok=True)
# injuries (ESPN public feed) -> outs + questionable
try:
    j=json.load(urllib.request.urlopen('https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries',timeout=30))
    outs=[i['athlete']['displayName'] for t in j['injuries'] for i in t['injuries'] if i['status']=='Out']
    gtd=[i['athlete']['displayName'] for t in j['injuries'] for i in t['injuries'] if i['status']!='Out']
    json.dump(outs,open(f'slate/{DATE}_out.json','w')); json.dump(gtd,open(f'{D}/gtd.json','w'))
except Exception as e:
    print('injury feed failed:',e)
    if not os.path.exists(f'slate/{DATE}_out.json'): json.dump([],open(f'slate/{DATE}_out.json','w'))
    if not os.path.exists(f'{D}/gtd.json'): json.dump([],open(f'{D}/gtd.json','w'))
sh(f'python3 auto_minutes.py {DATE} slate/{DATE}_rot_last.json > /dev/null')
sh(f'python3 rot_blend.py {DATE} 0.6')
os.environ['NO_OUTGUESS']='1'; os.environ['SAVE_SIM']='1'
sh(f'python3 slate1021.py {DATE} {D} > {D}/p1.log'); sh(f'python3 blend_minutes.py {D}')
sh(f'python3 slate1021.py {DATE} {D} --blend > {D}/p2.log'); sh(f'python3 card_slate.py {D} > /dev/null')
sh(f'python3 dvp.py {D}')
subprocess.run(f'python3 boom.py {D}', shell=True)
if os.path.exists(f'{D}/fb_odds.json'):
    _fbold=pd.read_csv(f'{D}/fb_priced.csv') if os.path.exists(f'{D}/fb_priced.csv') else None
    subprocess.run(f'python3 fb_price.py {D} > {D}/fb.log', shell=True)
    if _fbold is not None and os.path.exists(f'{D}/fb_priced.csv'):
        import datetime as _d2; _now=_d2.datetime.now(_d2.timezone.utc)
        _st={f"{g['away']}@{g['home']}" for g in json.load(open(f'{D}/lines.json'))['games'] if _d2.datetime.fromisoformat(g['commence'].replace('Z','+00:00'))<_now}
        _new=pd.read_csv(f'{D}/fb_priced.csv'); pd.concat([_fbold[_fbold.game.isin(_st)],_new[~_new.game.isin(_st)]]).to_csv(f'{D}/fb_priced.csv',index=False)
# ---- card rules (from graded history)
B=pd.read_csv(f'{D}/board_all.csv'); B['flags']=B['flags'].fillna('')
B['adj']=0.5+0.6*(B.model-0.5)                       # calibration shrink (k=0.6)
ok=(B['gap'].abs()<=4)&~B['flags'].str.contains('new team|small|unclear')
ok&=~((B.side=='Less')&(B['gap']>2))&~((B.side=='More')&(B['gap']<-2))
std=B[ok&B.type.isin(['PP standard','book line'])&~B.stat.isin(['STL','BLK','STL+BLK'])]
std=std[(std.adj>=0.58)&(std.edge>=0.05)&~((std['min']>=35)&(std.side=='Less')&(std.adj<0.62))]
std=std[~((std.stat=='PTS')&(std.side=='Less')&(std.adj<0.60))]          # straight PTS Unders need 60%; combos preferred
gob=B[ok&(B.type=='goblin')&(B.model>=0.84)]
card=pd.concat([std.assign(tier='standard',p=std.adj),gob.assign(tier='goblin',p=gob.model)])
card=card.sort_values('p',ascending=False).drop_duplicates(['player','stat'])
import datetime as _dt
_started=set()
try:
    for _g in json.load(open(f'{D}/lines.json'))['games']:
        if _dt.datetime.fromisoformat(_g['commence'].replace('Z','+00:00'))<_dt.datetime.now(_dt.timezone.utc): _started.add(f"{_g['away']}@{_g['home']}")
except Exception: pass
_cols=['game','team','player','stat','tier','line','side','p','mean','min','gap','where']
card=card[~card.game.isin(_started)][_cols]
if _started and os.path.exists(f'{D}/card.csv'):          # games already tipped keep the card that was posted before tip
    _old=pd.read_csv(f'{D}/card.csv'); card=pd.concat([_old[_old.game.isin(_started)][[c for c in _cols if c in _old]],card])
card.to_csv(f'{D}/card.csv',index=False)
G=pd.read_csv(f'{D}/games.csv')
G['full_game_note']=['skip: model >6 off market' if abs(r.model_total-r.mkt_total)>6 or abs(r.model_spread_home-r.mkt_spread_home)>6 else '' for r in G.itertuples()]
def _ev(r):   # moneyline EV+ tag: calibrated model win% beats market by 3+ pts; favorites also need 65%+
    if r.full_game_note: return ''
    a,h=r.game.split('@'); out=[]
    for team,p,m in ((h,r.p_home_win,r.mkt_home_win),(a,1-r.p_home_win,1-r.mkt_home_win)):
        c=m+0.5*(p-m)          # meet the market halfway (model alone over-rates dogs)
        if c-m>=0.03 and (m<0.5 or c>=0.65): out.append(f"EV+ {team} ML ({'fav' if m>=0.5 else 'dog'}) {round(c*100)}% vs mkt {round(m*100)}%")
    return '; '.join(out)
G['ev_tag']=[_ev(r) for r in G.itertuples()]
G.to_csv(f'{D}/games.csv',index=False)
print(card.head(30).to_string(index=False))
# ---- best 3 per team (incl. a points slot when one is close) for games with props; leans marked below the card bar
ok_bt=ok|((B['gap'].abs()<=4)&(B['flags']=='new team'))   # traded players still count here (graded lean at most)
pool=B[ok_bt&B.type.isin(['PP standard','book line'])&~B.stat.isin(['STL','BLK','STL+BLK'])&(B.edge>=0.02)].copy()
pool=pool[~((pool['min']>=35)&(pool.side=='Less')&(pool.adj<0.62))].sort_values('adj',ascending=False).drop_duplicates(['player','stat'])
rows=[]
for t,x in pool.groupby('team'):   # 4 per team, one prop per player, always an Over and a points prop when one is close
    u=x.drop_duplicates('player'); sel=list(u.index[:2])
    def add(m):
        c=x[m&~x.player.isin(x.loc[sel,'player'])&(x.adj>=0.53)].head(1)
        if len(c): sel.append(c.index[0])
    if not (x.loc[sel,'side']=='More').any(): add(x.side=='More')
    if not x.loc[sel,'stat'].isin(['PTS','PA','PR','PRA']).any(): add(x.stat.isin(['PTS','PA','PR','PRA']))
    for i in u.index:
        if len(sel)>=4: break
        if i not in sel and x.loc[i,'player'] not in set(x.loc[sel,'player']): sel.append(i)
    rows.append(x.loc[sel].sort_values('adj',ascending=False))
if rows:
    BT=pd.concat(rows); BT['grade']=['card' if a>=0.58 and f=='' else 'lean' for a,f in zip(BT.adj,BT['flags'])]; BT['adj']=BT.adj.round(3)
    BT=BT[['game','team','player','stat','line','side','adj','mean','min','grade','where']].rename(columns={'adj':'p'})
    BT=BT[~BT.game.isin(_started)]
    if _started and os.path.exists(f'{D}/by_team.csv'):
        _o=pd.read_csv(f'{D}/by_team.csv'); BT=pd.concat([_o[_o.game.isin(_started)],BT])
    BT.to_csv(f'{D}/by_team.csv',index=False)
