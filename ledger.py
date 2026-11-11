"""Bet ledger: an append-only record of every card pick, with its price, app, posting time and flat 1-unit result.

  python3 ledger.py stamp slate/MMDD          # run_day.py calls this after each card build: first-seen time + price per pick
  python3 ledger.py add 2026-11-10            # grade_day.py calls this after grading: appends that day's card to bet_ledger.csv
  python3 ledger.py report                    # writes performance.md (record, units, ROI, profit, max drawdown)
  python3 ledger.py backfill                  # one-time: loads graded_log.csv history (marked source=backfill)

Rules (so the record can be trusted):
- Rows are only ever ADDED. A pick already in the ledger is never edited or deleted, even if a re-grade disagrees;
  the disagreement goes to ledger_issues.csv and an email alert instead.
- Every card pick is logged, including losses and DNPs (DNP = void, 0 units).
- Units are flat 1-unit risk. A pick with a real book price uses that price. PrizePicks/DFS lines have no price:
  they are counted at -120 (the ~54.5% DFS break-even already used in SKILL.md) and marked price_src=assumed_dfs.
  Goblins have no fair price at all, so they get a win rate but no units (price_src=none).
"""
import sys, os, datetime as dt
import pandas as pd

LEDGER = 'bet_ledger.csv'
ISSUES = 'ledger_issues.csv'
KEY = ['date', 'game', 'player', 'stat', 'side', 'line']
COLS = KEY + ['team', 'tier', 'top', 'model_p', 'price', 'price_src', 'book', 'posted_at', 'actual', 'result', 'units',
              'source', 'logged_at', 'flag']
DFS_PRICE = -120
CT = dt.timezone(dt.timedelta(hours=-6))


def now(): return dt.datetime.now(CT).strftime('%Y-%m-%d %H:%M')


def payout(a):  # profit on a 1-unit win at American odds a
    return a / 100 if a > 0 else 100 / -a


def price_info(tier, price, where=''):
    if price == price and price is not None and float(price) == DFS_PRICE and 'PrizePicks' in str(where): return float(DFS_PRICE), 'assumed_dfs'
    if price == price and price is not None and abs(float(price)) >= 100: return float(price), 'book'
    if tier == 'standard': return float(DFS_PRICE), 'assumed_dfs'
    return None, 'none'


def units(result, price):
    if price is None or price != price: return None
    return {'Win': round(payout(price), 3), 'Loss': -1.0, 'Push': 0.0, 'DNP': 0.0}.get(result)


def _k(df): return list(zip(*[df[c].astype(str) if c != 'line' else df[c].astype(float).astype(str) for c in KEY]))


def load():
    if os.path.exists(LEDGER): return pd.read_csv(LEDGER)
    return pd.DataFrame(columns=COLS)


def append(rows):
    """Append rows whose key is not in the ledger. Existing rows are never changed; conflicts are reported."""
    L = load()
    if rows.empty: return 0
    rows = rows.copy()
    for c in COLS:
        if c not in rows: rows[c] = ''
    rows = rows[COLS].drop_duplicates(KEY)
    have = dict(zip(_k(L), L.result.astype(str))) if len(L) else {}
    new, issues = [], []
    for k, r in zip(_k(rows), rows.itertuples(index=False)):
        if k in have:
            if have[k] != str(r.result):
                issues.append(dict(zip(KEY, k), ledger_result=have[k], new_result=r.result, seen_at=now()))
            continue
        new.append(r)
    if new:
        N = pd.DataFrame(new, columns=COLS)
        N.to_csv(LEDGER, mode='a', header=not os.path.exists(LEDGER), index=False)
    if issues:
        I = pd.DataFrame(issues)
        I.to_csv(ISSUES, mode='a', header=not os.path.exists(ISSUES), index=False)
        msg = '\n'.join(f"- {i['date']} {i['player']} {i['stat']} {i['side']} {i['line']}: ledger says {i['ledger_result']}, "
                        f"re-grade says {i['new_result']} (ledger NOT changed)" for i in issues)
        open('alerts_out.txt', 'a').write(f"Bet ledger: re-grade disagrees with the logged result\n{msg}\n\n")
        print('LEDGER ISSUES:\n' + msg)
    return len(new)


