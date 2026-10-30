"""Default rotations for a slate: roster x last-season recency-weighted minutes, scaled to 240.
Usage: python3 auto_minutes.py 2026-10-21 [out.json]   (edit the json by hand for injuries/news)"""
import sys, json
import numpy as np, pandas as pd
import nba_sim as S

TOP_PICKS = {'AJ Dybantsa', 'Darryn Peterson', 'Cameron Boozer', 'Caleb Wilson', 'Keaton Wagler', 'Mikel Brown Jr.',
             'Darius Acuff Jr.', 'Kingston Flemings', 'Morez Johnson Jr.', 'Brayden Burries', 'Nate Ament'}


def team_minutes(p, R, team, asof, pri, injured=()):
    r = R[(R.team_abbreviation == team) & ~R.display_name.isin(injured)]
    rows = []
    for x in r.itertuples():
        h = p[p.pid == x.pid]
        if len(h):
            prof = S.player_profile(p, x.pid, asof, pri)
            last = h[h.season == h.season.max()]
            # full last-season average is steadier than the end-of-season recency weight (tanking, rest, playoffs)
            mu = last['min'].mean() if len(last) >= 15 else prof['mu']
            # starter on last team -> keep; bench guys moving teams lose a bit
            if prof['last_team'] != team and mu < 26:
                mu *= 0.92
            rows.append((x.display_name, mu, len(h), prof['last_team']))
        else:
            rows.append((x.display_name, 24.0 if x.display_name in TOP_PICKS else 6.0, 0, 'ROOKIE'))
    df = pd.DataFrame(rows, columns=['name', 'mu', 'games', 'last_team']).sort_values('mu', ascending=False)
    df = df[df.mu >= 8].head(10).copy()
    for _ in range(20):                              # scale to 240 with a 37-minute cap
        f = 240 / df.mu.sum()
        df['mu'] = np.minimum(df.mu * f, 37.0)
        if abs(df.mu.sum() - 240) < 0.5:
            break
    df['mu'] = df.mu.round(0)
    return df


OUT = set()
try:
    OUT = set(json.load(open(f'slate/{sys.argv[1]}_out.json')))
except Exception:
    pass


if __name__ == '__main__':
    date = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else f'slate/{date}_rotations.json'
    asof = pd.Timestamp(date)
    p, t = S.load((2025, 2026)); pri = S.pos_priors(p)
    R = pd.read_parquet(f'{S.ROOT}/rosters/parquet/rosters_2027.parquet'); R['pid'] = R.athlete_id.astype('int64')
    s = pd.read_parquet(f'{S.ROOT}/schedules/parquet/nba_schedule_2027.parquet')
    g = s[(s.game_date.astype(str) == date) & (s.season_type == 2)]
    res = {}
    for x in g.itertuples():
        for tm in (x.home_abbreviation, x.away_abbreviation):
            df = team_minutes(p, R, tm, asof, pri, injured=OUT)
            res[tm] = {n: float(m) for n, m in zip(df.name, df.mu)}
            print(tm, ' | '.join(f"{n} {int(m)}{'*' if lt != tm else ''}" for n, m, lt in zip(df.name, df.mu, df.last_team)))
    json.dump(res, open(out, 'w'), indent=1)
    print('wrote', out, '(* = new team or rookie)')
