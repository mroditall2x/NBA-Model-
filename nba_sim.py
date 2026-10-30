"""NBA full-game Monte Carlo (v1) for player props + spread/total.

Design
- Team level (stage 1): shared possessions (pace of both teams, log5), shot volumes per possession
  (team offense x opponent defense / league), shot mix + make % built bottom-up from the players
  expected on the floor (so injuries change team efficiency), opponent defensive make-% factor,
  game shocks, credited rebounds from misses, assists from makes, TOV/STL/BLK, overtime.
- Player level (stage 2): minutes ~ Normal(recent mean, sd), blowout logic from the simulated
  final margin (core players sit, bench absorbs), every team total allocated to players in
  proportion to (per-minute rate x minutes) with Dirichlet overdispersion. Team totals are
  preserved exactly, so player props are correlated with the score and with each other.
- Targeting: optional market spread/total (or the model's own numbers) set team expected points
  exactly by scaling possessions (half of the total gap) and 2P/3P make probability.
"""
import os
import numpy as np
import pandas as pd

ROOT = os.environ.get('NBA_DATA', '/home/claude/nba/repo/nba')
TEAM_HL, PLAYER_HL, MIN_HL = 25, 30, 6          # half-lives in games
SEASON_DISC = 0.7                               # weight multiplier for prior-season games
TEAM_K, P2_K, P3_K, FT_K = 8, 100, 150, 40
RATE_K = float(os.environ.get('RATE_K', 60))
USAGE_POW = float(os.environ.get('USAGE_POW', 1.1))
PACE_SD, SHOCK_SD, SHOCK3_SD, COMMON_SD, COMP = 0.02, 0.0, 0.05, 0.0, 0.14
DIR_CONC = float(os.environ.get('DIR_CONC', 120.0))                                # Dirichlet concentration (lower = more spread)
AND1 = 0.035
MARGIN_INFLATE = 1.25
HOME_EDGE = 2.0                                 # points, used only in model mode
MIN_SD_SCALE = float(os.environ.get('MIN_SD_SCALE', 0.75))
CORE_MIN = float(os.environ.get('CORE_MIN', 26))
BLOWOUT_CUT = 0.25
OPP_MODE = int(os.environ.get('OPP_MODE', 0))      # 1 = REB/AST from on-court chances (potential REB/AST proxy)
REB_K = float(os.environ.get('REB_K', 100)); AST_K = float(os.environ.get('AST_K', 100))
OPP_BLEND = float(os.environ.get('OPP_BLEND', 1.0))  # weight on chance-based rate vs raw per-minute rate
STATS = ['fg2a', 'fg3a', 'fta', 'oreb', 'dreb', 'ast', 'tov', 'stl', 'blk']


