"""Full-slate prop run for 2026-10-21 (generic: python3 slate1021.py DATE DIR)."""
import json, sys, unicodedata, glob, os
import numpy as np, pandas as pd
import nba_sim as S

DATE = sys.argv[1] if len(sys.argv) > 1 else '2026-10-21'
DIR = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'slate/1021'
N = 20000
STAT = {'PTS': 'pts', 'REB': 'reb', 'AST': 'ast', 'PA': 'pa', 'PR': 'pr', 'RA': 'ra', 'PRA': 'pra', 'STL': 'stl', 'BLK': 'blk', 'SB': 'stocks'}
ALIAS = {'bobby portis jr': 'bobby portis', 'nicolas claxton': 'nic claxton'}


def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().replace('.', '').replace("'", '').strip()
    return ALIAS.get(s, s)


def imp(o):
    return -o / (-o + 100) if o < 0 else 100 / (o + 100)


p, t = S.load((2025, 2026)); pri = S.pos_priors(p); lg = S.league(t[t.season == 2026])
R = pd.read_parquet(f'{S.ROOT}/rosters/parquet/rosters_2027.parquet'); R['pid'] = R.athlete_id.astype('int64')
rot = json.load(open(f'slate/{DATE}_rotations.json'))
lines = json.load(open(f'{DIR}/lines.json'))['games']
P = pd.concat([pd.read_csv(f, sep='|', header=None, names=['game', 'player', 'stat', 'line', 'o', 'u']) for f in sorted(glob.glob(f'{DIR}/props_p*.txt'))])
P['key'] = P.player.map(norm)

# name -> pid / last team / history
last = p.sort_values('game_date').groupby('pid').tail(1)
hist_name = {norm(n): pid for n, pid in zip(last.name, last.pid)}
last_team = dict(zip(last.pid, last.team))
roster_team = {norm(n): (pid, tm) for n, pid, tm in zip(R.display_name, R.pid, R.team_abbreviation)}
name_of = {}


def season_minutes(pid):
    h = p[p.pid == pid]
    if not len(h):
        return 18.0                      # rookie with live props: plays, minutes unknown
    l = h[h.season == h.season.max()]
    return float(l['min'].mean()) if len(l) >= 15 else float(h['min'].tail(10).mean())


