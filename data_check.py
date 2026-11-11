"""Stale-data check, run by run_day.py before the card is built.   python3 data_check.py 2026-11-10 [--injury-failed]

Checks: hoopR box scores caught up to the last game day, ESPN injury feed loaded, lines are for this date and were
pulled recently, props file not empty. Problems go to slate/MMDD/data_warnings.txt (shown with the card), print as a
loud banner and are emailed once (alerts_out.txt -> GitHub issue). Same warnings are not re-sent on every rebuild.
Default is warn-and-continue. Set STRICT_DATA=1 to stop the build instead when box scores are 2+ game days behind.
Never changes any projection.
"""
import sys, os, glob, json, datetime as dt
import pandas as pd

CT = dt.timezone(dt.timedelta(hours=-6))


def check(DATE, injury_ok=True):
    D = f'slate/{DATE[5:7]}{DATE[8:10]}'
    day = dt.date.fromisoformat(DATE); now = dt.datetime.now(CT)
    warn, hard = [], False
    data = os.environ.get('NBA_DATA', 'repo/nba')
    # 1. box scores
    try:
        yr = day.year + 1 if day.month >= 8 else day.year
        b = pd.read_parquet(f'{data}/player_box/parquet/player_box_{yr}.parquet', columns=['game_date'])
        last_box = pd.to_datetime(b.game_date).max().date()
        s = pd.read_parquet(f'{data}/schedules/parquet/nba_schedule_{yr}.parquet', columns=['game_date'])
        days = sorted({d for d in pd.to_datetime(s.game_date).dt.date if d < day})
        missing = [d for d in days if d > last_box]
        if missing:
            msg = (f'Box scores are {len(missing)} game day(s) behind (hoopR last has {last_box}, missing '
                   f'{", ".join(map(str, missing[-3:]))}). Minutes, rotations and recent form use old games.')
            warn.append(msg); hard = len(missing) >= 2
    except Exception as e:
        warn.append(f'Could not read hoopR box scores/schedule ({e}).'); hard = True
    # 2. injuries
    if not injury_ok:
        warn.append('ESPN injury feed failed: OUT/questionable list is from the last good pull (or empty). Check injuries by hand.')
    # 3. lines
    try:
        g = json.load(open(f'{D}/lines.json'))['games']
        dates = {dt.datetime.fromisoformat(x['commence'].replace('Z', '+00:00')).astimezone(CT).date() for x in g}
        if day not in dates: warn.append(f'lines.json games are for {sorted(map(str, dates))}, not {DATE}.')
    except Exception as e:
        warn.append(f'lines.json unreadable ({e}).')
    raws = sorted(glob.glob(f'{D}/odds_raw_*.json'))
    if raws and day == now.date():
        hhmm = raws[-1][-9:-5]
        pulled = dt.datetime.combine(day, dt.time(int(hhmm[:2]), int(hhmm[2:])), CT)
        age = (now - pulled).total_seconds() / 3600
        if age > 5: warn.append(f'Lines were last pulled at {pulled:%I:%M %p} CT ({age:.0f}h ago). Prices may have moved.')
    p = f'{D}/props_p1.txt'
    if not os.path.exists(p) or not open(p).read().strip():
        warn.append('No player props for this slate (props_p1.txt missing/empty): card will have no props.')
    return warn, hard, D


def report(DATE, injury_ok=True):
    warn, hard, D = check(DATE, injury_ok)
    f = f'{D}/data_warnings.txt'
    old = open(f).read() if os.path.exists(f) else ''
    txt = ''.join(f'- {w}\n' for w in warn)
    if warn:
        print('\n' + '!' * 70 + '\nDATA WARNING - check before betting this card:\n' + txt + '!' * 70 + '\n')
        if txt != old: open('alerts_out.txt', 'a').write(f'Stale data on the {DATE} card\n{txt}\n')
    else:
        print('data check: all fresh')
    open(f, 'w').write(txt)
    if hard and os.environ.get('STRICT_DATA') == '1':
        sys.exit('STRICT_DATA=1 and box scores are 2+ game days behind: card NOT built.')
    return warn


if __name__ == '__main__':
    report(sys.argv[1], '--injury-failed' not in sys.argv)
