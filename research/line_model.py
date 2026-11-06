"""Why might the line be wrong tonight?  Learns the gap between the closing line and the result.
python3 research/line_model.py            -> walk-forward backtest (train on earlier seasons, test on the next)
Target: home margin + home spread (ATS residual) and total - closing total. Features are pre-game only (games before the date):
team efficiency (season and last 10), pace, style (3PA / FT / OREB / TOV rates, fast-break and paint points), rest and
back-to-backs, and availability (production of regulars missing from tonight's box score = the final injury report).
The market line is an input, so the model only has to learn where the line is off. Factors come from XGBoost contributions."""
import os, sys, numpy as np, pandas as pd
ROOT = os.environ.get('NBA_DATA', 'repo/nba')
SEASONS = [2022, 2023, 2024, 2025, 2026, 2027]
N = lambda x: pd.to_numeric(x, errors='coerce').fillna(0)


def team_games():
    t = pd.concat([pd.read_parquet(f'{ROOT}/team_box/parquet/team_box_{s}.parquet') for s in SEASONS if os.path.exists(f'{ROOT}/team_box/parquet/team_box_{s}.parquet')])
    t = t[t.season_type == 2].copy()
    for c in ['team_score', 'opponent_team_score', 'field_goals_attempted', 'free_throws_attempted', 'offensive_rebounds', 'defensive_rebounds',
              'total_turnovers', 'three_point_field_goals_attempted', 'fast_break_points', 'points_in_paint', 'assists', 'field_goals_made']:
        t[c] = N(t[c])
    t['date'] = pd.to_datetime(t.game_date)
    t['poss'] = t.field_goals_attempted - t.offensive_rebounds + t.total_turnovers + 0.44 * t.free_throws_attempted
    o = t[['game_id', 'team_id', 'poss', 'field_goals_attempted', 'offensive_rebounds', 'defensive_rebounds', 'three_point_field_goals_attempted',
           'free_throws_attempted', 'total_turnovers', 'fast_break_points', 'points_in_paint']].rename(columns=lambda c: 'opp_' + c if c not in ('game_id',) else c)
    t = t.merge(o.rename(columns={'opp_team_id': 'opponent_team_id'}), on=['game_id', 'opponent_team_id'])
    t['gp'] = (t.poss + t.opp_poss) / 2
    t['ortg'] = t.team_score / t.gp * 100; t['drtg'] = t.opponent_team_score / t.gp * 100
    t['r3'] = t.three_point_field_goals_attempted / t.field_goals_attempted; t['rft'] = t.free_throws_attempted / t.field_goals_attempted
    t['orb'] = t.offensive_rebounds / (t.offensive_rebounds + t.opp_defensive_rebounds); t['tov'] = t.total_turnovers / t.gp
    t['fb'] = t.fast_break_points / t.gp * 100; t['paint'] = t.points_in_paint / t.gp * 100
    t['d_r3'] = t.opp_three_point_field_goals_attempted / t.opp_field_goals_attempted; t['d_tov'] = t.opp_total_turnovers / t.gp
    t['d_fb'] = t.opp_fast_break_points / t.gp * 100; t['d_paint'] = t.opp_points_in_paint / t.gp * 100
    return t.sort_values(['team_id', 'date'])


def rolling(t):
    """pre-game features: season-to-date (shrunk toward last season at the start) and last 10, all shifted one game."""
    feats = ['ortg', 'drtg', 'gp', 'r3', 'rft', 'orb', 'tov', 'fb', 'paint', 'd_r3', 'd_tov', 'd_fb', 'd_paint']
    g = t.groupby('team_id')
    out = t[['game_id', 'team_id', 'season', 'date', 'team_home_away', 'team_abbreviation', 'team_score', 'opponent_team_score']].copy()
    for f in feats:
        sea = t.groupby(['team_id', 'season'])[f].transform(lambda x: x.shift().expanding().mean())
        n = t.groupby(['team_id', 'season']).cumcount()
        prev = g[f].transform(lambda x: x.shift().rolling(82, min_periods=10).mean())          # last ~season, any season
        w = n / (n + 10)
        out[f] = np.where(n > 0, w * sea.fillna(prev) + (1 - w) * prev.fillna(sea), prev)
        out[f + '_l10'] = g[f].transform(lambda x: x.shift().rolling(10, min_periods=3).mean())
    out['net'] = out.ortg - out.drtg; out['net_l10'] = out.ortg_l10 - out.drtg_l10
    d = g.date.diff().dt.days
    out['rest'] = d.clip(upper=4).fillna(4); out['b2b'] = (d == 1).astype(int)
    out['g4'] = g.date.transform(lambda x: pd.Series(1, index=x.index).rolling(4).count()) if False else 0
    return out