MOVR = json.load(open(f'{DIR}/min_override.json')) if os.path.exists(f'{DIR}/min_override.json') and '--blend' in sys.argv else {}
GTD = {norm(x) for x in json.load(open(f'{DIR}/gtd.json'))}
notes, out_guess, rows, games_out = [], [], [], []
for g in lines:
    home, away = g['home'], g['away']; gk = f'{away}@{home}'
    gp = P[P.game == gk]
    prop_keys = set(gp.key)
    teams = {}
    for tm in (home, away):
        m = {norm(n): v for n, v in rot[tm].items()}
        # rotation players with no props at all and real minutes -> likely out
        for k, v in list(m.items()):
            if k not in prop_keys and (k in GTD or v >= 27) and not os.environ.get('NO_OUTGUESS'):
                out_guess.append((gk, tm, k, v)); m.pop(k)
        teams[tm] = m
    # prop players missing from rotations
    for k in prop_keys:
        if any(k in teams[tm] for tm in (home, away)):
            continue
        pid, tm = roster_team.get(k, (hist_name.get(k), None))
        if pid is None:
            notes.append((gk, k, 'no NBA history (rookie) - pass')); continue
        if tm not in (home, away):
            tm = last_team.get(pid) if last_team.get(pid) in (home, away) else None
        if tm is None:
            # decide by which team's props list... fall back: skip
            notes.append((gk, k, 'team unknown - pass')); continue
        teams[tm][k] = season_minutes(pid)
        notes.append((gk, k, f'added to {tm} at {teams[tm][k]:.0f} min'))
    sides = {}
    for tm in (home, away):
        m = teams[tm]
        for k in list(m):
            if k in MOVR:
                m[k] = MOVR[k]
        f = 240 / sum(m.values())
        m = {k: min(v * f, 38.0) for k, v in m.items()}
        pids, mins = [], {}
        for k, v in m.items():
            pid = roster_team.get(k, (hist_name.get(k), None))[0]
            if pid is None:
                continue
            pids.append(pid); mins[pid] = v; name_of[pid] = k
        sides[tm] = (pids, mins)
    print(gk, {tm: (len(sides[tm][0]), round(sum(sides[tm][1].values()))) for tm in sides}, flush=True)
    mk = lambda tm: S.build_side(p, t, tm, pd.Timestamp(DATE), lg, pri, players=sides[tm][0], minutes=sides[tm][1])
    Gm = S.Game(mk(home), mk(away), lg, np.random.default_rng(1)); scm, _ = Gm.run(N)
    Gk = S.Game(mk(home), mk(away), lg, np.random.default_rng(2)); _, boxes = Gk.run(N, spread=g['home_spread'], total=g['total'])
    df = S.to_frame(Gk, boxes); df['key'] = df.player.map(norm)
    if os.environ.get('SAVE_SIM'): df.to_parquet(f'{DIR}/sim_{gk}.parquet')
    mm = scm[:, 0] - scm[:, 1]; mt = scm.sum(1)
    sh, sa = imp(g['spread_odds'][0]), imp(g['spread_odds'][1]); oo, uu = imp(g['total_odds'][0]), imp(g['total_odds'][1])
    mh, ma = imp(g['ml_home']), imp(g['ml_away'])
    games_out.append(dict(game=gk, model_spread_home=round(-mm.mean(), 1), mkt_spread_home=g['home_spread'],
                          p_home_cover=round((mm + g['home_spread'] > 0).mean(), 3), mkt_home_cover=round(sh / (sh + sa), 3),
                          model_total=round(mt.mean(), 1), mkt_total=g['total'], p_over=round((mt > g['total']).mean(), 3),
                          mkt_over=round(oo / (oo + uu), 3), p_home_win=round((mm > 0).mean(), 3), mkt_home_win=round(mh / (mh + ma), 3),
                          poss=round(Gm.targets[2], 1)))
    for r in gp.itertuples():
        x = df[df.key == r.key][STAT[r.stat]].values
        if not len(x):
            rows.append(dict(game=gk, player=r.player, stat=r.stat, line=r.line, note='not modeled')); continue
        po, pu = (x > r.line).mean(), (x < r.line).mean()
        p_over = po / (po + pu) if po + pu else .5
        mo, mu_ = imp(r.o), imp(r.u); mkt = mo / (mo + mu_)
        pid = roster_team.get(r.key, (hist_name.get(r.key), None))[0]
        ng = int((p.pid == pid).sum()); lt = last_team.get(pid)
        tm = home if r.key in teams[home] else away
        rows.append(dict(game=gk, team=tm, player=r.player, stat=r.stat, line=r.line, mean=round(x.mean(), 2), p_over=round(p_over, 3),
                         mkt_over=round(mkt, 3), edge=round(p_over - mkt, 3), pp=(float(r.line).is_integer() and r.o == r.u == -119),
                         exp_min=round(df[df.key == r.key]['min'].mean(), 1), games=ng, new_team=(lt is not None and lt != tm)))
G = pd.DataFrame(games_out); B = pd.DataFrame(rows)
G.to_csv(f'{DIR}/games.csv', index=False); B.to_csv(f'{DIR}/board.csv', index=False)
pd.DataFrame(out_guess, columns=['game', 'team', 'player', 'proj_min']).to_csv(f'{DIR}/assumed_out.csv', index=False)
pd.DataFrame(notes, columns=['game', 'player', 'note']).to_csv(f'{DIR}/notes.csv', index=False)
print(G.to_string(index=False)); print('assumed out:', out_guess); print('notes:', len(notes)); print(B.note.value_counts() if 'note' in B else '')
