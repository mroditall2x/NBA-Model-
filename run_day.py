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
card[['game','team','player','stat','tier','line','side','p','mean','min','gap','where']].to_csv(f'{D}/card.csv',index=False)
G=pd.read_csv(f'{D}/games.csv')
G['full_game_note']=['skip: model >6 off market' if abs(r.model_total-r.mkt_total)>6 or abs(r.model_spread_home-r.mkt_spread_home)>6 else '' for r in G.itertuples()]
G.to_csv(f'{D}/games.csv',index=False)
print(card.head(30).to_string(index=False))
