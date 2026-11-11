"""Where is the model wrong?  python3 model_report.py  -> model_report.md   (REPORT ONLY: changes nothing in the model)

Reads graded_log.csv (picks with a model probability) + bet_ledger.csv (prices). Breaks results down by probability
bucket, stat, side, tier, line size, player and price, and says for each split whether the miss is big enough to be
a real pattern or could just be luck (z-score: |z| >= 2 likely real, 1-2 watch, < 1 noise).
Any fix it points at must pass the out-of-sample check (fit on older picks, test on the newest ones) before it goes
into the model - and only with Deon's OK.
"""
import os, math, datetime as dt
import numpy as np, pandas as pd

MIN_N = 8


def md(df):
    if df is None or df.empty: return '_not enough picks yet_'
    h = '| ' + ' | '.join(map(str, df.columns)) + ' |\n|' + '---|' * len(df.columns) + '\n'
    return h + '\n'.join('| ' + ' | '.join('' if v != v else str(v) for v in r) + ' |' for r in df.itertuples(index=False))


def verdict(z):
    a = abs(z)
    if a >= 2: return 'LIKELY REAL ' + ('(model too high)' if z < 0 else '(model too low)')
    if a >= 1: return 'watch ' + ('(running cold)' if z < 0 else '(running hot)')
    return 'noise'


def split(x, key, label=None, min_n=MIN_N, ordered=False):
    rows = []
    for k, g in x.groupby(key, observed=True):
        if len(g) < min_n: continue
        exp, hit = g.p.sum(), g.win.sum(); sd = math.sqrt((g.p * (1 - g.p)).sum()) or 1
        z = (hit - exp) / sd
        rows.append({label or key: k, 'n': len(g), 'model_says': f'{g.p.mean():.1%}', 'actual': f'{g.win.mean():.1%}',
                     'gap': f'{g.win.mean() - g.p.mean():+.1%}', 'z': round(z, 1), 'read': verdict(z)})
    return (pd.DataFrame(rows) if ordered else pd.DataFrame(rows).sort_values('z')) if rows else pd.DataFrame()


def logloss(p, y): p = np.clip(p, 1e-4, 1 - 1e-4); return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def prob(v):  # some 10/28 rows were logged as text like '59%'
    try:
        s = str(v).strip(); return float(s[:-1]) / 100 if s.endswith('%') else float(s)
    except ValueError: return float('nan')


