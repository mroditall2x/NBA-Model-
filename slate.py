"""Run a slate: model spread/total/ML vs market, every prop vs the market's no-vig line, first field goal.
Usage: python3 slate.py slate/2026-10-20.json"""
import json, sys, glob, os
import numpy as np, pandas as pd
import nba_sim as S, first_basket as F

STAT_MAP = {'Points': 'pts', 'Rebounds': 'reb', 'Assists': 'ast', 'Points + Assists': 'pa', 'Points + Rebounds': 'pr',
            'Rebounds + Assists': 'ra', 'Pts + Reb + Ast': 'pra', 'Steals': 'stl', 'Blocks': 'blk', 'Steals + Blocks': 'stocks'}
LABEL = {v: k for k, v in STAT_MAP.items()}
LABEL.update(pra='PRA', pr='PR', pa='PA', ra='RA', stocks='STL+BLK', pts='PTS', reb='REB', ast='AST', stl='STL', blk='BLK')
N = 20000


def imp(o):
    return -o / (-o + 100) if o < 0 else 100 / (o + 100)


def american(p):
    p = float(np.clip(p, 1e-4, 0.9999))
    return f"{-round(100 * p / (1 - p)):+d}" if p >= 0.5 else f"+{round(100 * (1 - p) / p)}"


def main(cfg_path):
    cfg = json.load(open(cfg_path))
    asof = pd.Timestamp(cfg['date'])
    p, t = S.load((2025, 2026)); pri = S.pos_priors(p)
    lg = S.league(t[t.season == 2026])
    R = pd.read_parquet(f'{S.ROOT}/rosters/parquet/rosters_2027.parquet'); R['pid'] = R.athlete_id.astype('int64')
    name2pid = dict(zip(R.display_name, R.pid))
    fbm = F.fit(F.build(), p)
    games_out, props_out, fb_out = [], [], []
    for g in cfg['games']:
        trk = cfg.get('tracking', {})
        mk = lambda side: S.apply_tracking(S.build_side(p, t, g[side], asof, lg, pri, players=[name2pid[n] for n in g['minutes'][side]],
                                                        minutes=g['minutes'][side]), trk)
        # model-only numbers (for spread/total/ML edges) and market-anchored run (for props)
        Gm = S.Game(mk('home'), mk('away'), lg, np.random.default_rng(1)); scm, _ = Gm.run(N)
        Gk = S.Game(mk('home'), mk('away'), lg, np.random.default_rng(2))
        sck, boxes = Gk.run(N, spread=g['home_spread'], total=g['total'])
        df = S.to_frame(Gk, boxes)
        mm = scm[:, 0] - scm[:, 1]; mt = scm.sum(1)
        ml_h, ml_a = imp(g['ml_home']), imp(g['ml_away'])
        sp_h, sp_a = imp(g['spread_odds'][0]), imp(g['spread_odds'][1])
        to_o, to_u = imp(g['total_odds'][0]), imp(g['total_odds'][1])
        pace_model = Gm.targets[2]
        games_out.append(dict(game=f"{g['away']} @ {g['home']}", poss=round(pace_model, 1),
                              pace_home_outlier=g['outlier_pace'][g['home']], pace_away_outlier=g['outlier_pace'][g['away']],
                              model_home_pts=round(scm[:, 0].mean(), 1), model_away_pts=round(scm[:, 1].mean(), 1),
                              model_spread_home=round(-mm.mean(), 1), mkt_spread_home=g['home_spread'],
                              p_home_cover=round((mm + g['home_spread'] > 0).mean(), 3), mkt_home_cover=round(sp_h / (sp_h + sp_a), 3),
                              model_total=round(mt.mean(), 1), mkt_total=g['total'],
                              p_over=round((mt > g['total']).mean(), 3), mkt_over=round(to_o / (to_o + to_u), 3),
                              p_home_win=round((mm > 0).mean(), 3), mkt_home_win=round(ml_h / (ml_h + ml_a), 3),
                              public=g.get('public', '')))
        # props
        for f in glob.glob(os.path.join(os.path.dirname(cfg_path), g['props_glob'])):
            for title, line, oo, uo in json.load(open(f)):
                pl, st = title.split(' - ', 1)
                if st not in STAT_MAP: continue
                key = STAT_MAP[st]
                x = df[df.player == pl][key].values
                if not len(x):
                    props_out.append(dict(game=g['away'] + '@' + g['home'], player=pl, stat=LABEL[key], line=line, note='not in model rotation'))
                    continue
                po, pu = (x > line).mean(), (x < line).mean()
                mo, mu = imp(oo), imp(uo)
                mkt_over = mo / (mo + mu)
                p_over = po / (po + pu) if (po + pu) > 0 else 0.5   # push-excluded
                props_out.append(dict(game=g['away'] + '@' + g['home'], player=pl, stat=LABEL[key], line=line,
                                      proj=round(np.median(x), 1), mean=round(x.mean(), 2), p_over=round(p_over, 3),
                                      mkt_over=round(mkt_over, 3), edge=round(p_over - mkt_over, 3),
                                      pp_line=(float(line).is_integer() and oo == uo == -119)))
        # first field goal
        fb = g.get('first_fg')
        hs, as_ = [name2pid[n] for n in g['starters']['home']], [name2pid[n] for n in g['starters']['away']]
        res = F.price(fbm, hs, as_, name2pid[g['jumpers']['home']], name2pid[g['jumpers']['away']],
                      names={v: k for k, v in name2pid.items()})
        tb = res['table']
        if fb:
            book = {k: imp(v) for k, v in fb.items()}
            s = sum(book.values())
            tb['book_odds'] = tb.player.map(lambda n: fb.get(n))
            tb['book_novig'] = tb.player.map(lambda n: round(book[n] / s, 4) if n in book else None)
            tb['edge'] = (tb.p_first_fg - tb.book_novig).round(4)
            tb['ev_per_$1'] = tb.apply(lambda r: round(r.p_first_fg * (r.book_odds / 100 if r.book_odds > 0 else 100 / -r.book_odds) - (1 - r.p_first_fg), 3) if r.book_odds == r.book_odds and r.book_odds is not None else None, axis=1)
        tb.insert(0, 'game', g['away'] + '@' + g['home'])
        tb['p_team_tip'] = np.where(tb.side == 'home', res['p_home_tip'], 1 - res['p_home_tip'])
        fb_out.append(tb)
    G = pd.DataFrame(games_out); P = pd.DataFrame(props_out); FB = pd.concat(fb_out)
    out = os.path.splitext(cfg_path)[0]
    G.to_csv(out + '_games.csv', index=False); P.to_csv(out + '_props.csv', index=False); FB.to_csv(out + '_firstfg.csv', index=False)
    return G, P, FB


if __name__ == '__main__':
    G, P, FB = main(sys.argv[1])
    pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
    print(G.T.to_string())
    print(P.sort_values('edge').to_string())
    print(FB.to_string())
