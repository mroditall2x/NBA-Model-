"""python3 card_diff.py slate/MMDD
Runs after an injury rebuild. Compares the card from before the rebuild (*.prev, saved by injury_watch.py) with the new one
for the games that had a status change and haven't tipped, then pushes the new picks to Deon's phone through ntfy."""
import sys, os, json, urllib.request, pandas as pd
D = sys.argv[1]
if not os.path.exists(f'{D}/watch_changes.json'): sys.exit('no changes file')
W = json.load(open(f'{D}/watch_changes.json'))
def picks(suffix):
    fr = [pd.read_csv(f'{D}/{f}.csv{suffix}') for f in ('card', 'by_team') if os.path.exists(f'{D}/{f}.csv{suffix}') and os.path.getsize(f'{D}/{f}.csv{suffix}') > 5]
    return pd.concat(fr).drop_duplicates(['game', 'player', 'stat', 'side']) if fr else pd.DataFrame(columns=['game', 'player', 'stat', 'side', 'line', 'p', 'where'])
def label(r):
    app = str(r.where).replace('PrizePicks', 'PP').replace('Underdog', 'UD').replace(' / ', '/')
    return f"{r.player} {r.stat} {'O' if r.side == 'More' else 'U'}{r.line:g} {round(r.p * 100)}% ({app})"
def key(x): return set(zip(x.player, x.stat, x.side))
old, new = picks('.prev'), picks('')
G = pd.read_csv(f'{D}/games.csv').set_index('game') if os.path.exists(f'{D}/games.csv') else None
Gp = pd.read_csv(f'{D}/games.csv.prev').set_index('game') if os.path.exists(f'{D}/games.csv.prev') else None
FB = pd.read_csv(f'{D}/fb_priced.csv') if os.path.exists(f'{D}/fb_priced.csv') else None
tag = lambda t, g: '' if t is None or g not in t.index or pd.isna(t.loc[g, 'ev_tag']) else str(t.loc[g, 'ev_tag'])
out = []
for g in W['games']:
    o, n = old[old.game == g], new[new.game == g]
    ko, kn = key(o), key(n)
    why = '; '.join(c['text'] for c in W['changes'] if c['game'] == g)
    fresh = 'lines refreshed' if g in W.get('refreshed', []) else 'same lines' if g not in W.get('capped', []) else 'lines NOT refreshed, daily cap hit'
    b = [f"{g} ({fresh})", why]
    gone = [label(r) for r in o.itertuples() if (r.player, r.stat, r.side) not in kn]
    add = [label(r) for r in n.sort_values('p', ascending=False).itertuples() if (r.player, r.stat, r.side) not in ko]
    keep = [label(r) for r in n.sort_values('p', ascending=False).itertuples() if (r.player, r.stat, r.side) in ko]
    if add: b.append('NEW: ' + ' | '.join(add))
    if gone: b.append('PULLED: ' + ' | '.join(gone))
    if keep: b.append('KEPT: ' + ' | '.join(keep))
    if not (add or gone or keep): b.append('No props on the card for this game.')
    t0, t1 = tag(Gp, g), tag(G, g)
    if t0 != t1: b.append(f"Full game: {t1 or 'EV+ tag removed'}" + (f" (was: {t0})" if t0 else ''))
    if FB is not None and 'ev' in FB:
        f = FB[(FB.game == g) & (FB.ev >= 0.10)].sort_values('ev', ascending=False)
        if len(f): b.append('First basket EV+: ' + ' | '.join(f"{r.player} +{r.book:g} (fair +{r.fair_odds:g})" for r in f.itertuples()))
    out.append('\n'.join(b))
msg = '\n\n'.join(out)[:3800]
print(msg)
topic = os.environ.get('NTFY_TOPIC')
if topic and msg:
    try:
        urllib.request.urlopen(urllib.request.Request(f'https://ntfy.sh/{topic}', data=msg.encode(),
                                                      headers={'Title': 'NBA card updated', 'Tags': 'rotating_light', 'Priority': '4'}), timeout=20)
        print('push sent')
    except Exception as e: print('push failed:', e)
