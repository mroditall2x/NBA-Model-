"""Play-style tracking from play-by-play.  python3 style.py slate/MMDD [YYYY-MM-DD]
For every team, this season: shot mix (rim / spot-up 3 / pull-up 3 / pull-up 2 / other 2), how often shots come in transition
(within 7 s of a defensive rebound or a steal), how often the offense gets stuck late in the clock (shot 18+ s after the
possession started), assisted share and pace. The same numbers for what each DEFENSE allows. Ranks 1-30 (1 = most).
Writes slate/MMDD/style_team.csv, style_notes.csv (clashes for tonight's games and card/by-team players) and appends
slate/style_log.csv (one row per team per game, so later we can test whether style clashes move spreads and totals).
Tracking only: nothing here changes the card. Pull-up/spot-up comes from the play-by-play shot labels, not tracking data;
coverages (drop, switch, blitz) are not visible. Frequencies are stickier than make %."""
import sys, os, json, datetime as dt
import numpy as np, pandas as pd

ROOT = os.environ.get('NBA_DATA', 'repo/nba')
TRANS_S, LATE_S = 7, 18
STEAL = 'steal'
CATS = ['rim', 'spot3', 'pull3', 'pull2', 'other2']


def shots(pbp):
    d = pbp.sort_values(['game_id', 'game_play_number']).copy()
    d['t'] = d.start_game_seconds_remaining.astype(float)
    d['txt'] = d.text.fillna('')
    d['off'] = np.where(d.team_id == d.home_team_id, d.home_team_abbrev, d.away_team_abbrev)
    d['opp'] = np.where(d.team_id == d.home_team_id, d.away_team_abbrev, d.home_team_abbrev)
    ty = d.type_text.fillna('')
    is_shot = (d.shooting_play == True) & ~ty.str.contains('Free Throw')
    # possession starts: own defensive rebound, opponent turnover (steal = live ball), opponent made FG / last FT, period start
    dreb = ty.eq('Defensive Rebound')
    tov = ty.str.contains('Turnover')
    live = tov & d.txt.str.contains(STEAL, case=False)
    made_fg = is_shot & (d.scoring_play == True)
    last_ft = ty.str.contains(r'Free Throw - (?:1 of 1|2 of 2|3 of 3)') & (d.scoring_play == True)
    rows = []
    for gid, g in d.groupby('game_id', sort=False):
        start, trans_ok = {}, {}
        per = None
        for r, sh, dr, tv, lv, mf, lf in zip(g.itertuples(), is_shot[g.index], dreb[g.index], tov[g.index], live[g.index], made_fg[g.index], last_ft[g.index]):
            if r.period != per:
                per = r.period; start = {r.home_team_abbrev: r.t, r.away_team_abbrev: r.t}; trans_ok = {}
            if dr:
                start[r.off] = r.t; trans_ok[r.off] = r.t
            elif tv:                                   # ball goes to the other team
                start[r.opp] = r.t
                if lv: trans_ok[r.opp] = r.t
            elif sh:
                el = start.get(r.off, r.t) - r.t
                tr = (trans_ok.get(r.off) is not None) and (trans_ok[r.off] - r.t) <= TRANS_S
                rows.append((gid, r.game_date, r.off, r.opp, r.type_text, r.txt, bool(r.scoring_play), r.score_value or 0, tr, el >= LATE_S))
                trans_ok.pop(r.off, None)
                if mf:
                    start[r.opp] = r.t
            elif lf:
                start[r.opp] = r.t
    s = pd.DataFrame(rows, columns=['game_id', 'game_date', 'off', 'opp', 'type', 'text', 'made', 'pts', 'trans', 'late'])
    t = s['type'].fillna(''); three = s.text.str.contains('three point')
    s['cat'] = np.select([t.str.contains('Dunk|Layup|Tip|Putback|Finger Roll|Alley'),
                          three & t.str.contains('Pullup|Step Back|Running|Fade|Turnaround'), three,
                          t.str.contains('Pullup|Step Back|Fade|Turnaround')], ['rim', 'pull3', 'spot3', 'pull2'], 'other2')
    s['ast'] = s.made & s.text.str.contains(r'assists\)')
    s['pts'] = np.where(s.made, np.where(three, 3, 2), 0)
    return s


