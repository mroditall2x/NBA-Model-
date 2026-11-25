"""REB / AST / RA team-play research.
For every REB/AST/RA prop on the board (slate/*/board_all.csv), build features from games BEFORE that date:
  - hit rate vs tonight's line (last 10 / season)
  - adjusted assists ("potential assist" proxy): assists scaled by how well teammates shot (league FG% / teammates' FG%)
  - rebound chances: (team misses + opp misses) x min/48 ; player's rebounds per chance
  - opponent: assists allowed per game, rebounds allowed to the player's position (G/F/C) per 36 vs league
Then test whether each feature predicts Over/Under AFTER the market chance is known (that's where money is)."""
import glob, sys, numpy as np, pandas as pd
REPO = sys.argv[1]; DATA = sys.argv[2]; OUT = sys.argv[3]

pb = pd.concat([pd.read_parquet(f'{DATA}/player_box/parquet/player_box_{s}.parquet') for s in (2026, 2027)])
pb = pb[(pb.season_type == 2) & (~pb.did_not_play.fillna(False)) & (pb.minutes.fillna(0) > 0)].copy()
pb['date'] = pd.to_datetime(pb.game_date)
pb['name'] = pb.athlete_display_name
pos = pb.athlete_position_abbreviation.fillna('F').str[0].map({'G': 'G', 'F': 'F', 'C': 'C', 'P': 'G', 'S': 'G'}).fillna('F')
pb['pos'] = pos
pb['ra'] = pb.rebounds + pb.assists
tb = pd.concat([pd.read_parquet(f'{DATA}/team_box/parquet/team_box_{s}.parquet') for s in (2026, 2027)])
tb = tb[tb.season_type == 2].copy()
tb['date'] = pd.to_datetime(tb.game_date)
tb['miss'] = tb.field_goals_attempted - tb.field_goals_made
opp = tb[['game_id', 'team_id', 'miss', 'field_goals_made', 'field_goals_attempted', 'assists', 'total_rebounds']].rename(
    columns={'team_id': 'opponent_team_id', 'miss': 'opp_miss', 'field_goals_made': 'o_fgm', 'field_goals_attempted': 'o_fga',
             'assists': 'o_ast', 'total_rebounds': 'o_reb'})
tb = tb.merge(opp, on=['game_id', 'opponent_team_id'], how='left')
pb = pb.merge(tb[['game_id', 'team_id', 'miss', 'opp_miss', 'field_goals_made', 'field_goals_attempted']].rename(
    columns={'field_goals_made': 't_fgm', 'field_goals_attempted': 't_fga'}), on=['game_id', 'team_id'], how='left')
lg_fg = (tb.field_goals_made.sum() / tb.field_goals_attempted.sum())
mate_fg = (pb.t_fgm - pb.field_goals_made) / (pb.t_fga - pb.field_goals_attempted).clip(lower=1)
pb['ast_adj'] = pb.assists * (lg_fg / mate_fg.clip(0.30, 0.65))        # potential-assist proxy
pb['reb_ch'] = (pb.miss + pb.opp_miss) * pb.minutes / 48.0              # rebound chances while on floor (approx)
pb = pb.sort_values('date')

# opponent profile per (opponent team, position): what players at that position did vs them, per 36
pb['opp_abbr'] = pb.opponent_team_abbreviation
pb['team_abbr'] = pb.team_abbreviation

rows = []
for f in sorted(glob.glob(f'{REPO}/slate/1[01]*/board_all.csv')):
    mmdd = f.split('/')[-2]
    date = pd.Timestamp(f'2026-{mmdd[:2]}-{mmdd[2:]}')
    b = pd.read_csv(f)
    b = b[b.stat.isin(['REB', 'AST', 'RA']) & ~b.type.fillna('').str.contains('goblin|demon', case=False)]
    b = b.dropna(subset=['line', 'market'])
    if not len(b):
        continue
    b = b.drop_duplicates(['player', 'stat', 'line'])
    hist = pb[pb.date < date]
    cur = hist[hist.season == 2027]
    today = pb[pb.date == date]
    # league per-36 by position this season (fallback last season early on)
    base = cur if len(cur) > 1500 else hist[hist.date >= date - pd.Timedelta(days=200)]
    lg36 = base.groupby('pos')[['rebounds', 'assists']].sum().div(base.groupby('pos').minutes.sum(), axis=0) * 36
    opp36 = base.groupby(['opp_abbr', 'pos'])[['rebounds', 'assists']].sum().div(
        base.groupby(['opp_abbr', 'pos']).minutes.sum(), axis=0) * 36
    oppg = base.groupby(['opp_abbr', 'game_id'])[['assists', 'rebounds']].sum().groupby('opp_abbr').mean()
    for r in b.itertuples():
        h = hist[hist.name == r.player]
        t = today[today.name == r.player]
        if len(h) < 5 or not len(t):
            continue
        t = t.iloc[0]
        col = {'REB': 'rebounds', 'AST': 'assists', 'RA': 'ra'}[r.stat]
        actual = t[col]
        if actual == r.line:
            continue
        hs = h[h.season == 2027]
        l10 = h.tail(10)
        p_over_mkt = r.market if r.side == 'More' else 1 - r.market
        p_over_model = r.model if r.side == 'More' else 1 - r.model
        pos_ = h.pos.iloc[-1]
        oppab = t.opp_abbr
        o36 = opp36.loc[(oppab, pos_)] if (oppab, pos_) in opp36.index else None
        m10 = l10.minutes.mean()
        # per-minute rates x recent minutes
        reb_rate = (l10.rebounds.sum() / l10.reb_ch.sum()) if l10.reb_ch.sum() > 0 else np.nan
        ch_pm = l10.reb_ch.sum() / l10.minutes.sum()
        astadj_pm = l10.ast_adj.sum() / l10.minutes.sum()
        ast_pm = l10.assists.sum() / l10.minutes.sum()
        reb_pm = l10.rebounds.sum() / l10.minutes.sum()
        rows.append(dict(
            date=date.date(), player=r.player, stat=r.stat, line=r.line, side=r.side, mkt_over=p_over_mkt, model_over=p_over_model,
            proj_mean=r.mean, actual=actual, over=int(actual > r.line), min_model=r.min, min_l10=m10, min_actual=t.minutes,
            hit_l10=(l10[col] > r.line).mean(), hit_season=(hs[col] > r.line).mean() if len(hs) >= 5 else np.nan,
            avg_l10=l10[col].mean(), med_l10=l10[col].median(),
            ast_l10=l10.assists.mean(), ast_adj_l10=l10.ast_adj.mean(), ast_gap=(astadj_pm - ast_pm) * r.min,
            reb_l10=l10.rebounds.mean(), reb_ch_l10=l10.reb_ch.mean(), reb_per_ch=reb_rate,
            pos=pos_, opp=oppab,
            opp_reb_pos=(o36['rebounds'] / lg36.loc[pos_, 'rebounds']) if o36 is not None else np.nan,
            opp_ast_pos=(o36['assists'] / lg36.loc[pos_, 'assists']) if o36 is not None else np.nan,
            opp_ast_g=oppg.assists.get(oppab, np.nan), opp_reb_g=oppg.rebounds.get(oppab, np.nan),
        ))
d = pd.DataFrame(rows)
d.to_csv(OUT, index=False)
print(len(d), 'props with results')
