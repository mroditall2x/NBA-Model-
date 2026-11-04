"""python3 espn_box.py YYYY-MM-DD -> slate/MMDD/espn_box.csv (player box scores from ESPN for finished games).
Lets us grade the same night instead of waiting for hoopR (~7-9 AM). Runs on GitHub (ESPN is reachable there)."""
import sys, json, urllib.request, pandas as pd
DATE = sys.argv[1]; D = f'slate/{DATE[5:7]}{DATE[8:10]}'
B = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30))
sb = get(f'{B}/scoreboard?dates={DATE.replace("-", "")}')
rows, firsts = [], []
statuses = []
for ev in sb.get('events', []):
    st = ev['status']['type']; comp = ev['competitions'][0]
    t = {c['homeAway']: c['team']['abbreviation'] for c in comp['competitors']}
    game = f"{t['away']}@{t['home']}"
    print(game, st['description'])
    statuses.append(dict(game=game, status=st['description']))
    if not st.get('completed'): continue
    S = get(f"{B}/summary?event={ev['id']}"); ids = {}
    for team in S.get('boxscore', {}).get('players', []):
        for a in team['statistics'][0]['athletes']: ids[str(a['athlete']['id'])] = (a['athlete']['displayName'], team['team']['abbreviation'])
    fp = next((pl for pl in S.get('plays', []) if pl.get('scoringPlay') and pl.get('scoreValue') in (2, 3)), None)
    if fp and fp.get('participants'):
        nm, tm = ids.get(str(fp['participants'][0]['athlete']['id']), (fp.get('text', '').split(' makes')[0], ''))
        firsts.append(dict(game=game, team=tm, player=nm, text=fp.get('text', '')))
    for team in S.get('boxscore', {}).get('players', []):
        s = team['statistics'][0]; keys = s.get('keys') or s.get('names') or s.get('labels')
        for a in s['athletes']:
            if a.get('didNotPlay') or not a.get('stats'): continue
            v = dict(zip(keys, a['stats']))
            g = lambda *ks: next((v[k] for k in ks if k in v), '0')
            mk = lambda x: float(str(x).split('-')[0] or 0)
            rows.append(dict(game=game, team=team['team']['abbreviation'], player=a['athlete']['displayName'],
                             minutes=mk(g('minutes', 'MIN')), PTS=mk(g('points', 'PTS')), REB=mk(g('rebounds', 'REB')), AST=mk(g('assists', 'AST')),
                             **{'3PM': mk(g('threePointFieldGoalsMade-threePointFieldGoalsAttempted', '3PT'))},
                             STL=mk(g('steals', 'STL')), BLK=mk(g('blocks', 'BLK')), OREB=mk(g('offensiveRebounds', 'OREB'))))
pd.DataFrame(rows).to_csv(f'{D}/espn_box.csv', index=False)
pd.DataFrame(statuses).to_csv(f'{D}/game_status.csv', index=False)
if firsts: pd.DataFrame(firsts).to_csv(f'{D}/fb_actual.csv', index=False)
print(len(rows), 'player lines ->', f'{D}/espn_box.csv')