# ---------------------------------------------------------------- data
def load(seasons=(2025, 2026, 2027)):
    pb, games = [], []
    for s in seasons:
        f = f'{ROOT}/player_box/parquet/player_box_{s}.parquet'
        if os.path.exists(f):
            pb.append(pd.read_parquet(f))
    p = pd.concat(pb)
    p = p[(p.season_type == 2) & (~p.did_not_play.fillna(False)) & (p.minutes.fillna(0) > 0)].copy()
    p = p[~p.team_abbreviation.isin(['WORLD', 'STARS', 'STRIPES'])]
    for c in ['field_goals_made', 'field_goals_attempted', 'three_point_field_goals_made', 'three_point_field_goals_attempted',
              'free_throws_made', 'free_throws_attempted', 'offensive_rebounds', 'defensive_rebounds', 'assists',
              'turnovers', 'steals', 'blocks', 'points', 'minutes']:
        p[c] = p[c].fillna(0).astype(float)
    p = p.rename(columns={'three_point_field_goals_made': 'fg3m', 'three_point_field_goals_attempted': 'fg3a',
                          'free_throws_made': 'ftm', 'free_throws_attempted': 'fta', 'offensive_rebounds': 'oreb',
                          'defensive_rebounds': 'dreb', 'assists': 'ast', 'turnovers': 'tov', 'steals': 'stl',
                          'blocks': 'blk', 'points': 'pts', 'minutes': 'min', 'team_abbreviation': 'team',
                          'opponent_team_abbreviation': 'opp', 'athlete_display_name': 'name', 'athlete_id': 'pid'})
    p['fg2a'] = p.field_goals_attempted - p.fg3a
    p['fg2m'] = p.field_goals_made - p.fg3m
    p['reb'] = p.oreb + p.dreb
    p['pos'] = p.athlete_position_abbreviation.fillna('F').str[-1].map({'C': 'C', 'G': 'G'}).fillna('F')
    p['pid'] = p.pid.astype('int64')
    p['game_date'] = pd.to_datetime(p.game_date)
    keep = ['game_id', 'season', 'game_date', 'pid', 'name', 'team', 'opp', 'home_away', 'starter', 'pos', 'min',
            'fg2m', 'fg2a', 'fg3m', 'fg3a', 'ftm', 'fta', 'oreb', 'dreb', 'reb', 'ast', 'tov', 'stl', 'blk', 'pts']
    p = p[keep].sort_values(['game_date', 'game_id'])
    oc = [pd.read_parquet(f) for f in [os.path.join(os.path.dirname(os.path.dirname(ROOT)), f'oncourt_{s}.parquet') for s in seasons] if os.path.exists(f)]
    if oc:
        p = p.merge(pd.concat(oc), on=['game_id', 'pid'], how='left')
    for c in ['oreb_ch', 'dreb_ch', 'tm_fga_on', 'tm_fgm_on', 'on_min']:
        if c not in p:
            p[c] = np.nan
    # team-game table from player sums (consistent with what props pay)
    agg = p.groupby(['game_id', 'season', 'game_date', 'team', 'opp', 'home_away'], as_index=False)[
        ['min', 'fg2m', 'fg2a', 'fg3m', 'fg3a', 'ftm', 'fta', 'oreb', 'dreb', 'ast', 'tov', 'stl', 'blk', 'pts']].sum()
    agg['poss'] = agg.fg2a + agg.fg3a - agg.oreb + agg.tov + 0.44 * agg.fta
    o = agg.rename(columns={c: 'o_' + c for c in agg.columns if c not in ('game_id', 'season', 'game_date', 'team', 'opp', 'home_away')})
    t = agg.merge(o.drop(columns=['season', 'game_date', 'opp', 'home_away']).rename(columns={'team': 'opp'}), on=['game_id', 'opp'])
    t['gposs'] = (t.poss + t.o_poss) / 2
    t['ot'] = np.clip(np.round((t['min'] - 240) / 25), 0, 4)
    return p, t.sort_values(['game_date', 'game_id'])


def _w(n_games_ago, season_flags, hl):
    return 0.5 ** (n_games_ago / hl) * np.where(season_flags, SEASON_DISC, 1.0)


def league(t):
    s = t[['fg2a', 'fg3a', 'fta', 'tov', 'fg2m', 'fg3m', 'ftm', 'oreb', 'dreb', 'ast', 'stl', 'blk', 'pts', 'gposs', 'min']].sum()
    poss48 = (t.gposs * 240 / t['min']).mean()
    o_miss = (t.fg2a + t.fg3a - t.fg2m - t.fg3m)
    return dict(poss48=poss48, r2=s.fg2a / s.gposs, r3=s.fg3a / s.gposs, rft=s.fta / s.gposs, rtov=s.tov / s.gposs,
                p2=s.fg2m / s.fg2a, p3=s.fg3m / s.fg3a, pft=s.ftm / s.fta, orb=s.oreb / o_miss.sum(),
                drb=(t.o_dreb.sum()) / (o_miss.sum() - t.oreb.sum()), astr=s.ast / (s.fg2m + s.fg3m),
                stlr=s.stl / t.o_tov.sum(), blkr=s.blk / (t.o_fg2a - t.o_fg2m).sum(), pts=t.pts.mean())


