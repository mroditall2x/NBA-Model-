import pandas as pd, json, sys
sys.path.insert(0,'.'); from slate_names import norm
R=sys.argv[1]
q=pd.read_parquet('/home/claude/nba/repo/nba/player_box/parquet/player_box_2027.parquet'); q['d']=q.game_date.astype(str).str[:10]
q['min']=pd.to_numeric(q.minutes,errors='coerce').fillna(0); q['k']=q.athlete_display_name.map(norm)
DAYS=['10-28','10-30','10-31','11-01','11-02','11-04','11-05','11-06','11-07','11-08']
retset=set()
for d in DAYS:
    j=json.load(open(f'{R}/ret/slate/2026-{d}_returning.json'))
    for tm,rs in j.items():
        for r in rs: retset.add((f'2026-{d}',tm,norm(r['player']),r['normal_min']>=20))
rows=[]
for v in ('base','ret','vA','vC'):
    for d in DAYS:
        D=f'2026-{d}'; rot=json.load(open(f'{R}/{v}/slate/{D}_rotations.json'))
        a=q[q.d==D]
        for tm,mm in rot.items():
            mm={norm(k):x for k,x in mm.items()}
            regs=[k for (dd,t,k,reg) in retset if dd==D and t==tm and reg]
            for r in a[a.team_abbreviation==tm].itertuples():
                if r.min<=0: continue
                grp='returner' if (D,tm,r.k,True) in retset or (D,tm,r.k,False) in retset else ('teammate of returning regular' if regs else 'other')
                rows.append(dict(v=v,d=D,tm=tm,k=r.k,grp=grp,pred=mm.get(r.k,0.0),act=r.min))
X=pd.DataFrame(rows); X['err']=(X.pred-X.act).abs(); X['bias']=X.pred-X.act
print(X.groupby(['grp','v']).agg(n=('err','size'),MAE=('err','mean'),bias=('bias','mean')).round(2))
print(X[(X.grp=='returner')].pivot_table(index=['d','tm','k','act'],columns='v',values='pred').round(1).to_string())
