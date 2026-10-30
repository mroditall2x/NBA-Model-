---
name: nba-prop-model
description: Use when Deon asks to analyze, simulate, or grade NBA player props (PTS, REB, AST, PRA, PR, PA, RA, STL, BLK, STL+BLK), first basket, or a game's spread/total/moneyline, especially PrizePicks lines.
---

# NBA Prop Model

Deon (Houston, mostly PrizePicks) bets PTS, REB, AST, PRA, PR, PA, RA, STL, BLK, STL+BLK and first basket. Every slate follows the same order, ends with ONE clear final card, and gets graded afterward. The market is sharper than the model on sides; treat edges as leans sized small until the graded log proves otherwise.

## Files (workspace `~/nba`, rebuild if missing)
- `nba_sim.py` – engine (data load, team/player profiles, possession-chain game sim, player allocation).
- `first_basket.py` – first made FG model from play-by-play (tip win x tip-winner-scores-first x player share).
- `slate.py` + `slate/<date>.json` – runs a slate: model vs market sides/totals/ML, every prop vs no-vig market, first FG table.
- `backtest.py` – rolling backtest on last season vs closing lines.
- Data: `git clone --depth 1 --filter=blob:none --no-checkout https://github.com/sportsdataverse/hoopr-nba-data repo`, then
  `git checkout HEAD -- nba/player_box/parquet/player_box_<yr>.parquet nba/team_box/... nba/pbp/... nba/rosters/parquet/rosters_<yr>.parquet nba/betting_lines/closing_lines_odds_api.parquet`
  (season label = ending year; 2026-27 = 2027). `pip install pyarrow --break-system-packages`.

## Workflow (in this order)
1. **Lines & pace from Outlier** (built-in browser, Deon logs in himself; never touch tokens/credentials).
   - Games page: ML, spread, total + odds. Match Details -> Matchup: Team Rankings incl. **Pace Factor** (swap arrows for the other side), expected lineups, injuries, public betting %.
   - Player props: `.../NBA/games/<id>?marketType=PLAYER_PROP&marketGroup=OFFENSIVE_PROPS | GENERAL_PROPS | DEFENSIVE_PROPS | FIRST_PROPS`. Expand cards with an in-page click script and parse the alt ladder; main line = pair with Over/Under odds closest to even. Whole-number lines at -119/-119 are the PrizePicks lines. Pages load slowly: poll until buttons exist before parsing.
2. **Status check** – injuries/questionables from Outlier + news search. A player with live prop lines is expected to play.
3. **Minutes** – set every rotation player's expected minutes by hand (recent games, injuries, new teams). Early season this is the biggest input; flag players on new teams.
4. **Run the slate** – market mode (sim anchored to spread/total) for props; model mode for sides/totals.
5. **Edge calls** – props: More if P(over) >= 0.58 and P(over) - market no-vig >= +0.06; Less mirror. Otherwise Pass. Treat edges > 20 pts as a red flag (check minutes/injury/role first), not a lock.
   Sides: ALWAYS show a 'Model leans' block on every card (Deon wants it, even when not recommended): model spread/win%/cover% vs market, labeled Strong / Lean / No lean (Strong = cover or win prob 8+ pts off market). Tag them as leans, not recommendations, until the graded side log proves out. Backtest context: market beat model (backtest: market MAE 11.4 vs model 12.4). Totals: model lean side went 140-111 last season (49-35 at 5+ pts) – lean only, small size.