def team_profile(t, team, asof, lg):
    """Recency-weighted, league-regressed team offense/defense rates as of a date (exclusive)."""
    x = t[(t.team == team) & (t.game_date < asof)]
    if not len(x):
        return dict(off={k: 1.0 for k in ['r2', 'r3', 'rft', 'rtov', 'orb', 'astr', 'pace']},
                    dfn={k: 1.0 for k in ['r2', 'r3', 'rft', 'rtov', 'p2', 'p3', 'orb', 'drb', 'stlr', 'blkr']})
    cur = x.season.max()
    ago = np.arange(len(x))[::-1]
    w = _w(ago, (x.season < cur).values, TEAM_HL)
    W = w.sum()

    def ratio(num, den, lgv):  # weighted ratio regressed to league, returned as multiplier vs league
        n, d = (w * num).sum(), (w * den).sum()
        val = (n / d) if d > 0 else lgv
        return (W * val + TEAM_K * lgv) / (W + TEAM_K) / lgv

    miss = x.fg2a + x.fg3a - x.fg2m - x.fg3m
    omiss = x.o_fg2a + x.o_fg3a - x.o_fg2m - x.o_fg3m
    off = dict(r2=ratio(x.fg2a, x.gposs, lg['r2']), r3=ratio(x.fg3a, x.gposs, lg['r3']),
               rft=ratio(x.fta, x.gposs, lg['rft']), rtov=ratio(x.tov, x.gposs, lg['rtov']),
               orb=ratio(x.oreb, miss, lg['orb']), astr=ratio(x.ast, x.fg2m + x.fg3m, lg['astr']),
               pace=ratio(x.gposs * 240, x['min'], lg['poss48']))
    dfn = dict(r2=ratio(x.o_fg2a, x.gposs, lg['r2']), r3=ratio(x.o_fg3a, x.gposs, lg['r3']),
               rft=ratio(x.o_fta, x.gposs, lg['rft']), rtov=ratio(x.o_tov, x.gposs, lg['rtov']),
               p2=ratio(x.o_fg2m, x.o_fg2a, lg['p2']), p3=ratio(x.o_fg3m, x.o_fg3a, lg['p3']),
               orb=ratio(x.o_oreb, omiss, lg['orb']), drb=ratio(x.dreb, omiss - x.o_oreb, lg['drb']),
               stlr=ratio(x.stl, x.o_tov, lg['stlr']), blkr=ratio(x.blk, x.o_fg2a - x.o_fg2m, lg['blkr']))
    return dict(off=off, dfn=dfn)


def pos_priors(p):
    s = p.groupby('pos')[['min'] + STATS + ['fg2m', 'fg3m', 'ftm']].sum()
    pri = {pos: {k: s.loc[pos, k] / s.loc[pos, 'min'] for k in STATS} for pos in s.index}
    for pos in s.index:
        pri[pos].update(p2=s.loc[pos, 'fg2m'] / s.loc[pos, 'fg2a'], p3=s.loc[pos, 'fg3m'] / s.loc[pos, 'fg3a'],
                        pft=s.loc[pos, 'ftm'] / s.loc[pos, 'fta'])
    x = p.dropna(subset=['on_min'])
    for pos in s.index:
        y = x[x.pos == pos]
        pri[pos].update(oreb_pct=y.oreb.sum() / y.oreb_ch.sum(), dreb_pct=y.dreb.sum() / y.dreb_ch.sum(),
                        ast_pct=y.ast.sum() / y.tm_fgm_on.sum())
    pri['_ch'] = dict(oreb=x.oreb_ch.sum() / x.on_min.sum(), dreb=x.dreb_ch.sum() / x.on_min.sum(),
                      ast=x.tm_fgm_on.sum() / x.on_min.sum())
    return pri


