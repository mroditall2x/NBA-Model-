"""Hourly injury watch.  python3 injury_watch.py YYYY-MM-DD
- Pulls ESPN's injury feed (free, no odds credits) and keeps slate/MMDD/injury_report.json (per game, for the board).
- Compares with the last check. If a player on a team that hasn't tipped yet changes status (new Out, Questionable -> Out,
  back from injury...), it rebuilds the card with the lines already pulled (no credits) and sends a push to Deon's phone
  through ntfy (topic from the NTFY_TOPIC secret). Games that already tipped are ignored.
Prints REBUILD when the card should be rebuilt (the workflow runs run_day.py after it)."""
import sys, os, json, urllib.request, datetime as dt
DATE = sys.argv[1]; D = f'slate/{DATE[5:7]}{DATE[8:10]}'
ABB = {'Dallas Mavericks': 'DAL', 'Minnesota Timberwolves': 'MIN', 'San Antonio Spurs': 'SA', 'Denver Nuggets': 'DEN', 'Golden State Warriors': 'GS',
       'Los Angeles Clippers': 'LAC', 'LA Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
       'Cleveland Cavaliers': 'CLE', 'Miami Heat': 'MIA', 'New York Knicks': 'NY', 'Philadelphia 76ers': 'PHI', 'Washington Wizards': 'WSH',
       'New Orleans Pelicans': 'NO', 'Phoenix Suns': 'PHX', 'Sacramento Kings': 'SAC', 'Utah Jazz': 'UTAH', 'Houston Rockets': 'HOU',
       'Chicago Bulls': 'CHI', 'Oklahoma City Thunder': 'OKC', 'Atlanta Hawks': 'ATL', 'Charlotte Hornets': 'CHA', 'Indiana Pacers': 'IND',
       'Orlando Magic': 'ORL', 'Milwaukee Bucks': 'MIL', 'Portland Trail Blazers': 'POR', 'Memphis Grizzlies': 'MEM', 'Toronto Raptors': 'TOR',
       'Detroit Pistons': 'DET'}
if not os.path.exists(f'{D}/lines.json'): sys.exit('no lines for today yet')
now = dt.datetime.now(dt.timezone.utc)
games = {}
for g in json.load(open(f'{D}/lines.json'))['games']:
    tip = dt.datetime.fromisoformat(g['commence'].replace('Z', '+00:00'))
    games[f"{g['away']}@{g['home']}"] = dict(away=g['away'], home=g['home'], tip=tip, live=tip > now)
team_game = {t: k for k, g in games.items() for t in (g['away'], g['home'])}

j = json.load(urllib.request.urlopen(urllib.request.Request('https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries',
                                                            headers={'User-Agent': 'Mozilla/5.0'}), timeout=30))
cur = {}
for t in j.get('injuries', []):
    tm = ABB.get(t.get('displayName'), t.get('displayName'))
    if tm not in team_game: continue
    for i in t.get('injuries', []):
        cur[i['athlete']['displayName']] = dict(team=tm, status=i.get('status', ''), note=i.get('shortComment') or i.get('longComment') or '')

report = {k: [dict(player=p, **v) for p, v in cur.items() if v['team'] in (g['away'], g['home'])] for k, g in games.items()}
json.dump({'checked': now.isoformat(), 'games': report}, open(f'{D}/injury_report.json', 'w'), indent=1)

lp = f'{D}/injuries_last.json'
last = json.load(open(lp)) if os.path.exists(lp) else None
json.dump(cur, open(lp, 'w'))
if last is None: sys.exit('first check of the day saved')

changes = []
for p in set(cur) | set(last):
    a, b = last.get(p, {}).get('status', 'Active'), cur.get(p, {}).get('status', 'Active')
    tm = (cur.get(p) or last.get(p))['team']
    if a != b and games[team_game[tm]]['live']: changes.append((team_game[tm], tm, p, a, b))
if not changes: sys.exit('no changes')