def main():
    G = pd.read_csv('graded_log.csv'); G['model_p'] = G.model_p.map(prob)
    x = G[G.model_p.notna() & G.result.isin(['Win', 'Loss'])].copy()
    x['p'] = x.model_p; x['win'] = (x.result == 'Win').astype(int); x['side'] = x.call
    x['date'] = x.date.astype(str)
    x['bucket'] = pd.cut(x.p, [0, .55, .60, .65, .70, .80, 1.0], labels=['<55%', '55-60%', '60-65%', '65-70%', '70-80%', '80%+'])
    x['line_size'] = pd.cut(x.line.astype(float), [-1, 2.5, 6.5, 15.5, 999], labels=['0.5-2.5', '3-6.5', '7-15.5', '16+'])
    x['stat_side'] = x.stat + ' ' + x.side
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=-6))).strftime('%Y-%m-%d %H:%M')
    exp, hit = x.p.sum(), x.win.sum(); z = (hit - exp) / math.sqrt((x.p * (1 - x.p)).sum())
    o = [f'# Model error report\n\n_Updated {now} CT. {len(x)} graded picks with a model probability '
         f'({x.date.min()} to {x.date.max()}). Report only: nothing here changes the model._\n',
         f'**Overall:** model said {x.p.mean():.1%}, picks hit {x.win.mean():.1%} '
         f'({int(hit)}-{len(x) - int(hit)}). z = {z:+.1f} -> {verdict(z)}.\n',
         '_How to read: `gap` = actual minus what the model said. `z` says whether the gap is bigger than luck would '
         'explain for that many picks. Only LIKELY REAL rows are worth acting on, and only after the out-of-sample check._\n']

    o.append('## 1. Calibration (is a 65% pick really 65%?)\n\n' + md(split(x, 'bucket', 'model p', 1, ordered=True)) + '\n')
    for key, title in (('stat', '2. By stat'), ('side', '3. Over vs Under'), ('stat_side', '4. Stat + side'),
                       ('tier', '5. By tier'), ('line_size', '6. By line size')):
        o.append(f'## {title}\n\n' + md(split(x, key)) + '\n')

    # projection bias: projected mean vs actual (all logged rows with a mean)
    m = G[G['mean'].notna() & G.actual.notna()].copy()
    rows = []
    for s, g in m.groupby('stat'):
        if len(g) < MIN_N: continue
        err = g.actual - g['mean']; se = err.std(ddof=1) / math.sqrt(len(g)) if len(g) > 1 else 1
        t = err.mean() / se if se else 0
        rows.append(dict(stat=s, n=len(g), avg_projection=round(g['mean'].mean(), 2), avg_actual=round(g.actual.mean(), 2),
                         miss=f'{err.mean():+.2f}', beat_projection=f'{(err > 0).mean():.0%}', z=round(t, 1),
                         read=('LIKELY REAL ' if abs(t) >= 2 else 'watch ' if abs(t) >= 1 else 'noise') +
                              ('' if abs(t) < 1 else '(projects too low)' if t > 0 else '(projects too high)')))
    o.append('## 7. Projection bias (projected mean vs what happened)\n\n'
             '_Positive miss = players beat the projection (model too low). Only players the model picked, so this '
             'leans toward whatever side the card favours._\n\n' + md(pd.DataFrame(rows)) + '\n')

    # price check: did the card pay too much juice?
    if os.path.exists('bet_ledger.csv'):
        L = pd.read_csv('bet_ledger.csv')
        b = L[(L.price_src == 'book') & L.result.isin(['Win', 'Loss'])].copy()
        if len(b):
            imp = lambda a: -a / (-a + 100) if a < 0 else 100 / (a + 100)
            b['breakeven'] = b.price.map(imp)
            b['model_ev'] = b.model_p * b.price.map(lambda a: a / 100 if a > 0 else 100 / -a) - (1 - b.model_p)
            neg = b[b.model_ev < 0]
            o.append('## 8. Price check (card picks with a real book price)\n\n'
                     f'- {len(b)} priced picks: hit {(b.result == "Win").mean():.1%} vs average break-even '
                     f'{b.breakeven.mean():.1%} (average price {b.price.mean():+.0f}).\n'
                     f'- Model\'s own EV was **negative at the posted price on {len(neg)} of {len(b)}** '
                     f'(those went {(neg.result == "Win").sum()}-{(neg.result == "Loss").sum()}, '
                     f'{neg.units.sum():+.2f}u). The card ranks by chance, not price, so heavy-juice Unders '
                     '(e.g. 3PM Unders at -180 to -240) make the card even when the price eats the edge.\n'
                     f'- Picks the model rated +EV at the price went {(b[b.model_ev >= 0].result == "Win").sum()}-'
                     f'{(b[b.model_ev >= 0].result == "Loss").sum()}, {b[b.model_ev >= 0].units.sum():+.2f}u.\n')

    # players picked often
    pl = split(x, 'player', min_n=4)
    o.append('## 9. Players picked 4+ times\n\n_Small samples: treat as a heads-up, not a rule._\n\n' + md(pl) + '\n')

    # out-of-sample: would a different calibration shrink have helped on picks it never saw?
    x = x.sort_values('date'); cut = int(len(x) * 0.7)
    tr, te = x.iloc[:cut], x.iloc[cut:]
    if len(te) >= 20:
        grid = np.round(np.arange(0.3, 1.31, 0.05), 2)
        s = grid[int(np.argmin([logloss(0.5 + k * (tr.p - 0.5), tr.win) for k in grid]))]
        base, new = logloss(te.p, te.win), logloss(0.5 + s * (te.p - 0.5), te.win)
        better = new < base - 0.005
        o.append('## 10. Out-of-sample check (calibration)\n\n'
                 f'Fit on the oldest {len(tr)} picks ({tr.date.min()} to {tr.date.max()}), tested on the newest {len(te)} '
                 f'({te.date.min()} to {te.date.max()}) that the fit never saw.\n\n'
                 f'- Best extra shrink on the old picks: x{s} (1.0 = keep the current probabilities).\n'
                 f'- Log loss on the new picks: current {base:.4f}, with x{s}: {new:.4f} (lower is better).\n'
                 f'- **{"Passes: worth proposing to Deon" if better and s != 1 else "Does not pass: keep the current calibration"}.**\n')
    o.append('## Rules\n\n- This report never changes the model. A change needs (1) a LIKELY REAL pattern, (2) a fix that '
             'holds up out-of-sample on picks it was not fit on, and (3) Deon\'s approval.\n'
             '- Re-check after ~50 more graded picks; patterns under ~30 picks are usually noise.\n')
    open('model_report.md', 'w').write('\n'.join(o))
    print('\n'.join(o[:2]))


if __name__ == '__main__':
    main()