def player_profile(p, pid, asof, pri, pos=None, name=None):
    x = p[(p.pid == pid) & (p.game_date < asof)]
    if pos is None:
        pos = x.pos.iloc[-1] if len(x) else 'F'
    pr = pri[pos]
    out = dict(pid=pid, name=name or (x.name.iloc[-1] if len(x) else str(pid)), pos=pos, n_games=len(x),
               last_team=x.team.iloc[-1] if len(x) else None)
    if not len(x):
        out.update({k: pr[k] for k in STATS}, p2=pr['p2'], p3=pr['p3'], pft=pr['pft'], mu=12.0, sd=6.0, starter_rate=0.0)
        return out
    cur = x.season.max()
    ago = np.arange(len(x))[::-1]
    w = _w(ago, (x.season < cur).values, PLAYER_HL)
    wm = (w * x['min']).sum()
    for k in STATS:
        out[k] = ((w * x[k]).sum() + RATE_K * pr[k]) / (wm + RATE_K)
    if OPP_MODE and x.on_min.notna().any():
        y = x.dropna(subset=['on_min']); wy = w[x.on_min.notna().values]
        for k, ch, pk, kk in (('oreb', 'oreb_ch', 'oreb_pct', REB_K), ('dreb', 'dreb_ch', 'dreb_pct', REB_K), ('ast', 'tm_fgm_on', 'ast_pct', AST_K)):
            pct = ((wy * y[k]).sum() + kk * pr[pk]) / ((wy * y[ch]).sum() + kk)
            out[k + '_chance_pct'] = pct
            out[k] = OPP_BLEND * pct * pri['_ch'][k] + (1 - OPP_BLEND) * out[k]
    for m, a, kk, pk in [('fg2m', 'fg2a', P2_K, 'p2'), ('fg3m', 'fg3a', P3_K, 'p3'), ('ftm', 'fta', FT_K, 'pft')]:
        out[pk] = ((w * x[m]).sum() + kk * pr[pk]) / ((w * x[a]).sum() + kk)
    wmin = 0.5 ** (ago / MIN_HL) * np.where(x.season.values < cur, 0.5, 1.0)
    mu = (wmin * x['min']).sum() / wmin.sum()
    sd = np.sqrt((wmin * (x['min'] - mu) ** 2).sum() / wmin.sum())
    out.update(mu=mu, sd=MIN_SD_SCALE * max(3.5, min(sd, 9.0)), starter_rate=(wmin * x.starter.astype(float)).sum() / wmin.sum())
    return out


# ---------------------------------------------------------------- sim
class Side:
    def __init__(self, code, players, prof):
        self.code, self.players, self.prof = code, players, prof
        self.mu = np.array([pl['mu'] for pl in players], float)
        self.sd = np.array([pl['sd'] for pl in players], float)
        self.rate = {k: np.array([pl[k] for pl in players], float) for k in STATS}
        self.pct = {k: np.array([pl[k] for pl in players], float) for k in ('p2', 'p3', 'pft')}
        self.names = [pl['name'] for pl in players]
        # scale expected minutes to 240 for team-level shot mix
        m = self.mu * 240 / self.mu.sum()
        self.m_exp = m

    def mix(self):
        m = self.m_exp
        a2, a3, af = (self.rate['fg2a'] * m), (self.rate['fg3a'] * m), (self.rate['fta'] * m)
        return dict(p2=(a2 * self.pct['p2']).sum() / a2.sum(), p3=(a3 * self.pct['p3']).sum() / a3.sum(),
                    pft=(af * self.pct['pft']).sum() / af.sum(), share3=a3.sum() / (a2.sum() + a3.sum()))


def _mn(rng, n, w):
    """multinomial draw per row: n (N,), w (N,k) nonnegative weights"""
    w = np.maximum(w, 1e-12)
    pv = w / w.sum(1, keepdims=True)
    return rng.multinomial(n.astype(np.int64), pv)


def _dirichlet(rng, base, conc):
    g = rng.gamma(np.maximum(base * conc, 1e-3), 1.0)
    return g