def profile(s, key):
    g = s.groupby(key)
    out = pd.DataFrame({'games': g.game_id.nunique(), 'fga': g.size()})
    for c in CATS:
        out[c] = g.cat.apply(lambda x, c=c: (x == c).mean() * 100)
    out['trans'] = g.trans.mean() * 100
    out['trans_pps'] = s[s.trans].groupby(key).pts.mean()
    out['halfcourt_pps'] = s[~s.trans].groupby(key).pts.mean()
    out['late'] = g.late.mean() * 100
    out['ast'] = s[s.made].groupby(key).ast.mean() * 100
    return out.round(3)


def ranked(p):
    for c in CATS + ['trans', 'late', 'ast', 'trans_pps', 'halfcourt_pps']:
        p[c + '_rk'] = p[c].rank(ascending=False, method='min').astype('Int64')
    return p


if __name__ == '__main__':
    D = sys.argv[1]; MMDD = D[-4:]
    DATE = sys.argv[2] if len(sys.argv) > 2 else f"{dt.date.today().year}-{MMDD[:2]}-{MMDD[2:]}"
    yr = int(DATE[:4]) + (1 if int(DATE[5:7]) >= 8 else 0)
    pbp = pd.read_parquet(f'{ROOT}/pbp/parquet/play_by_play_{yr}.parquet')
    pbp = pbp[pd.to_datetime(pbp.game_date).dt.strftime('%Y-%m-%d') < DATE]
    s = shots(pbp)
    O = ranked(profile(s, 'off')).add_prefix('o_'); X = ranked(profile(s, 'opp')).add_prefix('d_')
    T = O.join(X, how='outer'); T.index.name = 'team'
    T.to_csv(f'{D}/style_team.csv')
    games = json.load(open(f'{D}/lines.json'))['games'] if os.path.exists(f'{D}/lines.json') else []
    lab = {'rim': 'rim shots', 'spot3': 'spot-up 3s', 'pull3': 'pull-up 3s', 'pull2': 'pull-up 2s', 'trans': 'transition', 'late': 'late-clock shots'}
    notes, log = [], []
    for g in games:
        gk = f"{g['away']}@{g['home']}"
        for tm, op in ((g['away'], g['home']), (g['home'], g['away'])):
            if tm not in T.index or op not in T.index:
                continue
            a, b = T.loc[tm], T.loc[op]
            for c in ('rim', 'spot3', 'pull3', 'pull2', 'trans'):
                if a[f'o_{c}_rk'] <= 8 and b[f'd_{c}_rk'] <= 8:      # what they like, the defense gives up
                    notes.append(dict(game=gk, team=tm, kind='edge', note=f"{tm} offense top-8 in {lab[c]} ({a[f'o_{c}']:.1f}%, #{int(a[f'o_{c}_rk'])}) vs {op} D that allows #{int(b[f'd_{c}_rk'])}"))
                if a[f'o_{c}_rk'] <= 8 and b[f'd_{c}_rk'] >= 23:     # what they like, the defense takes away
                    notes.append(dict(game=gk, team=tm, kind='clash', note=f"{tm} leans on {lab[c]} (#{int(a[f'o_{c}_rk'])}) but {op} D takes it away (#{int(b[f'd_{c}_rk'])} allowed)"))
            if a['o_late_rk'] <= 8:
                notes.append(dict(game=gk, team=tm, kind='watch', note=f"{tm} offense often stuck late in the clock ({a['o_late']:.1f}% of shots, #{int(a['o_late_rk'])})"))
            log.append(dict(date=DATE, game=gk, team=tm, opp=op, home=int(tm == g['home']), mkt_spread_team=g['home_spread'] if tm == g['home'] else -g['home_spread'],
                            mkt_total=g['total'], **{f'o_{c}': a[f'o_{c}'] for c in CATS + ['trans', 'late', 'ast', 'halfcourt_pps', 'trans_pps']},
                            **{f'd_{c}': b[f'd_{c}'] for c in CATS + ['trans', 'late', 'ast', 'halfcourt_pps', 'trans_pps']}))
    pd.DataFrame(notes, columns=['game', 'team', 'kind', 'note']).to_csv(f'{D}/style_notes.csv', index=False)
    if log:
        L = pd.DataFrame(log)
        if os.path.exists('slate/style_log.csv'):
            old = pd.read_csv('slate/style_log.csv'); L = pd.concat([old[old.date != DATE], L])
        L.to_csv('slate/style_log.csv', index=False)
    print(f'{len(T)} teams, {s.game_id.nunique()} games, {len(notes)} notes -> {D}/style_team.csv, style_notes.csv')
