"""Projected starting lineups (RotoWire) -> slate/MMDD/lineups.json.   python3 lineups.py 2026-11-13
Added 11/13: the model built minutes from season averages only, so a surprise starter looked like a bench player
(Caleb Martin 11/12: model 14 min, started, played 21; all four of his Unders on the card lost).
Output: {TEAM: {"status": "expected"|"confirmed", "starters": [names], "out": [...], "ques": [...], "doubt": [...]}}
TEAM uses the model's ESPN abbreviations. Never fails the run: if the page can't be read or parsed it writes nothing.
Used by run_day.py (RotoWire 'Out' players join the ESPN out list) and card_slate.py (flags)."""
import sys, re, json, html, urllib.request
URL = 'https://www.rotowire.com/basketball/nba-lineups.php'
# RotoWire abbreviation -> ESPN abbreviation used in lines.json / games
AB = {'NYK': 'NY', 'GSW': 'GS', 'SAS': 'SA', 'NOP': 'NO', 'NOR': 'NO', 'UTA': 'UTAH', 'WAS': 'WSH', 'PHO': 'PHX',
      'BRK': 'BKN', 'BRO': 'BKN', 'CHO': 'CHA', 'OKL': 'OKC'}


def parse(page):
    out = {}
    blocks = re.split(r'<div class="lineup is-nba', page)[1:]
    for b in blocks:
        abbrs = re.findall(r'class="lineup__abbr"[^>]*>\s*([A-Z]{2,4})\s*<', b)
        lists = re.split(r'class="lineup__list\s+is-(?:visit|home)', b)[1:]
        if len(abbrs) < 2 or len(lists) < 2: continue
        for ab, part in zip(abbrs[:2], lists[:2]):
            status = 'confirmed' if re.search(r'lineup__status[^"]*is-confirmed', part) else 'expected'
            head, _, mnp = part.partition('MAY NOT PLAY')
            def players(s):
                r = []
                for li in re.findall(r'<li class="lineup__player[^"]*"[^>]*>(.*?)</li>', s, re.S):
                    m = re.search(r'title="([^"]+)"', li) or re.search(r'<a[^>]*>([^<]+)</a>', li)
                    inj = re.search(r'lineup__inj[^>]*>\s*([^<]+?)\s*<', li)
                    if m: r.append((html.unescape(m.group(1)).strip(), inj.group(1).strip() if inj else ''))
                return r
            st = players(head)[:5]
            if len(st) < 5: continue                        # partial block: don't guess
            t = {'status': status, 'starters': [n for n, _ in st], 'out': [], 'ques': [], 'doubt': [], 'prob': []}
            for n, tag in players(mnp) + [p for p in st if p[1]]:
                k = {'OUT': 'out', 'OFS': 'out', 'QUES': 'ques', 'GTD': 'ques', 'DOUBT': 'doubt', 'PROB': 'prob'}.get(tag.upper().rstrip('.'))
                if k and n not in t[k]: t[k].append(n)
            out[AB.get(ab, ab)] = t
    return out


if __name__ == '__main__':
    DATE = sys.argv[1]; D = f'slate/{DATE[5:7]}{DATE[8:10]}'
    try:
        req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
        page = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
    except Exception as e:
        print('lineups: fetch failed:', e); sys.exit(0)
    L = parse(page)
    if not L:
        print('lineups: page read but no lineups parsed (layout change?) - nothing written'); sys.exit(0)
    json.dump(L, open(f'{D}/lineups.json', 'w'), indent=1)
    print(f'lineups: {len(L)} teams', ' '.join(f"{k}:{v['status'][0]}" for k, v in sorted(L.items())))