def stamp(D):
    """Record when each card pick first appeared and the price it was posted at (kept across rebuilds)."""
    if not os.path.exists(f'{D}/card.csv'): return
    C = pd.read_csv(f'{D}/card.csv')
    f = f'{D}/card_stamps.csv'
    S = pd.read_csv(f) if os.path.exists(f) else pd.DataFrame(columns=['game', 'player', 'stat', 'side', 'line', 'first_seen', 'price_first', 'last_seen'])
    t = now()
    k = lambda d: list(zip(d.game, d.player, d.stat, d.side, d.line.astype(float)))
    seen = set(k(S)) if len(S) else set()
    add = C[[x not in seen for x in k(C)]]
    if len(add):
        S = pd.concat([S, pd.DataFrame(dict(game=add.game, player=add.player, stat=add.stat, side=add.side, line=add.line.astype(float),
                                            first_seen=t, price_first=add.price, last_seen=t))])
    cur = set(k(C))
    S.loc[[x in cur for x in k(S)], 'last_seen'] = t
    S.to_csv(f, index=False)


def add(DATE):
    D = f'slate/{DATE[5:7]}{DATE[8:10]}'
    if not os.path.exists(f'{D}/card_graded.csv'): print('no graded card for', DATE); return
    C = pd.read_csv(f'{D}/card_graded.csv')
    if os.path.exists(f'{D}/card_stamps.csv'):
        S = pd.read_csv(f'{D}/card_stamps.csv')[['game', 'player', 'stat', 'side', 'line', 'first_seen']]
        C = C.merge(S.assign(line=S.line.astype(float)), on=['game', 'player', 'stat', 'side', 'line'], how='left')
    else:
        C['first_seen'] = None
    rows = []
    for r in C.itertuples():
        pr, src = price_info(r.tier, getattr(r, 'price', None), getattr(r, 'where', ''))
        flags = []
        if src == 'assumed_dfs': flags.append('no book price - counted at -120 (DFS)')
        if src == 'none': flags.append('no price - win rate only')
        if r.result == 'DNP': flags.append('void (DNP)')
        if not isinstance(r.first_seen, str): flags.append('posting time unknown')
        rows.append(dict(date=DATE, game=r.game, player=r.player, stat=r.stat, side=r.side, line=float(r.line), team=r.team,
                         tier=r.tier, top=getattr(r, 'top', ''), model_p=round(float(r.p), 4), price=pr, price_src=src,
                         book=getattr(r, 'where', ''), posted_at=r.first_seen if isinstance(r.first_seen, str) else '',
                         actual=r.actual, result=r.result, units=units(r.result, pr), source='live', logged_at=now(),
                         flag='; '.join(flags)))
    n = append(pd.DataFrame(rows))
    print(n, 'new picks added to', LEDGER, 'for', DATE)


def backfill():
    """Load graded_log.csv history once. Prices come from card_graded.csv where that day saved them."""
    G = pd.read_csv('graded_log.csv')
    rows = []
    px = {}
    for d in sorted(set(G.date.astype(str))):
        f = f'slate/{d[5:7]}{d[8:10]}/card_graded.csv'
        if os.path.exists(f):
            c = pd.read_csv(f)
            if 'price' in c:
                for r in c.itertuples(): px[(d, r.player, r.stat, r.side, float(r.line))] = (r.price, getattr(r, 'where', ''), getattr(r, 'top', ''))
    for r in G.itertuples():
        d = str(r.date); tier = r.tier if isinstance(r.tier, str) else 'untiered'
        p0, book, top = px.get((d, r.player, r.stat, r.call, float(r.line)), (None, '', ''))
        dfs = tier == 'standard' or str(r.pp_line) == 'True'      # early rows: only flat PrizePicks lines get the DFS price
        pr, src = price_info('standard' if dfs else tier, p0)
        flags = ['backfilled from graded_log', 'posting time unknown']
        if src == 'assumed_dfs': flags.append('no book price - counted at -120 (DFS)')
        if src == 'none': flags.append('no price - win rate only')
        mp = str(r.model_p).strip(); mp = float(mp[:-1]) / 100 if mp.endswith('%') else float(mp) if mp not in ('', 'nan') else None
        if mp is None: flags.append('no model_p (pre-calibration log)')
        rows.append(dict(date=d, game=r.game, player=r.player, stat=r.stat, side=r.call, line=float(r.line), team='', tier=tier,
                         top=top, model_p=mp, price=pr, price_src=src, book=book, posted_at='', actual=r.actual,
                         result=r.result, units=units(r.result, pr), source='backfill', logged_at=now(), flag='; '.join(flags)))
    print(append(pd.DataFrame(rows)), 'history rows added')