def availability():
    """production of regulars (15+ min over the team's last 10 games) who are not in tonight's box score."""
    P = []
    for s in SEASONS:
        f = f'{ROOT}/player_box/parquet/player_box_{s}.parquet'
        if os.path.exists(f):
            P.append(pd.read_parquet(f, columns=['game_id', 'season_type', 'game_date', 'team_id', 'athlete_id', 'minutes', 'points', 'rebounds', 'assists', 'turnovers', 'did_not_play']))
    p = pd.concat(P); p = p[p.season_type == 2].copy()
    p['m'] = N(p.minutes); p['val'] = N(p.points) + 0.7 * N(p.rebounds) + 0.7 * N(p.assists) - N(p.turnovers)
    p['played'] = (p.m > 0) & ~p.did_not_play.fillna(False)
    p['date'] = pd.to_datetime(p.game_date)
    games = p[['game_id', 'team_id', 'date']].drop_duplicates().sort_values(['team_id', 'date'])
    pl = p[p.played][['game_id', 'team_id', 'athlete_id', 'm', 'val']]
    res = []
    for tid, gg in games.groupby('team_id'):
        ids = gg.game_id.tolist()
        x = pl[pl.team_id == tid]
        by = {gid: v for gid, v in x.groupby('game_id')}
        for i, gid in enumerate(ids):
            prev = [by[j] for j in ids[max(0, i - 10):i] if j in by]
            if len(prev) < 3:
                res.append((gid, tid, 0.0, 0.0)); continue
            h = pd.concat(prev); a = h.groupby('athlete_id').agg(m=('m', 'sum'), v=('val', 'sum'), n=('m', 'size'))
            a['mpg'] = a.m / len(prev); a['vpg'] = a.v / len(prev)
            reg = a[a.mpg >= 15]
            here = set(by[gid].athlete_id) if gid in by else set()
            miss = reg[~reg.index.isin(here)]
            res.append((gid, tid, float(miss.vpg.sum()), float(miss.mpg.sum())))
    return pd.DataFrame(res, columns=['game_id', 'team_id', 'miss_val', 'miss_min'])


def build():
    t = team_games(); r = rolling(t)
    r = r.merge(availability(), on=['game_id', 'team_id'], how='left').fillna({'miss_val': 0, 'miss_min': 0})
    h = r[r.team_home_away == 'home'].drop(columns='team_home_away'); a = r[r.team_home_away == 'away'].drop(columns=['team_home_away', 'season', 'date'])
    g = h.merge(a, on='game_id', suffixes=('_h', '_a'))
    L = pd.read_parquet(f'{ROOT}/betting_lines/closing_lines_odds_api.parquet')[['game_id', 'home_point', 'over_under']]
    L['game_id'] = L.game_id.astype(g.game_id.dtype)
    g = g.merge(L, on='game_id').dropna(subset=['home_point', 'over_under'])
    g['margin'] = g.team_score_h - g.opponent_team_score_h; g['total'] = g.team_score_h + g.opponent_team_score_h
    g['ats'] = g.margin + g.home_point; g['ou'] = g.total - g.over_under
    num = [c[:-2] for c in g.columns if c.endswith('_h') and c[:-2] not in ('team_id', 'team_abbreviation', 'team_score', 'opponent_team_score')]
    for c in num:
        g['dif_' + c] = g[c + '_h'] - g[c + '_a']
    return g


FEATS_ATS = ['home_point', 'dif_net', 'dif_net_l10', 'dif_ortg', 'dif_drtg', 'rest_h', 'rest_a', 'b2b_h', 'b2b_a', 'miss_val_h', 'miss_val_a',
             'dif_r3', 'dif_tov', 'dif_fb', 'dif_paint', 'dif_orb', 'dif_rft', 'fb_h', 'd_fb_a', 'fb_a', 'd_fb_h']
FEATS_OU = ['over_under', 'gp_h', 'gp_a', 'ortg_h', 'drtg_h', 'ortg_a', 'drtg_a', 'ortg_l10_h', 'ortg_l10_a', 'b2b_h', 'b2b_a', 'rest_h', 'rest_a',
            'miss_val_h', 'miss_val_a', 'fb_h', 'fb_a', 'd_fb_h', 'd_fb_a', 'r3_h', 'r3_a', 'rft_h', 'rft_a']
PARAMS = dict(n_estimators=300, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, min_child_weight=20, reg_lambda=5.0)


def backtest(g):
    import xgboost as xgb
    from sklearn.linear_model import Ridge
    out = []
    for test in (2025, 2026, 2027):
        tr, te = g[g.season < test], g[g.season == test]
        if not len(te):
            continue
        for tgt, F in (('ats', FEATS_ATS), ('ou', FEATS_OU)):
            Xtr, Xte = tr[F].fillna(0), te[F].fillna(0)
            m = xgb.XGBRegressor(**PARAMS).fit(Xtr, tr[tgt]); pr = m.predict(Xte)
            rg = Ridge(alpha=50).fit((Xtr - Xtr.mean()) / Xtr.std(), tr[tgt]); prl = rg.predict((Xte - Xtr.mean()) / Xtr.std())
            y = te[tgt].values
            for name, p_ in (('xgb', pr), ('ridge', prl)):
                for th in (0, 1.5, 3):
                    k = (np.abs(p_) >= th) & (y != 0)
                    w = (np.sign(p_[k]) == np.sign(y[k])).mean() if k.any() else np.nan
                    out.append(dict(test=test, target=tgt, model=name, edge_pts=th, bets=int(k.sum()), win=round(w, 3), corr=round(np.corrcoef(p_, y)[0, 1], 3)))
    return pd.DataFrame(out)


if __name__ == '__main__':
    g = build(); g.to_parquet(os.environ.get('LM_OUT', 'line_model_games.parquet'))
    print(len(g), 'games', g.groupby('season').size().to_dict())
    R = backtest(g); print(R.to_string(index=False)); print('break-even at -110: 52.4%')