5b. **Potential assists / rebound chances (Outlier)** – open a player's prop detail (game page -> Player props -> expand card -> click any Over/Under line). 'Supporting Stats' shows **Potential Ast** (assists card) or **Reb Chances** + O/D split (rebounds card), plus Minutes; the split chips (L5/L10/L20/H2H/2026/2025) change them, URL `split=prevSeason|l10`. Put them in the slate config `tracking` block (min, pot_ast, ast, reb_ch, reb). Main use: spot hot/cold streaks driven by conversion luck (e.g. Towns L10 3.8 ast on 4.8 potential = 79% conversion vs 61% season -> trust ~3.0). Play-by-play chance proxies were tested and added nothing (OPP_MODE off).
6. **First basket** – compare model P to book no-vig (normalize the starters' implied probs); positive EV = P x payout - (1-P).
7. **Final card** – one list, best first, every prop labeled More / Less / Pass with probability and market %.
8. **Grade** after the game – append to the graded log (date, game, player, stat, line, call, model P, market P, actual, result). Track hit rate on qualifying calls, Brier once ~50 calls.

## Deon's apps (Texas: no legal sportsbooks)
- PrizePicks, Underdog, Courtside, Fliff, Chalkboard, Kalshi (uses Kalshi for book-style props/moneylines).
- Many of our best calls are sportsbook-only lines (not on PrizePicks, e.g. LeBron AST U7.5, Murray AST U6.5). Every card must tag each pick with WHERE it can be played: PP / Underdog / Kalshi. Every card: show best app + line per pick next to model %.
- PrizePicks = juiced Unders/goblins (flat payout). Underdog/Chalkboard/Courtside = better half-point lines. Fliff: Deon dislikes its prices (usually shorter than books) - do NOT price off Fliff. First basket, sides and totals: price vs best sportsbook odds on Outlier, as on 10/21.

## Full-slate workflow (learned 10/21/26, 11 games)
- `auto_minutes.py DATE` builds default rotations (full last-season minutes, 37 cap, rookies flagged); put Outs in `slate/DATE_out.json` (CBS injuries page works via WebFetch; ESPN doesn't).
- Outlier scraping at scale: inject the scraper once into `localStorage['__code']` and `eval` it after each page load; results accumulate in `localStorage['__nba<date>']`. Switch prop groups via the dropdown (find 'Offensive'/'General' ref, click, find option, click) instead of reloading - full page loads take 60-90 s. Keep each browser_batch under ~30 s or the laptop link drops. Export with a compact `game|player|STAT|line|o|u` CSV.
- `slate1021.py DATE DIR [--blend]`: rotation players with NO props who are on the injury list (or 27+ min) are treated as OUT; prop players missing from rotations are added at last-season minutes. Pass 1 -> derive market-implied minutes from each player's PRA (else PTS) line -> `--blend` reruns with 50/50 model/market minutes. Card only takes props with |implied - model minutes| <= 4, not new team, 60+ career games, no Unders on teams missing a 21+ min player, best prop per player.


## 10/21/26 results (11 games)
- Card 19-14-1; 70%+ tier 8-2 (two-night 70%+: 23-8). Sides leans 5-1, totals leans 2-1 (two nights 4-1).
- First FG value list 1/7 (P.J. Washington +1000 hit = +4u flat); flagged Ty Jerome +650 also hit.
- DAL@HOU deep dive went 2-4: HOU starters played 30-37 min in an 18-pt win (Durant 37, Jabari 36). Lesson: when the line implies MORE minutes than the model (gap > +2) for a heavy favorite's starters, do NOT trust the Unders - the market minutes were right. PrizePicks goblins 7/7, demons 2/4.
- Box scores: when hoopR lags, open https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=YYYYMMDD in the laptop browser and fetch /summary?event=ID same-origin (WebFetch/shell get stale or blocked copies).

## 10/22/26 results (2 games)
- Card 5-1-1 (LeBron AST U, Murray AST U, Jokic AST U10, LeBron PTS O, Brown PRA O won; Embiid REB O lost; JDub REB 5 push). Goblins 6/6.
- Sides 0-2 (CLE +2.5, DEN +8.5, DEN ML lost); totals Unders 2-0 (220, 180) -> totals leans now 6-1 over three nights.
- Mistake: overrode the model's Jokic AST Under using last-season history (10.6 apg) -> he had 5. Don't override the model mid-day on one-player history; flag it and let the model call stand.
- Deon's mixed NFL/NBA 5-leg (JJ U3.5 tkl, Maye U29.5 rush, Caleb U0.5 INT, LeBron AST U7.5, Jokic RA U22.5) went 5/5; I had graded JJ/Jokic as passes.

## Engine notes / calibration (2025-26 backtest, 253 games, 5.4k player-games)
- Score: margin SD 13.7 / total SD 18.2 vs real 13.7 / 18.0 around closing lines (PACE_SD 0.02, COMP 0.14 Q4 compression, MARGIN_INFLATE 1.25).
- Player dist: DIR_CONC 120, MIN_SD_SCALE 0.75 -> points 80% band covers 82%, 50% band 50.5%.
- Minutes are mean-preserving in blowouts (history already contains them); bench absorbs remaining minutes.
- First FG: tip-winning team makes the first FG ~64%; player share shrunk toward starter FGA share (12 pseudo-games).

## Lessons (keep applying)
- Tier bias fix (10/19/26): mean-preserving blowout minutes + RATE_K 60 + USAGE_POW 1.1 took stars' over-the-median rate from 73% to 57% and cut MAE on every stat. Re-check tier bias after any engine change.
- Opening night: the model runs on last season's roles. When a gap is explained by a role/minutes change (new team, 2nd-year jump, bench guy), Pass – keep only gaps that survive a sane minutes assumption.
- Calls on the very first slate came out heavily Under; prop Overs are shaded up by books, so mean edge ~ -4.5 pts of probability is normal, but 100+ qualifying calls means thresholds are too loose for early season: use P >= 0.62 / <= 0.38 and |edge| >= 0.10 until ~10 games in.
- New superteams (PHI: Maxey/Brown/LeBron/Embiid) – usage shares compress; market already prices this, so require extra margin on stars' Overs.
- First-basket log 10/20/26: BOS@DET John Collins +900 (model 4th, 9.8%); PHI@NYK Tyrese Maxey (model #2, 12.7%; odds not captured); OKC@SAS Devin Vassell +800 (model value pick, 12.7% vs 9.2% no-vig, +$0.15/$1) - HIT. Value picks 1-for-2 (George miss, Vassell hit).
- Opening night full grade (3 games): qualifying calls 32-24 (57%); by model confidence 70%+ = 15-6, 65-70% = 9-12, 62-65% = 8-6. Lean on 70%+ calls until the log says otherwise. Bench scorers with uncertain minutes (Jared McCain 20 pts in 22 min) burned Unders - same new-role rule.
- Flex 6-leg 10/20/26: 4/6 (Tatum RA +0.5, Wembanyama BLK 6 missed).
- Totals 10/20/26: PHI/NYK Under 232.5 won (206), OKC/SAS Under 231.5 won (220); BOS/DET weak Under passed (234).
- Sides log: 10/20/26 NYK -4.5 lean lost (PHI won 106-100); SAS no lean (OKC won 116-104).
- Sides log: 10/20/26 DET +1.5 / ML +110 (model 64% win) won 121-113 – flagged as lean.
- Opener 10/20/26 BOS@DET graded: qualifying prop calls 15-13; model Brier 0.245 vs market 0.248 on all 119 props. Losses came from new roles the model couldn't see: Tatum 11 AST in 38 min with Jaylen Brown gone (model 5.1), Ausar Thompson 11 REB/5 AST in 33 min. Early season: pass on Unders for a player whose team lost a primary creator/rebounder, until ~5 games show his new usage.
- STL/BLK went over more than the model expected on night 1 (STL overs 50% vs model 38%) - watch this, don't adjust on one game.
- Outlier pace is last season's until ~10 games in; blend with the model's possessions.

## Communication
- Plain language, tables for boards, final card at the end, sources listed.
- Don't flip-flop silently: if a call changes, say from what to what and why.
- PrizePicks: Flex allows one miss; goblins/demons alter lines; same-game correlated legs lower payout.

## Code (save each block to ~/nba)

### nba_sim.py
```python
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
```

### first_basket.py
```python
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
```

### slate.py
```python
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
        sides = {}
        for side in ('home', 'away'):
            code = g[side]; mins = g['minutes'][side]
            pids = [name2pid[n] for n in mins]
            sides[side] = S.build_side(p, t, code, asof, lg, pri, players=pids, minutes=mins)
        H, A = sides['home'], sides['away']
        # model-only numbers (for spread/total/ML edges) and market-anchored run (for props)
        Gm = S.Game(H, A, lg, np.random.default_rng(1)); scm, _ = Gm.run(N)
        Gk = S.Game(S.build_side(p, t, g['home'], asof, lg, pri, players=[name2pid[n] for n in g['minutes']['home']], minutes=g['minutes']['home']),
                    S.build_side(p, t, g['away'], asof, lg, pri, players=[name2pid[n] for n in g['minutes']['away']], minutes=g['minutes']['away']),
                    lg, np.random.default_rng(2))
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
```

## 10/23 results (12 games)
- Clean Unders 4-6 (LaVine REB, Kuzma RA, Morant RA, Tatum RA by 0.5, D.Robinson STL, Hunter RA lost). Common cause: actual minutes 4-8 above model even with small gaps (LaVine 39 vs 31, Kuzma 30 vs 22). Early-season rotations still expanding for starters -> haircut Under confidence ~5 pts until ~10 games in.
- Goblins 7-0 (now 13-0 over two nights). Demons 1-1.
- Totals leans 3-0 (9-1 over four nights); most games went well UNDER the market — don't keep adding +4 to model totals blindly.
- Sides 3-2 (SAC+8.5, LAC+8.5, HOU+5.5 won; CHA+2.5, GS-3.5 lost).
- First basket: Sengun +775 hit from value list (1/11). Utah's unlisted 5th starter (Ace Bailey) scored first — when the book lists only 4 starters, the 5th is a live longshot.
- Morant new-team AST share was underrated (8 and 7 ast); model's "new team" assist cut too aggressive for primary ball handlers.
- Drummond played 7 min — backup-C demons are pure minutes risk.

## 10/24 results (8 games)
- Standard 4-6: STL/BLK picks 2-4 (Maxey Stl+Blk O, MPJ STL U, Sarr BLK U, K.George STL O lost). Defensive standard lines are coin flips - don't build the card's top on them.
- Goblins 9-1 (first goblin loss: Maxey STL 0.5). Demons 2-2.
- Sportsbook ALT ladders (Deon asked for better payouts than goblins): 10-4, about +9u flat. Workflow: pull the raw Outlier ladder (__raw1024), price every Over x.5 with numeric odds vs sim P, show 60%+ at plus-money and a swing tier. Keep doing this.
- Sides leans 4-1 (MIL+12.5, NO+11.5, GS+9.5, CHA+3.5 won; DAL+14.5 lost by 1.5 after Kyrie ruled out late). Totals 0-1 (MIL/PHI U234.5 -> 243); 5 of 8 games went over - Saturday ran high; totals now 9-2.
- First basket value list 0-for-11.
- Kalshi: Deon's combo leg showed "SA win by over 14.5" (Yes) though he says he tapped No on 15.5 - always have him check the Yes/No label on each leg before confirming.
- Late injury news (Kyrie out at 5:25) - the model barely moved the line (7.8 -> 8.3): it underweights star absences. When a star is ruled out late, trust the market move over the model.

## 10/25 results (7 games)
- Standard 5-4, goblins 8-2 (MPJ R+A 5.5 got 0 in a 27-pt blowout; Chet P+R 14 vs 15.5), demons 2-1, alts 5-4 (+1u; SGA alts 3/3, Hunter alts 0/2).
- Totals 2-0 (MEM/SAC O234.5 hit by 0.5 at 235; TOR/MIN U). Totals now 11-2. Sides 1-2 (DET -1.5 won; SAC +3.5, BKN +7.5 lost). The LAC +16.5 I told Deon to skip would have covered (OKC by 7).
- MISTAKE (2nd time, after Jokic 10/22): overrode the model on LeBron with game history - model said AST U6.5 / RA U14.5, I pushed REB O4.5 / RA O10.5 goblins; he had 5 AST, 2 REB. Rule: when I disagree with the model, present the model's call AND my reason, don't recommend the opposite side.
- First basket value list 0-for-9 (season 3-for-40, about -12u). Stop leading with first-basket value picks; offer them only on request.

## 10/26 results
- Card (standard/book): 4-4-1 (Holmgren DNP, Nembhard DNP = void). Sheppard AST Less lost after he moved to bench (lines pulled/reset) — when PP pulls a line pre-tip, assume role change and drop the pick.
- Goblins: 27-7. Losses: two early exits (Markkanen 6 min, JJJ 10 min), Larsson/Davion Mitchell 0 REB, Booker 3-pt night, Bam, Champagnie (4 min). Low-minute bench goblins (Champagnie) are risky.
- Late leans 5-3-1: Braun AST Less, VanVleet AST Less (with minutes-adjusted read), Curry RA Less, KD PTS Less won; Draymond AST Less lost (starting = playmaker in no-Butler lineup), Boozer REB More lost.
- Full game 3-4: IND/MIL Under 238.5 W (212), MIL +4.5 W, GS +7.5 W; MEM/UTAH Over 237.5 L (215 — model 251 badly high), CHI +14.5 L (lost by 35), ATL@HOU Under 229.5 L (230), GS/DEN Under 236.5 L (248).
- Lesson: big model-vs-market total gaps (MEM/UTAH +13.5) were wrong; cap trust when gap > 8 early season.
- Box scores before hoopR updates (~noon CT): in the laptop browser navigate to site.api.espn.com, fetch `/apis/site/v2/sports/basketball/nba/summary?event=<espn game_id>` for each game (ids from nba_schedule_2027.parquet), return compact `TEAM|Player|min,pts,fg,3p,ft,reb,ast,to,stl,blk,...` with a marker (BOX26) and parse from the transcript. Injuries: same origin, `/apis/site/v2/sports/basketball/nba/injuries` (CBS WebFetch now blocked).

## 10/27 slate (4 games) built 10:45 CT from Outlier (OFF+GEN only), rot_blend 0.6, outs from ESPN injuries.

## 10/27 results (4 games)
- Card: 3-3-1 (Brunson AST More 5.5 W, LaVine AST More 2.5 W, Sharpe REB Less 8 W; Tatum AST Less 7 L (OT, 42 min, 8 ast), Sabonis REB Less 13 L (14), Brunson RA More 9 L (8); Hart AST 4 push).
- Alts 1-7 (only Brunson AST O6.5 +145 hit; LaVine O3.5, Brunson O7.5, Hart O4.5 all missed by 1). Leans 4-2 (Tatum 1H FS More 23.5 W 27.4, Tatum PTS More 26.5 W 40, Luka REB Less 7.5 W; Camara PTS Less L, Sabonis RA Less 19 L).
- Full game 0-5: DET +4.5 L (lost by 14), BKN/BOS Under L (OT 249), SAC +18.5 L (by 27), POR/LAL Under 233.5 L (265), LAL -1.5 L. Model badly underrated SA again and both 8+ total gaps lost -> STOP recommending totals when model-market gap > 6; spreads with 6+ gap = pass.
- First basket: Reaves +700 HIT (Morant miss) -> +6u on 2 units.
- Deon's PrizePicks history 10/7-10/27 mostly losses on 4-6 pick power/flex with mixed sports; recommend 2-picks, flat small stakes, budget. Don't push volume.
## Calibration (47 graded standard calls with model_p): shrink k = 0.61 -> show p_adj = 0.5 + 0.6*(p-0.5) on every card (68% -> 61%, 64% -> 58%). Goblins calibrated (84% on 85% model). Card bar = p_adj >= 0.58. Unders on stars/bigs (35+ min) need p_adj >= 0.62 (OT/close-game minutes risk).
- 10/28: Three Pointers live in OFFENSIVE group but lazy-load: scroll to bottom (window.scrollTo(0,99999), wait 2s) before __expand. __want regex in localStorage.__code now includes Three Pointers|Offensive Rebounds (Outlier lists no OREB props). DEF group = Blocks, Steals, Steals + Blocks. Priced in slate/1028/extra_props.csv (sim cols fg3m, blk, stl, stocks). New: defense-vs-position (G/F/C) factors for pts/reb/ast in slate/1028/dvp.csv, pts_dvp.csv, ra_dvp.csv (shrink 50%, blend last season + this season w=gm/(gm+10)). Deon asked for points slot per game + 3PM/defense props.

## 10/28 results (12 games)
- Card standard 6-2-1 (KD AST More 4 push at 4); goblins 7-0 + extra goblins 11-0 (18-0); alts 2-2; four-per-game list 31-10 (76%).
- Points slot 8-9: straight PTS 4-8 (Unders lost: McDaniels, PJW, da Silva, Toppin, NAW, OG, Diabate), combos P+A/P+R Unders 4-1. -> Points: prefer combo Unders (P+A, P+R) over straight PTS Unders.
- Matchup (DvP) reb/ast adjustment night 1: picks >=58% before adjustment 29-12-1, after 27-15-4; the 5 picks it dropped all WON, the 9 it added went 3-3-3. -> Do NOT drop picks on DvP alone; use as tiebreaker/display only until ~150 graded.
- 3PM lines 4-3, defense lines 3-5 (LaRavia STL/SB Unders lost, Eason BLK/SB Unders lost). Defense standard lines still weak; goblins fine.
- Full game card 1-3 (+DEN/NO Under alt W): LAC +4.5 L (LAL by 16), OKC -6.5 L (DAL by 24 — OKC missing Chet/JDub/Wallace/Caruso, line moved to -5.5; Deon read DAL right), HOU/MIL U225.5 L (232), UTAH +12.5 W. Lesson: when a team is missing 3+ rotation players and the line moves against the model, pass/side with market.
- Deon's Novig 6-leg props parlay (all model picks) cashed 14.99x; 4-leg full-game (HOU ML, DEN/NO U236.5, UTA +14.5, LAL/LAC U224.5) cashed 9.55x. ~$245 on $20.

## 10/29 results (only MEM@POR carded; laptop online late)
- Goblins 5-0 (Coward RA, Jrue RA, Edey REB, Morant PR 15.5 & REB 1.5); Clingan PR Less 22.5 W (19). Full game: POR -7.5 L, Over 233.5 L (MEM won 124-103, Outlier had MEM ML tagged EV+).
- Deon SGP cashed: Clingan PR <23, Boozer 4+ AST (12), Under 232.5 -> $117 on $25.
- Lessons: missing props != OUT (Boozer had no posted props but played 12 ast) — check ESPN injury feed instead. Outlier EV+ tag on an underdog ML is a signal worth tracking ('EV+ dog' category).
- Line movement rule (Deon 10/30, spreads, totals, moneylines and props): ML = 3+ pts of no-vig win prob. snapshot lines in the morning (gh/line_moves.py snap) and re-check before tip. A move of 1+ pt (0.5 on prop lines under 5) AGAINST the model's side = drop the leg or follow the market if tied to injury news; a move TOWARD the model = keep. Log open vs close on every pick.