def max_drawdown(u):
    c = u.cumsum(); return float((c.cummax().clip(lower=0) - c).max()) if len(c) else 0.0


def summary(x):
    w, l, p = (x.result == 'Win').sum(), (x.result == 'Loss').sum(), (x.result == 'Push').sum()
    v = (x.result == 'DNP').sum()
    u = x[x.units.notna() & (x.result != 'DNP')]
    risked = len(u[u.result != 'Push'])
    prof = u.units.sum()
    return dict(picks=len(x), record=f'{w}-{l}-{p}' + (f' ({v} void)' if v else ''),
                win_pct=f'{w / (w + l):.1%}' if w + l else '-', units=f'{prof:+.2f}',
                roi=f'{prof / risked:+.1%}' if risked else '-', max_dd=f'{max_drawdown(u.units):.2f}u' if len(u) else '-')


def md(df):  # markdown table without extra packages
    if df is None or df.empty: return '_none_'
    h = '| ' + ' | '.join(map(str, df.columns)) + ' |\n|' + '---|' * len(df.columns) + '\n'
    return h + '\n'.join('| ' + ' | '.join('' if v != v else str(v) for v in r) + ' |' for r in df.itertuples(index=False))


def table(df, by):
    rows = [dict({by: k}, **summary(x)) for k, x in df.groupby(by)]
    return md(pd.DataFrame(rows)) if rows else '_none_'


def report():
    L = load()
    if L.empty: print('ledger empty'); return
    L = L.sort_values(['date', 'posted_at', 'logged_at'], na_position='first')
    L['stat_group'] = L.stat.map(lambda s: 'points' if s in ('PTS', 'PA', 'PR', 'PRA') else 'reb/ast' if s in ('REB', 'AST', 'RA') else 'other')
    L['price_basis'] = L.price_src.map({'book': 'real price (book or exchange)', 'assumed_dfs': 'DFS (-120 assumed)', 'none': 'no price (goblin / untagged)'})
    out = [f'# Model performance\n\n_Updated {now()} CT from `bet_ledger.csv`. Flat 1 unit per pick. '
           'Rows are never deleted or edited, losses and voids included._\n']
    for name, x in (('Live (logged at grading, from the day this tracker started)', L[L.source == 'live']),
                    ('History (backfilled from graded_log.csv; posting times and some prices unknown)', L[L.source == 'backfill'])):
        out.append(f'## {name}\n')
        if x.empty: out.append('_No picks yet._\n'); continue
        s = summary(x)
        out.append(f"**{s['record']}**, win rate {s['win_pct']}, **{s['units']} units**, ROI {s['roi']}, max drawdown {s['max_dd']}\n")
        u = x[x.units.notna() & (x.result != 'DNP')]
        if len(u):
            day = u.groupby('date').units.sum().cumsum().round(2)
            out.append('Cumulative units by day: ' + ', '.join(f'{d[5:]} {v:+g}' for d, v in day.items()) + '\n')
        for by, title in (('price_basis', 'By price basis'), ('tier', 'By tier'), ('stat_group', 'By stat group'),
                          ('side', 'Over vs Under'), ('top', 'Top-5 vs rest')):
            out.append(f'### {title}\n\n{table(x, by)}\n')
    out.append('## Notes\n\n- ROI = units won / units risked (pushes and voids not counted as risked).\n'
               '- Max drawdown = biggest drop from a running high in cumulative units.\n'
               '- DFS picks (PrizePicks/Underdog flat lines) have no real price; -120 is the break-even used in SKILL.md. '
               'Judge them by win rate vs 54.5%.\n- Issues (re-grades that disagree with the log) are in `ledger_issues.csv`.\n')
    open('performance.md', 'w').write('\n'.join(out))
    print('\n'.join(out[:4]))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'report'
    if cmd == 'stamp': stamp(sys.argv[2])
    elif cmd == 'add': add(sys.argv[2]); report()
    elif cmd == 'backfill': backfill(); report()
    else: report()
