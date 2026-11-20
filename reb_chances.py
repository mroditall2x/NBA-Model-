"""NBA.com rebound tracking (11/20, TEST - report only, nothing in the model uses it yet).
python3 reb_chances.py 2026-11-20  ->  slate/MMDD/reb_chances.csv
Per player: rebounds, rebound chances (times he was near a rebound), contested share, and how many of
his chances he converts - for the season and the last 5 games, so we can see chances rising while
rebound lines stay flat (the REB Under losses). Never stops the daily build: on any error it prints
why and exits 0."""
import sys, os, json, time, urllib.request, urllib.parse
import pandas as pd

DATE = sys.argv[1] if len(sys.argv) > 1 else time.strftime('%Y-%m-%d')
MMDD = DATE[5:7] + DATE[8:10]
D = f'slate/{MMDD}'
y, m = int(DATE[:4]), int(DATE[5:7])
SEASON = f'{y}-{str(y+1)[2:]}' if m >= 9 else f'{y-1}-{str(y)[2:]}'
HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
       'Referer': 'https://www.nba.com/', 'Origin': 'https://www.nba.com', 'Accept': 'application/json, text/plain, */*',
       'Accept-Language': 'en-US,en;q=0.9', 'x-nba-stats-origin': 'stats', 'x-nba-stats-token': 'true'}
KEEP = ['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', 'REB', 'REB_CHANCES', 'REB_CHANCE_PCT',
        'REB_CHANCE_PCT_ADJ', 'REB_CONTEST', 'REB_UNCONTEST', 'REB_CONTEST_PCT', 'OREB_CHANCES', 'DREB_CHANCES']

def pull(last_n):
    q = {'College': '', 'Conference': '', 'Country': '', 'DateFrom': '', 'DateTo': '', 'Division': '', 'DraftPick': '',
         'DraftYear': '', 'GameScope': '', 'Height': '', 'LastNGames': last_n, 'LeagueID': '00', 'Location': '', 'Month': 0,
         'OpponentTeamID': 0, 'Outcome': '', 'PORound': 0, 'PerMode': 'PerGame', 'PlayerExperience': '',
         'PlayerOrTeam': 'Player', 'PlayerPosition': '', 'PtMeasureType': 'Rebounding', 'Season': SEASON,
         'SeasonSegment': '', 'SeasonType': 'Regular Season', 'StarterBench': '', 'TeamID': 0, 'VsConference': '',
         'VsDivision': '', 'Weight': ''}
    url = 'https://stats.nba.com/stats/leaguedashptstats?' + urllib.parse.urlencode(q)
    err = None
    for i in range(3):
        try:
            j = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=45))
            rs = j['resultSets'][0]
            df = pd.DataFrame(rs['rowSet'], columns=rs['headers'])
            return df[[c for c in KEEP if c in df.columns]]
        except Exception as e:
            err = e; print(f'  try {i+1} (last {last_n}) failed: {type(e).__name__}: {e}'); time.sleep(5 * (i + 1))
    raise RuntimeError(err)

try:
    t0 = time.time()
    s = pull(0); l5 = pull(5)
    l5 = l5[['PLAYER_ID', 'GP', 'MIN', 'REB', 'REB_CHANCES', 'REB_CHANCE_PCT', 'REB_CONTEST_PCT']].add_suffix('_L5').rename(columns={'PLAYER_ID_L5': 'PLAYER_ID'})
    out = s.merge(l5, on='PLAYER_ID', how='left')
    out['chances_trend'] = (out['REB_CHANCES_L5'] - out['REB_CHANCES']).round(2)   # + = more chances lately
    os.makedirs(D, exist_ok=True)
    out.to_csv(f'{D}/reb_chances.csv', index=False)
    print(f'reb_chances: OK {len(out)} players, season {SEASON}, {time.time()-t0:.0f}s -> {D}/reb_chances.csv')
    print(out.sort_values('REB_CHANCES', ascending=False).head(8)[['PLAYER_NAME', 'REB', 'REB_CHANCES', 'REB_CHANCES_L5', 'chances_trend']].to_string(index=False))
except Exception as e:
    print('reb_chances: FAILED - NBA.com did not answer from this machine:', e)
sys.exit(0)