# keep the pre-rebuild card (card_diff.py pushes what changed) and decide which games need fresh prop lines:
# a real player newly ruled Out in a game with props. Teammates' lines move on that news, so the rebuild shouldn't use old ones.
import shutil
from slate_names import norm
for f in ('card.csv', 'by_team.csv', 'games.csv'):
    if os.path.exists(f'{D}/{f}'): shutil.copy(f'{D}/{f}', f'{D}/{f}.prev')
prop_rows = [l.split('|') for l in open(f'{D}/props_p1.txt') if '|' in l] if os.path.exists(f'{D}/props_p1.txt') else []
prop_games, prop_players = {r[0] for r in prop_rows}, {norm(r[1]) for r in prop_rows}
rp = f'slate/{DATE}_rotations.json'
rot = {norm(n): m for t in json.load(open(rp)).values() for n, m in t.items()} if os.path.exists(rp) else {}
MAX_REFRESH = 4                                       # per day, ~16 credits per game
rf = f'{D}/prop_refresh.json'
done = json.load(open(rf)) if os.path.exists(rf) else []
# books pull a ruled-out player's props and rotations drop him, so season minutes are what show he matters
try:
    import pandas as pd
    pb = pd.read_parquet(f"{os.environ.get('NBA_DATA', 'repo/nba')}/player_box/parquet/player_box_2027.parquet")
    pb['m'] = pd.to_numeric(pb.minutes, errors='coerce'); pb = pb[pb.m > 0]
    season_min = {norm(n): v for n, v in pb.groupby('athlete_display_name').m.mean().items()}
except Exception as e:
    print('season minutes unavailable:', e); season_min = {}
matters = lambda p: norm(p) in prop_players or max(rot.get(norm(p), 0), season_min.get(norm(p), 0)) >= 15
need = sorted({gk for gk, tm, p, a, b in changes if b == 'Out' and gk in prop_games and matters(p)})
refresh, capped = need[:max(0, MAX_REFRESH - len(done))], need[max(0, MAX_REFRESH - len(done)):]
json.dump(done + refresh, open(rf, 'w'))
json.dump(dict(games=sorted({c[0] for c in changes}), refreshed=refresh, capped=capped,
               changes=[dict(game=gk, team=tm, player=p, status=b, text=f"{p} {a} -> {b}") for gk, tm, p, a, b in changes]),
          open(f'{D}/watch_changes.json', 'w'))
if refresh: print('REFRESH', ','.join(games[g]['home'] for g in refresh))

# which card picks are touched (same team as the change)
import csv
picks = []
for f in ('card.csv', 'by_team.csv'):
    if os.path.exists(f'{D}/{f}'):
        picks += [r for r in csv.DictReader(open(f'{D}/{f}'))]
lines = []
for gk, tm, p, a, b in sorted(changes):
    hit = sorted({f"{r['player']} {r['stat']} {'O' if r['side']=='More' else 'U'}{r['line']}" for r in picks if r['team'] == tm})
    lines.append(f"{tm}: {p} {a} -> {b}" + (f"  | check: {', '.join(hit[:4])}" if hit else ''))
msg = 'Injury update (card rebuilding):\n' + '\n'.join(lines)
print(msg); print('REBUILD')
open(f'{D}/injury_alerts.log', 'a').write(f"{now:%H:%M}Z " + ' / '.join(lines) + '\n')
open('alerts_out.txt', 'a').write('## NBA injury alert\n' + msg + '\n\n')   # emailed by GitHub (issue)
topic = os.environ.get('NTFY_TOPIC')
if topic:
    try:
        urllib.request.urlopen(urllib.request.Request(f'https://ntfy.sh/{topic}', data=msg.encode(),
                                                      headers={'Title': 'NBA injury alert', 'Tags': 'rotating_light', 'Priority': '4'}), timeout=20)
        print('push sent')
    except Exception as e: print('push failed:', e)