class Game:
    def __init__(self, home, away, lg, rng=None, home_edge=HOME_EDGE):
        self.h, self.a, self.lg = home, away, lg
        self.rng = rng or np.random.default_rng(7)
        self.home_edge = home_edge

    # expected team-level ingredients
    def _team_inputs(self, off, de):
        lg = self.lg
        mo, md = off.prof['off'], de.prof['dfn']
        mix = off.mix()
        # attempts per possession: total FGA rate from team (x opp), 3P share from roster blended with team
        fga = (lg['r2'] * mo['r2'] + lg['r3'] * mo['r3']) * ((lg['r2'] * md['r2'] + lg['r3'] * md['r3']) / (lg['r2'] + lg['r3']))
        team_share3 = lg['r3'] * mo['r3'] / (lg['r2'] * mo['r2'] + lg['r3'] * mo['r3'])
        lg_share3 = lg['r3'] / (lg['r2'] + lg['r3'])
        def_share3 = lg['r3'] * md['r3'] / (lg['r2'] * md['r2'] + lg['r3'] * md['r3'])
        share3 = (0.5 * mix['share3'] + 0.5 * team_share3) * def_share3 / lg_share3
        share3 = float(np.clip(share3, 0.2, 0.65))
        return dict(r2=fga * (1 - share3), r3=fga * share3, rft=lg['rft'] * mo['rft'] * md['rft'],
                    rtov=lg['rtov'] * mo['rtov'] * md['rtov'],
                    p2=mix['p2'] * md['p2'], p3=mix['p3'] * md['p3'], pft=mix['pft'],
                    orb=lg['orb'] * mo['orb'] * md['orb'], astr=lg['astr'] * mo['astr'],
                    drb_def=lg['drb'] * md['drb'], stl_def=lg['stlr'] * md['stlr'], blk_def=lg['blkr'] * md['blkr'])

    def expected(self):
        lg = self.lg
        poss = lg['poss48'] * self.h.prof['off']['pace'] * self.a.prof['off']['pace']
        ih, ia = self._team_inputs(self.h, self.a), self._team_inputs(self.a, self.h)
        e = lambda i: poss * (2 * i['r2'] * i['p2'] + 3 * i['r3'] * i['p3'] + i['rft'] * i['pft'])
        return poss, ih, ia, e(ih), e(ia)

    @staticmethod
    def _chain_params(i):
        x = (i['rft'] / 2) / (i['r2'] + i['r3'])
        return dict(f=x / (1 + x), s3=i['r3'] / (i['r2'] + i['r3']))

    @staticmethod
    def _exp_pts(i, poss, g=1.0):
        c = Game._chain_params(i); f, s3 = c['f'], c['s3']
        p2, p3 = i['p2'] * g, i['p3'] * g
        mbar = 1 - (s3 * p3 + (1 - s3) * p2)
        chances = (1 - i['rtov']) / (1 - (1 - f) * mbar * i['orb'])
        per = f * 2 * i['pft'] + (1 - f) * (s3 * 3 * p3 * (1 + AND1 * 0) + (1 - s3) * 2 * p2 * (1 + AND1 * i['pft'] / 2))
        return poss * chances * per

    def run(self, n=10000, spread=None, total=None):
        """spread = home line (negative = home favored, e.g. -5.5). Without lines: model mode + home edge."""
        rng, lg = self.rng, self.lg
        poss0, ih, ia, _, _ = self.expected()
        eh, ea = self._exp_pts(ih, poss0), self._exp_pts(ia, poss0)
        self.model_pts = (eh + self.home_edge / 2, ea - self.home_edge / 2)
        if total is None:
            th, ta = self.model_pts
        else:
            th, ta = (total - spread) / 2, (total + spread) / 2
        poss0 = poss0 * ((th + ta) / (eh + ea)) ** 0.5
        mid, half = (th + ta) / 2, (th - ta) / 2 * MARGIN_INFLATE   # Q4 compression shrinks margins; pre-inflate
        for i, tgt in ((ih, mid + half), (ia, mid - half)):
            g = 1.0
            for _ in range(30):
                g *= tgt / self._exp_pts(i, poss0, g)
            i['p2'] *= g; i['p3'] *= g
        self.targets = (th, ta, poss0)
        self.inputs = (ih, ia)

        poss = poss0 * rng.normal(1, PACE_SD, n)
        common = rng.normal(1, COMMON_SD, n)
        shock = {s: common * rng.normal(1, SHOCK_SD, n) for s in (0, 1)}
        shock3 = {s: shock[s] * rng.normal(1, SHOCK3_SD, n) for s in (0, 1)}
        keys = ['fg2a', 'fg3a', 'fta', 'fg2m', 'fg3m', 'ftm', 'tov', 'oreb', 'dreb', 'ast', 'stl', 'blk']
        tot = {s: {k: np.zeros(n, np.int64) for k in keys} for s in (0, 1)}
        ins = {0: ih, 1: ia}

        def chunk(rows, frac, adj=None):
            P = np.maximum(np.round(poss[rows] * frac), 1).astype(np.int64)
            for s in (0, 1):
                i, oi = ins[s], ins[1 - s]; c = self._chain_params(i)
                T, O = tot[s], tot[1 - s]
                a = 1.0 if adj is None else adj[s]
                p2 = np.clip(i['p2'] * shock[s][rows] * a, 0.05, 0.95); p3 = np.clip(i['p3'] * shock3[s][rows] * a, 0.05, 0.9)
                C = rng.binomial(P, 1 - i['rtov'])
                tov = P - C
                acc = {k: np.zeros(len(rows), np.int64) for k in keys}
                acc['tov'] += tov
                for _ in range(8):
                    if not C.any(): break
                    trips = rng.binomial(C, c['f']); shots = C - trips
                    a3 = rng.binomial(shots, c['s3']); a2 = shots - a3
                    m2 = rng.binomial(a2, p2); m3 = rng.binomial(a3, p3)
                    and1 = rng.binomial(m2, AND1)
                    fta = 2 * trips + and1
                    miss = shots - m2 - m3
                    oreb = rng.binomial(miss, np.clip(i['orb'], 0.05, 0.6))
                    acc['fg2a'] += a2; acc['fg3a'] += a3; acc['fg2m'] += m2; acc['fg3m'] += m3; acc['fta'] += fta
                    acc['oreb'] += oreb
                    acc['dreb'] += rng.binomial(miss - oreb, np.clip(oi['drb_def'], 0.3, 0.99))  # credited to opponent
                    acc['blk'] += rng.binomial(a2 - m2, np.clip(oi['blk_def'], 0.01, 0.3))        # credited to opponent
                    C = oreb
                acc['ftm'] = rng.binomial(acc['fta'], np.clip(i['pft'], 0.3, 0.98))
                acc['ast'] = rng.binomial(acc['fg2m'] + acc['fg3m'], np.clip(i['astr'], 0.3, 0.9))
                acc['stl'] = rng.binomial(acc['tov'], np.clip(oi['stl_def'], 0.2, 0.8))  # credited to opponent
                for k in ['fg2a', 'fg3a', 'fta', 'fg2m', 'fg3m', 'ftm', 'tov', 'oreb', 'ast']:
                    T[k][rows] += acc[k]
                for k in ['dreb', 'blk', 'stl']:
                    O[k][rows] += acc[k]

        pts = lambda T: 2 * T['fg2m'] + 3 * T['fg3m'] + T['ftm']
        allr = np.arange(n)
        chunk(allr, 0.75)
        lead = pts(tot[0]) - pts(tot[1])                      # home lead after 3 quarters
        c = COMP * np.clip(lead / 20, -1.5, 1.5)
        chunk(allr, 0.25, adj={0: 1 - c, 1: 1 + c})          # 4th quarter: leader eases, trailer pushes
        self.lead3 = lead
        ot = np.zeros(n, int)
        for _ in range(4):
            tie = np.where(pts(tot[0]) == pts(tot[1]))[0]
            if not len(tie): break
            ot[tie] += 1
            chunk(tie, 5 / 48)
        self.ot = ot
        sh, sa = pts(tot[0]), pts(tot[1])
        margin = sh - sa
        boxes = {0: self._players(self.h, tot[0], margin, ot), 1: self._players(self.a, tot[1], -margin, ot)}
        self.tot, self.score = tot, np.c_[sh, sa]
        return self.score, boxes

    def _players(self, side, T, margin, ot):
        rng, n = self.rng, len(margin)
        k = len(side.mu)
        m = np.clip(rng.normal(side.mu, side.sd, (n, k)), 0, 46)
        core = side.mu >= CORE_MIN
        b = np.clip((np.abs(margin) - 12) / 14, 0, 1)[:, None]
        cut = 1 - BLOWOUT_CUT * b
        cut = cut / cut.mean()                       # mean-preserving: history already contains blowouts
        m = np.where(core, m * cut, m)
        team_min = (240 + 25 * ot).astype(float)
        # OT minutes go mostly to the core
        ot_w = np.where(core, side.mu, 0.2 * side.mu); ot_w = ot_w / ot_w.sum()
        m = m + (25 * ot)[:, None] * ot_w
        m = np.minimum(m, 48 + 5 * ot[:, None])
        # bench absorbs whatever is left so the team plays exactly team_min
        core_sum = (m * core).sum(1); bench_sum = (m * ~core).sum(1)
        need = np.maximum(team_min - core_sum, 0)
        scale_b = np.where(bench_sum > 0, need / np.maximum(bench_sum, 1e-9), 0)
        m = np.where(core, m, m * scale_b[:, None])
        tot_m = m.sum(1)
        m = m * (team_min / tot_m)[:, None]          # tiny final correction (e.g. no bench listed)
        out = dict(min=m)
        for st in STATS:
            r = side.rate[st] ** USAGE_POW if st in ('fg2a', 'fg3a', 'fta', 'ast') else side.rate[st]
            base = r * m
            w = _dirichlet(rng, base / base.sum(1, keepdims=True), DIR_CONC) * (base > 0)
            out[st] = _mn(rng, T[st], w)
        for att, mk, pk in (('fg2a', 'fg2m', 'p2'), ('fg3a', 'fg3m', 'p3'), ('fta', 'ftm', 'pft')):
            out[mk] = self._alloc_makes(out[att], T[mk], side.pct[pk])
        out['reb'] = out['oreb'] + out['dreb']
        out['pts'] = 2 * out['fg2m'] + 3 * out['fg3m'] + out['ftm']
        return out

    def _alloc_makes(self, att, M, pct):
        rng = self.rng
        w = att * pct[None, :]
        mk = _mn(rng, M, w + 1e-9 * (att > 0))
        for _ in range(6):
            over = np.maximum(mk - att, 0)
            if not over.any(): break
            mk = mk - over
            spare = att - mk
            extra = _mn(rng, over.sum(1), spare * pct[None, :] + 1e-9 * (spare > 0))
            mk = mk + extra
        return np.minimum(mk, att)


