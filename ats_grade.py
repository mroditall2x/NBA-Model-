"""python3 ats_grade.py 2026-11-08 [more dates...]  -> appends each game to ats_log.csv and rebuilds ats_teams.csv.

ATS tracker (added 11/10). Per game: the spread/total from the day's last pull (slate/MMDD/lines.json; .open = morning
line), the final score (slate/MMDD/espn_box.csv, else hoopR team_box), and the model's side from games.csv.
ats_teams.csv = per team: ATS W-L-P, average cover margin, Over/Under, home/away, favorite/underdog, rest.
Model side record (does the model's spread lean beat the line?) prints at the end and lives in ats_log.csv.
Note: lines are our last pull before tip, not true closing lines. Small samples are noise; cover margin > W-L."""
import sys, os, json, pandas as pd

LOG = 'ats_log.csv'


def scores(date, D):
    if os.path.exists(f'{D}/espn_box.csv'):
        E = pd.read_csv(f'{D}/espn_box.csv')
        return {(g, tm): float(x) for (g, tm), x in E.groupby(['game', 'team']).PTS.sum().items()}, 'espn'
    f = 'repo/nba/team_box/parquet/team_box_2027.parquet'
    if not os.path.exists(f):
        return {}, None
    t = pd.read_parquet(f); t = t[t.game_date.astype(str).str[:10] == date]
    out = {}
    for r in t.itertuples():
        g1 = f'{r.opponent_team_abbreviation}@{r.team_abbreviation}' if r.team_home_away == 'home' else f'{r.team_abbreviation}@{r.opponent_team_abbreviation}'
        out[(g1, r.team_abbreviation)] = float(r.team_score)
    return out, 'hoopr'


def rest_days(date):
    f = 'repo/nba/team_box/parquet/team_box_2027.parquet'
    if not os.path.exists(f):
        return {}
    t = pd.read_parquet(f); t['d'] = pd.to_datetime(t.game_date.astype(str).str[:10]); t = t[t.d < pd.Timestamp(date)]
    last = t.groupby('team_abbreviation').d.max()
    return {tm: (pd.Timestamp(date) - d).days - 1 for tm, d in last.items()}


def grade(date):
    D = f'slate/{date[5:7]}{date[8:10]}'
    if not os.path.exists(f'{D}/lines.json'):
        print(date, 'no lines'); return []
    L = json.load(open(f'{D}/lines.json'))['games']
    O = {f"{g['away']}@{g['home']}": g for g in json.load(open(f'{D}/lines.json.open'))['games']} if os.path.exists(f'{D}/lines.json.open') else {}
    G = pd.read_csv(f'{D}/games.csv').set_index('game') if os.path.exists(f'{D}/games.csv') else pd.DataFrame()
    S, src = scores(date, D); rest = rest_days(date)
    rows = []
    for g in L:
        gk = f"{g['away']}@{g['home']}"; hs, as_ = S.get((gk, g['home'])), S.get((gk, g['away']))
        if hs is None or as_ is None or g.get('home_spread') is None:
            continue
        sp, tot = float(g['home_spread']), float(g['total'])
        cover = hs - as_ + sp                                  # >0 home covered
        res = 'push' if cover == 0 else ('home' if cover > 0 else 'away')
        m = G.loc[gk] if gk in G.index else None
        model_side, model_edge, model_res = '', None, ''
        if m is not None and pd.notna(m.get('model_spread_home')):
            model_edge = round(float(m['mkt_spread_home']) - float(m['model_spread_home']), 1)   # >0 model likes home
            if model_edge != 0:
                model_side = 'home' if model_edge > 0 else 'away'
                model_res = 'push' if res == 'push' else ('W' if res == model_side else 'L')
        o = O.get(gk, {})
        rows.append(dict(date=date, game=gk, home=g['home'], away=g['away'], home_score=hs, away_score=as_,
                         open_spread=o.get('home_spread'), home_spread=sp, cover_home=round(cover, 1), ats=res,
                         open_total=o.get('total'), total=tot, final_total=hs + as_,
                         ou='push' if hs + as_ == tot else ('over' if hs + as_ > tot else 'under'),
                         home_rest=rest.get(g['home']), away_rest=rest.get(g['away']),
                         model_side=model_side, model_edge=model_edge, model_ats=model_res,
                         skip_note=(m.get('full_game_note') if m is not None and pd.notna(m.get('full_game_note')) else ''), src=src))
    print(date, len(rows), 'games graded', f'({src})' if src else '')
    return rows


def teams(A):
    rows = []
    for _, r in A.iterrows():
        for tm, opp, side, sp, cov in ((r.home, r.away, 'home', r.home_spread, r.cover_home), (r.away, r.home, 'away', -r.home_spread, -r.cover_home)):
            rows.append(dict(team=tm, side=side, fav=sp < 0, cover=cov, res='P' if cov == 0 else ('W' if cov > 0 else 'L'), ou=r.ou,
                             rest=r.home_rest if side == 'home' else r.away_rest))
    T = pd.DataFrame(rows)
    rec = lambda x: f"{(x.res=='W').sum()}-{(x.res=='L').sum()}" + (f"-{(x.res=='P').sum()}" if (x.res == 'P').any() else '')
    out = []
    for tm, x in T.groupby('team'):
        out.append(dict(team=tm, games=len(x), ats=rec(x), avg_cover=round(x.cover.mean(), 1),
                        last5=rec(x.tail(5)), ou=f"{(x.ou=='over').sum()}-{(x.ou=='under').sum()}",
                        home=rec(x[x.side == 'home']), away=rec(x[x.side == 'away']),
                        fav=rec(x[x.fav]), dog=rec(x[~x.fav]),
                        rested=rec(x[x.rest >= 1]), b2b=rec(x[x.rest == 0])))
    return pd.DataFrame(out).sort_values('avg_cover', ascending=False)


if __name__ == '__main__':
    new = [r for d in sys.argv[1:] for r in grade(d)]
    A = pd.read_csv(LOG) if os.path.exists(LOG) else pd.DataFrame()
    if new:
        N = pd.DataFrame(new)
        A = pd.concat([A[~A.set_index(['date', 'game']).index.isin(N.set_index(['date', 'game']).index)] if len(A) else A, N])
        A = A.sort_values(['date', 'game']); A.to_csv(LOG, index=False)
    if len(A):
        T = teams(A); T.to_csv('ats_teams.csv', index=False)
        print(f"\n{len(A)} games {A.date.min()} to {A.date.max()} | favorites {(A.cover_home.where(A.home_spread<0,-A.cover_home)>0).mean():.0%} cover | overs {(A.ou=='over').mean():.0%}")
        M = A[A.model_ats.isin(['W', 'L'])]
        dog = (M.model_side == 'home') == (M.home_spread > 0)     # model took the underdog
        print(f"balance: model picked the underdog in {dog.mean():.0%} of games (aim ~50%) | "
              f"fav picks {(M[~dog].model_ats=='W').sum()}-{(M[~dog].model_ats=='L').sum()} | dog picks {(M[dog].model_ats=='W').sum()}-{(M[dog].model_ats=='L').sum()}")
        for lab, x in (('model side, all', M), ('model side, 3+ pts off', M[M.model_edge.abs() >= 3]), ('model side, not skipped', M[M.skip_note.fillna('') == ''])):
            print(f"{lab}: {(x.model_ats=='W').sum()}-{(x.model_ats=='L').sum()}" + (f" ({(x.model_ats=='W').mean():.0%})" if len(x) else ''))
        print('\n' + T.to_string(index=False))
