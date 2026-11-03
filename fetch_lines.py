"""Pull NBA lines from The Odds API into the slate format the model uses.
  python3 fetch_lines.py YYYY-MM-DD [--props-teams HOU,BOS [--merge-props] | --props-all] [--snap]
Writes slate/MMDD/lines.json (consensus spread/total/ML per game), props_p1.txt + pp_compact.json (player props),
odds_raw.json (everything pulled, for line-movement history). --snap also saves *.open copies for line_moves.py.
Credits: game lines ~3 per pull (all games); props = markets x regions per game (~16). Free plan: keep props to 1-2 teams.
Key comes from env ODDS_API_KEY (GitHub secret) - never hard-code it."""
import os, sys, json, statistics, urllib.request, shutil, datetime as dt
from zoneinfo import ZoneInfo

KEY = os.environ.get('ODDS_API_KEY') or sys.exit('ODDS_API_KEY not set')
BASE = 'https://api.the-odds-api.com/v4/sports/basketball_nba'
DATE = sys.argv[1]; D = f'slate/{DATE[5:7]}{DATE[8:10]}'; os.makedirs(D, exist_ok=True)
args = sys.argv[2:]
PROPS_ALL = '--props-all' in args
MERGE = '--merge-props' in args      # refresh only these teams' games, keep every other game's props and lines
_pt = json.load(open('props_teams.json')) if os.path.exists('props_teams.json') else {}   # per-date override, e.g. {"2026-11-01": "BOS,GS"}
PROPS_TEAMS = set(args[args.index('--props-teams') + 1].split(',')) if '--props-teams' in args else set((_pt.get(DATE) or os.environ.get('PROPS_TEAMS', 'HOU')).split(','))
ABB = {'Dallas Mavericks': 'DAL', 'Minnesota Timberwolves': 'MIN', 'San Antonio Spurs': 'SA', 'Denver Nuggets': 'DEN', 'Golden State Warriors': 'GS',
       'Los Angeles Clippers': 'LAC', 'LA Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
       'Cleveland Cavaliers': 'CLE', 'Miami Heat': 'MIA', 'New York Knicks': 'NY', 'Philadelphia 76ers': 'PHI', 'Washington Wizards': 'WSH',
       'New Orleans Pelicans': 'NO', 'Phoenix Suns': 'PHX', 'Sacramento Kings': 'SAC', 'Utah Jazz': 'UTAH', 'Houston Rockets': 'HOU',
       'Chicago Bulls': 'CHI', 'Oklahoma City Thunder': 'OKC', 'Atlanta Hawks': 'ATL', 'Charlotte Hornets': 'CHA', 'Indiana Pacers': 'IND',
       'Orlando Magic': 'ORL', 'Milwaukee Bucks': 'MIL', 'Portland Trail Blazers': 'POR', 'Memphis Grizzlies': 'MEM', 'Toronto Raptors': 'TOR',
       'Detroit Pistons': 'DET'}
PROP = {'player_points': ('PTS', 'Points'), 'player_rebounds': ('REB', 'Rebounds'), 'player_assists': ('AST', 'Assists'),
        'player_points_rebounds_assists': ('PRA', 'Pts + Reb + Ast'), 'player_points_assists': ('PA', 'Points + Assists'),
        'player_points_rebounds': ('PR', 'Points + Rebounds'), 'player_rebounds_assists': ('RA', 'Rebounds + Assists'),
        'player_threes': ('3PM', 'Three Pointers'), 'player_points_alternate': ('PTS_ALT', 'Points Alt'),
        'player_first_basket': ('FB', 'First Basket')}
DFS = {'prizepicks', 'underdog'}

def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        print('credits left:', r.headers.get('x-requests-remaining'), '| used this call:', r.headers.get('x-requests-last'))
        return json.load(r)

def imp(o): return -o / (-o + 100) if o < 0 else 100 / (o + 100)
def med(x): return statistics.median(x) if x else None