def to_frame(game, boxes):
    """long table: sim, team, player, stats"""
    rows = []
    n = game.score.shape[0]
    for s, side in ((0, game.h), (1, game.a)):
        B = boxes[s]
        for j, nm in enumerate(side.names):
            d = {k: B[k][:, j] for k in ['min', 'pts', 'reb', 'ast', 'fg3m', 'fg3a', 'stl', 'blk', 'tov', 'oreb', 'dreb', 'fta', 'ftm']}
            d['sim'] = np.arange(n); d['team'] = side.code; d['player'] = nm
            rows.append(pd.DataFrame(d))
    df = pd.concat(rows, ignore_index=True)
    df['pra'] = df.pts + df.reb + df.ast; df['pr'] = df.pts + df.reb; df['pa'] = df.pts + df.ast
    df['ra'] = df.reb + df.ast; df['stocks'] = df.stl + df.blk
    return df


def build_side(p, t, team, asof, lg, pri, players=None, out=(), minutes=None):
    """players: list of pids (default: everyone who played for `team` in its last 10 games).
    out: pids or names to remove. minutes: {pid or name: expected minutes} overrides."""
    asof = pd.Timestamp(asof)
    if players is None:
        tg = t[(t.team == team) & (t.game_date < asof)].game_id.unique()[-10:]
        players = p[(p.team == team) & p.game_id.isin(tg)].pid.unique().tolist()
    profs = [player_profile(p, pid, asof, pri) for pid in players]
    out = set(out)
    profs = [x for x in profs if x['pid'] not in out and x['name'] not in out]
    minutes = minutes or {}
    for x in profs:
        for key in (x['pid'], x['name']):
            if key in minutes:
                x['mu'] = float(minutes[key])
    profs = [x for x in profs if x['mu'] >= 3]
    # rescale expected minutes toward 240 keeping the rotation shape
    tot = sum(x['mu'] for x in profs)
    if tot > 0:
        f = 240 / tot
        for x in profs:
            x['mu'] = min(x['mu'] * f, 40.0) if not any(k in minutes for k in (x['pid'], x['name'])) else x['mu']
    return Side(team, profs, team_profile(t, team, asof, lg))


