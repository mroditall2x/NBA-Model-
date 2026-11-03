"""python3 pick_status.py slate/MMDD
Re-checks every EARLY-card pick (card_early.csv, posted at the morning build) against the current board:
  Hold  = still clears the 58% bar at today's line
  Lean  = 54-57.9% now (smaller stake)
  Drop  = under 54%, or a status change for that team in today's injury alerts and the model no longer likes it
Line moves: 'toward' = the market moved our way (posted bettors hold a better number), 'against' = it moved the other way.
Writes early_status.csv; pushes a 'pick pulled' alert (ntfy) for any newly dropped pick. Dropped picks still get graded."""
import sys, os, json, urllib.request, pandas as pd
D = sys.argv[1]
if not os.path.exists(f'{D}/card_early.csv'): sys.exit('no early card')
E = pd.read_csv(f'{D}/card_early.csv'); B = pd.read_csv(f'{D}/board_all.csv')
B = B[B.type.isin(['PP standard', 'book line'])].copy(); B['adj'] = 0.5 + 0.6 * (B.model - 0.5)
alerts = open(f'{D}/injury_alerts.log').read() if os.path.exists(f'{D}/injury_alerts.log') else ''
prev = pd.read_csv(f'{D}/early_status.csv') if os.path.exists(f'{D}/early_status.csv') else None
rows = []
for r in E.itertuples():
    m = B[(B.player == r.player) & (B.stat == r.stat)]
    if m.empty: rows.append(dict(r._asdict(), line_now=None, p_now=None, move='', status='Hold (no current line)')); continue
    m = m.iloc[(m.line - r.line).abs().argsort()[:1]].iloc[0]
    p_now = m.adj if m.side == r.side else 1 - m.adj          # board may price the other side at the new line
    mv = m.line - r.line; t = 0.5 if r.line < 5 else 1.0
    move = '' if abs(mv) < t else ('toward' if (mv > 0) == (r.side == 'More') else 'against')
    news = f"{r.team}:" in alerts
    st = 'Hold' if p_now >= 0.58 else 'Lean' if p_now >= 0.54 else 'Drop'
    rows.append(dict(game=r.game, team=r.team, player=r.player, stat=r.stat, side=r.side, line=r.line, p=r.p, where=r.where,
                     line_now=m.line, p_now=round(p_now, 3), move=move, news=news, status=st))
S = pd.DataFrame(rows); S.to_csv(f'{D}/early_status.csv', index=False)
print(S[['player', 'stat', 'side', 'line', 'line_now', 'p', 'p_now', 'move', 'status']].to_string(index=False))
was = set() if prev is None else set(prev[prev.status == 'Drop'].player + prev[prev.status == 'Drop'].stat)
new_drops = S[(S.status == 'Drop') & ~(S.player + S.stat).isin(was)]
if len(new_drops):
    open('alerts_out.txt', 'a').write('## Early pick pulled\n' + '\n'.join(f"- {x.player} {'Over' if x.side=='More' else 'Under'} {x.line} {x.stat}: now {x.p_now:.0%} at {x.line_now}" + (' (injury news)' if x.news else '') for x in new_drops.itertuples()) + '\nIf you already bet it: hold or hedge.\n\n')
topic = os.environ.get('NTFY_TOPIC')
if len(new_drops) and topic:
    msg = 'Early pick pulled:\n' + '\n'.join(f"{x.player} {'O' if x.side=='More' else 'U'}{x.line} {x.stat} -> now {x.p_now:.0%} at {x.line_now}"
                                              + (' (injury news)' if x.news else '') + '. If you already bet it: hold or hedge.' for x in new_drops.itertuples())
    try: urllib.request.urlopen(urllib.request.Request(f'https://ntfy.sh/{topic}', data=msg.encode(), headers={'Title': 'NBA pick pulled', 'Tags': 'warning'}), timeout=20)
    except Exception as e: print('push failed', e)