ct = ZoneInfo('America/Chicago')
# no NBA games that day -> don't spend credits (free check against the schedule file / ESPN scoreboard)
try:
    import pandas as _pd
    _s = _pd.read_parquet(f"{os.environ.get('NBA_DATA', 'repo/nba')}/schedules/parquet/nba_schedule_2027.parquet", columns=['date'])
    _n = (_pd.to_datetime(_s['date'], utc=True).dt.tz_convert('America/Chicago').dt.date.astype(str) == DATE).sum()
except Exception:
    try:
        _j = json.load(urllib.request.urlopen(urllib.request.Request(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={DATE.replace('-', '')}", headers={'User-Agent': 'Mozilla/5.0'}), timeout=30))
        _n = len(_j.get('events', []))
    except Exception: _n = 1   # can't tell -> pull as usual
if _n == 0: print(f'no NBA games on {DATE} - skipping the odds pull (0 credits)'); sys.exit(0)
games = get(f'{BASE}/odds?apiKey={KEY}&regions=us&markets=h2h,spreads,totals&oddsFormat=american')
games = [g for g in games if dt.datetime.fromisoformat(g['commence_time'].replace('Z', '+00:00')).astimezone(ct).date().isoformat() == DATE]
raw = {'pulled_at': dt.datetime.now(ct).isoformat(), 'games': games, 'props': {}}
out = []
for g in games:
    home, away = ABB.get(g['home_team'], g['home_team']), ABB.get(g['away_team'], g['away_team'])
    sp, so, tot, to, mlh, mla = [], [], [], [], [], []
    for b in g['bookmakers']:
        for m in b['markets']:
            oc = {o['name']: o for o in m['outcomes']}
            if m['key'] == 'spreads' and g['home_team'] in oc:
                sp.append(oc[g['home_team']]['point']); so.append((oc[g['home_team']]['price'], oc[g['away_team']]['price']))
            if m['key'] == 'totals' and 'Over' in oc:
                tot.append(oc['Over']['point']); to.append((oc['Over']['price'], oc['Under']['price']))
            if m['key'] == 'h2h' and g['home_team'] in oc:
                mlh.append(oc[g['home_team']]['price']); mla.append(oc[g['away_team']]['price'])
    if not sp or not tot or not mlh or not mla: continue   # skip games already live / missing a market
    hs, t = med(sp), med(tot)
    so_m = [x for x, s in zip(so, sp) if s == hs] or so; to_m = [x for x, s in zip(to, tot) if s == t] or to
    out.append(dict(away=away, home=home, id=g['id'], commence=g['commence_time'], home_spread=hs,
                    spread_odds=[round(med([a for a, _ in so_m])), round(med([b for _, b in so_m]))], ml_home=round(med(mlh)), ml_away=round(med(mla)),
                    total=t, total_odds=[round(med([a for a, _ in to_m])), round(med([b for _, b in to_m]))]))
if MERGE and os.path.exists(f'{D}/lines.json'):      # finished games drop off the feed; keep them so their picks stay locked and graded
    have = {(g['away'], g['home']) for g in out}
    out += [g for g in json.load(open(f'{D}/lines.json'))['games'] if (g['away'], g['home']) not in have]
json.dump({'games': out}, open(f'{D}/lines.json', 'w'), indent=1)
print(f'{len(out)} games ->', f'{D}/lines.json')

props_txt, compact, alt_rows, fb = [], [], [], {}
for g in out:
    if not (PROPS_ALL or {g['home'], g['away']} & PROPS_TEAMS): continue
    gk = f"{g['away']}@{g['home']}"
    ev = get(f"{BASE}/events/{g['id']}/odds?apiKey={KEY}&regions=us,us_dfs&markets={','.join(PROP)}&oddsFormat=american")
    raw['props'][gk] = ev
    lines = {}   # (player, market) -> {line: [(over, under)], 'dfs': [lines]}
    for b in ev.get('bookmakers', []):
        for m in b['markets']:
            for o in m['outcomes']:
                key = (o.get('description'), m['key']); L = o.get('point')
                if key[0] is None or L is None: continue
                d = lines.setdefault(key, {'book': {}, 'dfs': set()})
                if b['key'] in DFS: d['dfs'].add(L); continue
                if abs(o['price']) >= 100: d['book'].setdefault(L, {}).setdefault(b['key'], {})[o['name']] = o['price']
    alts = []
    for b in ev.get('bookmakers', []):
        for m in b['markets']:
            if m['key'] == 'player_points_alternate':
                alts += [[gk, o.get('description'), o.get('point'), o['price'], b['key']] for o in m['outcomes'] if o.get('name') == 'Over' and o.get('point') is not None]
    best = {}
    for gk_, pl, L, pr, bk in alts:
        k = (pl, L)
        if k not in best or pr > best[k][3]: best[k] = [gk_, pl, L, pr, bk]
    alt_rows.extend(best.values())
    fbp = {}   # first basket: median 'Yes' price across books per player
    for b in ev.get('bookmakers', []):
        for m in b['markets']:
            if m['key'] == 'player_first_basket':
                for o in m['outcomes']:
                    pl = o.get('description') or o.get('name')
                    if o.get('name') in ('Yes', pl) and o['price'] >= 100: fbp.setdefault(pl, []).append(o['price'])
    if fbp: fb[gk] = [[pl, round(med(v))] for pl, v in fbp.items()]
    for (player, mk), d in lines.items():
        if mk in ('player_points_alternate', 'player_first_basket'): continue
        code, label = PROP[mk]
        pairs = {L: [(v['Over'], v['Under']) for v in books.values() if 'Over' in v and 'Under' in v] for L, books in d['book'].items()}
        pairs = {L: p for L, p in pairs.items() if p}
        pp = min(d['dfs'], key=lambda x: abs(x - (med(list(pairs)) or x))) if d['dfs'] else ''
        if pairs:   # main line = the one most books hang, ties -> closest to even
            L = max(pairs, key=lambda l: (len(pairs[l]), -abs(med([imp(a) - imp(b) for a, b in pairs[l]]))))
            o_, u_ = round(med([a for a, _ in pairs[L]])), round(med([b for _, b in pairs[L]]))
            if code != '3PM': props_txt.append(f'{gk}|{player}|{code}|{L}|{o_}|{u_}')
            compact.append([gk, player, label, str(L), str(o_), str(u_), str(pp), '', ''])
        elif pp != '':
            compact.append([gk, player, label, str(pp), '-119', '-119', str(pp), '', ''])
if not raw['props']: print('game lines only - keeping the props already pulled')
else:
  if MERGE:
    hit = set(raw['props'])
    if os.path.exists(f'{D}/props_p1.txt'): props_txt = [l for l in open(f'{D}/props_p1.txt').read().splitlines() if l and l.split('|')[0] not in hit] + props_txt
    if os.path.exists(f'{D}/pp_compact.json'): compact = [r for r in json.load(open(f'{D}/pp_compact.json')) if r[0] not in hit] + compact
    if os.path.exists(f'{D}/pts_alt.json'): alt_rows = [r for r in json.load(open(f'{D}/pts_alt.json')) if r[0] not in hit] + alt_rows
    if os.path.exists(f'{D}/fb_odds.json'): fb = {**json.load(open(f'{D}/fb_odds.json')), **fb}
  open(f'{D}/props_p1.txt', 'w').write('\n'.join(props_txt) + '\n')
  json.dump(compact, open(f'{D}/pp_compact.json', 'w'))
  json.dump(alt_rows, open(f'{D}/pts_alt.json', 'w'))
  if fb: json.dump(fb, open(f'{D}/fb_odds.json', 'w'))   # best Over price per points milestone (for boom.py)
json.dump(raw, open(f'{D}/odds_raw_{dt.datetime.now(ct):%H%M}.json', 'w'))
print(len(props_txt), 'prop lines ->', f'{D}/props_p1.txt')
if '--snap' in args:
    for f in ('lines.json', 'props_p1.txt'): shutil.copy(f'{D}/{f}', f'{D}/{f}.open')
    print('opening snapshot saved')