TRACK_BLEND = float(os.environ.get('TRACK_BLEND', 0.5))   # untested until graded: half weight


def apply_tracking(side, tracking):
    """Blend real NBA.com tracking into a Side's per-minute REB/AST rates.
    tracking: {player name: {"min": mpg, "pot_ast": potential assists pg, "ast": ast pg,
                             "reb_ch": rebound chances pg, "reb": reb pg}}  (season or last-N per-game values)
    AST rate  <- pot_ast/min x league potential-assist conversion (sum ast / sum pot_ast over supplied players)
    REB rate  <- reb_ch/min x player's chance conversion shrunk halfway to the supplied players' average"""
    rows = [v for v in tracking.values() if v.get('min')]
    if not rows:
        return side
    conv_a = sum(v.get('ast', 0) for v in rows if v.get('pot_ast')) / max(sum(v.get('pot_ast', 0) for v in rows), 1e-9)
    conv_r = sum(v.get('reb', 0) for v in rows if v.get('reb_ch')) / max(sum(v.get('reb_ch', 0) for v in rows), 1e-9)
    for j, nm in enumerate(side.names):
        v = tracking.get(nm)
        if not v or not v.get('min'):
            continue
        if v.get('pot_ast'):
            tr = v['pot_ast'] / v['min'] * conv_a
            side.rate['ast'][j] = TRACK_BLEND * tr + (1 - TRACK_BLEND) * side.rate['ast'][j]
        if v.get('reb_ch'):
            own = v.get('reb', conv_r * v['reb_ch']) / v['reb_ch']
            tr = v['reb_ch'] / v['min'] * (0.5 * own + 0.5 * conv_r)
            cur = side.rate['oreb'][j] + side.rate['dreb'][j]
            f = (TRACK_BLEND * tr + (1 - TRACK_BLEND) * cur) / max(cur, 1e-9)
            side.rate['oreb'][j] *= f; side.rate['dreb'][j] *= f
    return side


def summarize(game, df, lines=None):
    sh, sa = game.score[:, 0], game.score[:, 1]
    g = dict(home=game.h.code, away=game.a.code, home_pts=np.median(sh), away_pts=np.median(sa),
             margin_mean=(sh - sa).mean(), total_mean=(sh + sa).mean(), home_win=(sh > sa).mean(), ot=(game.ot > 0).mean())
    proj = df.groupby(['team', 'player'])[['min', 'pts', 'reb', 'ast', 'fg3m', 'pra', 'stl', 'blk', 'tov']].mean().round(1)
    return g, proj.sort_values('min', ascending=False)


def prop_prob(df, player, stat, line):
    x = df[df.player == player][stat].values
    return dict(player=player, stat=stat, line=line, mean=x.mean().round(2), median=np.median(x),
                p_over=(x > line).mean().round(3), p_push=(x == line).mean().round(3))
