"""First-basket model (first made field goal of the game; free throws don't count).

P(player) = P(his team makes the first FG) x P(player | his team makes first FG)
- P(team first) from the opening tip: P(win tip) from both jumpers' shrunk tip records, and the
  league rate at which the tip-winning team makes the first FG (measured from play-by-play).
- P(player | team first) = his share of his team's first FGs in games he started, shrunk toward
  his share of starter shot attempts (FB_K pseudo-games).
"""
import numpy as np
import pandas as pd

ROOT = '/home/claude/nba/repo/nba'
TIP_K, FB_K = 20, 12


def build(seasons=(2025, 2026)):
    d = pd.concat([pd.read_parquet(f'{ROOT}/pbp/parquet/play_by_play_{s}.parquet',
                                   columns=['game_id', 'season', 'season_type', 'sequence_number', 'period_number', 'type_text',
                                            'scoring_play', 'score_value', 'shooting_play', 'team_id', 'athlete_id_1',
                                            'athlete_id_2', 'athlete_id_3', 'athlete_name_1', 'athlete_name_2', 'text',
                                            'home_team_id', 'away_team_id', 'home_team_abbrev', 'away_team_abbrev', 'game_date'])
                   for s in seasons])
    d = d[(d.season_type == 2) & (d.period_number == 1)].sort_values(['game_id', 'sequence_number'])
    tip = d[d.type_text == 'Jumpball'].groupby('game_id').head(1)
    tip = tip[['game_id', 'team_id', 'athlete_id_1', 'athlete_id_2', 'athlete_name_1', 'athlete_name_2', 'home_team_id', 'game_date']]
    fg = d[(d.scoring_play == True) & d.score_value.isin([2, 3])].groupby('game_id').head(1)
    fg = fg[['game_id', 'team_id', 'athlete_id_1', 'athlete_name_1']].rename(columns={'team_id': 'fb_team', 'athlete_id_1': 'fb_pid', 'athlete_name_1': 'fb_name'})
    g = tip.merge(fg, on='game_id')
    return g


def tip_rates(g, roster_team_of):
    """Each jumper's tip record. roster_team_of: dict pid -> team_id for that game is not available,
    so the winner is the jumper whose team gained possession (team_id), using box-score team ids."""
    return g


def fit(g, p):
    """g: output of build(); p: player box (from nba_sim.load) with pid/team/game_id/starter/fg2a/fg3a."""
    lk = p[['game_id', 'pid', 'team', 'starter', 'fg2a', 'fg3a']].copy()
    lk['fga'] = lk.fg2a + lk.fg3a
    tm = pd.read_parquet(f'{ROOT}/team_box/parquet/team_box_2026.parquet', columns=['team_id', 'team_abbreviation']).drop_duplicates()
    abbr = dict(zip(tm.team_id, tm.team_abbreviation))
    g = g.copy()
    g['tip_team'] = g.team_id.map(abbr); g['fb_team_ab'] = g.fb_team.map(abbr)
    # tip records
    j = pd.concat([g[['game_id', 'athlete_id_1', 'tip_team']].rename(columns={'athlete_id_1': 'pid'}),
                   g[['game_id', 'athlete_id_2', 'tip_team']].rename(columns={'athlete_id_2': 'pid'})]).dropna()
    j['pid'] = j.pid.astype('int64')
    j = j.merge(lk[['game_id', 'pid', 'team']], on=['game_id', 'pid'])
    j['won'] = (j.team == j.tip_team).astype(float)
    tip = j.groupby('pid').agg(tips=('won', 'size'), wins=('won', 'sum'))
    tip['rate'] = (tip.wins + TIP_K * 0.5) / (tip.tips + TIP_K)
    # tip winner makes the first FG
    p_tipwin_first = (g.tip_team == g.fb_team_ab).mean()
    # player shares among starters
    st = lk[lk.starter == True].copy()
    st['team_fga'] = st.groupby(['game_id', 'team']).fga.transform('sum')
    st['fga_share'] = st.fga / st.team_fga
    st = st.merge(g[['game_id', 'fb_team_ab', 'fb_pid']], on='game_id')
    st['team_first'] = st.team == st.fb_team_ab
    st['is_fb'] = st.pid == st.fb_pid
    sh = st.groupby('pid').agg(starts=('game_id', 'size'), team_firsts=('team_first', 'sum'),
                               fbs=('is_fb', 'sum'), fga_share=('fga_share', 'mean'))
    sh['share'] = (sh.fbs + FB_K * sh.fga_share) / (sh.team_firsts + FB_K)
    return dict(tip=tip, p_tipwin_first=p_tipwin_first, share=sh)


def american(p):
    p = float(np.clip(p, 1e-4, 0.9999))
    return f"{-round(100 * p / (1 - p)):+d}" if p >= 0.5 else f"+{round(100 * (1 - p) / p)}"


def price(model, home_starters, away_starters, home_jumper, away_jumper, names=None):
    """starters: lists of pids (5 each); jumpers: pids. Returns a table of first-basket probabilities."""
    tip, sh = model['tip'], model['share']
    rh = tip.rate.get(home_jumper, 0.5); ra = tip.rate.get(away_jumper, 0.5)
    p_home_tip = rh * (1 - ra) / (rh * (1 - ra) + ra * (1 - rh))
    q = model['p_tipwin_first']
    p_home_first = p_home_tip * q + (1 - p_home_tip) * (1 - q)
    rows = []
    for team_p, pids, side in ((p_home_first, home_starters, 'home'), (1 - p_home_first, away_starters, 'away')):
        s = np.array([sh.share.get(x, 0.2) for x in pids], float)
        s = s / s.sum()
        for pid, si in zip(pids, s):
            pr = team_p * si
            rows.append(dict(side=side, pid=pid, player=(names or {}).get(pid, pid), p_first_fg=round(pr, 4),
                             fair_odds=american(pr), starts_sample=int(sh.starts.get(pid, 0)), first_fgs=int(sh.fbs.get(pid, 0))))
    out = pd.DataFrame(rows).sort_values('p_first_fg', ascending=False)
    return dict(p_home_tip=round(p_home_tip, 3), p_home_first=round(p_home_first, 3), table=out)
