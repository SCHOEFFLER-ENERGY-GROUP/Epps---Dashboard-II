import openpyxl, json, collections, re, sys, datetime
X=sys.argv[1]; WEEK=sys.argv[2]; OUT=sys.argv[3]
wb=openpyxl.load_workbook(X,data_only=True)
def sheet(pred): return [ws for ws in wb.worksheets if pred(ws.title)][0]
raw=sheet(lambda t:t.startswith('Raw Data'))
rows=list(raw.iter_rows(values_only=True)); H=list(rows[0])
MS='MAIL_STATUS' if 'MAIL_STATUS' in H else 'MAIL STATUS'
REQ=['TRACT_ID','ASSOCIATEID','LAND_OWNER','NET_AC','NET_MILES','INTEREST','ASSIGNED_TO_OWNER','TRACT_ACRES','SA_EXP_DATE','SA_LEASE_NO','TRACT_STATUS',MS]
miss=[c for c in REQ if c not in H]
if miss: sys.exit('MISSING '+str(miss))
rd=[dict(zip(H,r)) for r in rows[1:] if r[0]]
rd=[r for r in rd if r['INTEREST'] not in (0,None)]   # 0%-interest rows excluded
R2=lambda x:round(x or 0,2)
# Rob_Join hierarchy
rj=list(sheet(lambda t:t=='Rob_Join').iter_rows(values_only=True))
ci=rj[0].index('NEW_STATUS')
hier=[v for v in sorted([r[ci] for r in rj[1:] if r[ci]],key=lambda s:int(s.split('-')[0]))]
HIER=[s.split('-',1)[1] for s in hier]
RANK={s:i for i,s in enumerate(reversed(HIER))}  # MAILED=0 ... ACQUIRED=max
# history
ac=collections.defaultdict(float); lo=collections.defaultdict(set); allids=set()
for r in rd: ac[r[MS]]+=r['NET_AC'] or 0; lo[r[MS]].add(r['ASSOCIATEID']); allids.add(r['ASSOCIATEID'])
unk=set(ac)-set(HIER)
if unk: sys.exit('STATUS NOT IN Rob_Join HIERARCHY: '+str(unk))
hist={'date':WEEK,'totalLandowners':len(allids),'totalAcres':sum(ac.values()),
      'acres':{s:ac[s] for s in HIER if s in ac},'landowners':{s:len(lo[s]) for s in HIER if s in lo}}
# owners
by=collections.OrderedDict()
for r in rd: by.setdefault(r['ASSOCIATEID'],[]).append(r)
def ostatus(rs):
    c=collections.Counter(r[MS] for r in rs); return max(c,key=lambda s:(c[s],-RANK.get(s,0)))
snap=[]
for aid,rs in by.items():
    snap.append({'aid':aid,'name':rs[0]['LAND_OWNER'],'status':ostatus(rs),'acres':R2(sum(r['NET_AC'] or 0 for r in rs)),
                 'tracts':len({r['TRACT_ID'] for r in rs}),'assigned':rs[0]['ASSIGNED_TO_OWNER']})
snap.sort(key=lambda o:-o['acres'])
lodata=[{k:v for k,v in o.items() if k!='aid'} for o in snap]
# notes
def clean(t): return (t or '').replace('%u2019',"'").replace('%u2026','…').replace('\n',' ').strip()
def norm(s): return re.sub(r'[^a-z0-9]','',(s or '').lower())
nws=sheet(lambda t:t.strip().lower()=='notes'); nrows=list(nws.iter_rows(values_only=True))
NH=nrows[0]; notes=[dict(zip(NH,r)) for r in nrows[1:] if r[0]]
def ndt(n):
    t=n['Time'] or datetime.time(0); return datetime.datetime.combine(n['Date'].date(),t)
# details
det={}
for aid,rs in sorted(by.items(),key=lambda kv:kv[1][0]['LAND_OWNER']):
    nm=rs[0]['LAND_OWNER']
    tr=[{'id':r['TRACT_ID'],'status':r[MS],'acres':R2(r['NET_AC']),'miles':round(r['NET_MILES'] or 0,4),'interest':round(r['INTEREST'],6),'gross':R2(r['TRACT_ACRES'])} for r in rs]
    tids={r['TRACT_ID'] for r in rs}; nn=norm(nm)
    cand=[n for n in notes if n['Tract'] in tids and (norm(n['Land Owner'])==nn or (nn[:10] and norm(n['Land Owner'])[:10]==nn[:10]))]
    ln=None
    if cand:
        b=max(cand,key=ndt); ln={'date':f"{b['Date']:%b} {b['Date'].day}, {b['Date'].year}",'text':clean(b['Notes'])}
    det[nm]={'broker':rs[0]['ASSIGNED_TO_OWNER'],'tracts':tr,'lastNote':ln}
# line list
def sa(v):
    if isinstance(v,datetime.datetime): return v.strftime('%Y-%m-%d')
    return v
satr={}
for r in rd: satr.setdefault(r['TRACT_ID'],(sa(r['SA_EXP_DATE']) or '',r['SA_LEASE_NO'] or ''))
llws=sheet(lambda t:t=='Line List'); llr=list(llws.iter_rows(values_only=True)); LH=llr[0]
LL=[]
for r in llr[1:]:
    if not r[0]: continue
    d=dict(zip(LH,r)); s=satr.get(d['TRACT ID'],(None,None))
    LL.append({'tractId':d['TRACT ID'],'saExp':s[0],'saLease':s[1],'landowner':d['LAND OWNER'],'county':d['TRACT COUNTY'],'assigned':d['ASSIGNED TO OWNER'],
      'loStatus':d['LANDOWNER STATUS'],'trStatus':d['TRACT STATUS'],'interest':round(d['INTEREST'] or 0,6),'gross':R2(d['GROSS\nACRES']),'acres':R2(d['NET ACRES']),
      'infra':d['INFRASTRUCTURE\n(Y/N)'],'infraGross':R2(d['INFRASTRUCTURE GROSS $']),'infraNet':R2(d['INFRASTRUCTURE NET $'])})
# IOL
iws=sheet(lambda t:t=='IOL Tracking'); IH=[c.value for c in iws[1]]
col={h:i for i,h in enumerate(IH)}
def up(v): return v.strip().upper() if isinstance(v,str) else ('' if v is None else v)
def num(v,n=2):
    try: return round(float(v),n)
    except: return 0
IOL=[]
for row in iws.iter_rows(min_row=2):
    v=lambda h:row[col[h]].value
    if not v('TractID'): continue
    md=v('Merge/Mailed Date')
    dc=row[col['Delivery Confirmation']]
    IOL.append({'tractId':v('TractID'),'landowner':up(v('Landowner')),'address':up(v('Address')),'city':up(v('City')),'state':up(v('State')),'zip':str(v('Zip')).strip() if v('Zip') is not None else '',
      'county':up(v('TractCounty')),'mailedDate':md.strftime('%Y-%m-%d') if isinstance(md,datetime.datetime) else up(md),
      'deliveryConfirmation':dc.value or '','deliveryUrl':dc.hyperlink.target if dc.hyperlink else '','broker':up(v('Broker')),
      'interest':num(v('Interest'),6),'acres':num(v('Acres')),'netAcres':num(v('Net Acres')),'netFootage':num(v('Net Footage')),'netRods':num(v('Net Rods')),
      'pipeCost':num(v('Pipe Cost (500/rod)')),'iwWellCount':int(num(v('IW Well Count'))),'iwWellCost':num(v('IW Well Cost (1000/well)')),
      'obsWellCount':int(num(v('OBS/DIS Well Count'))),'obsWellCost':num(v('OBS/DIS Well Cost (500/well)')),'rectifierSite':'Y' if str(v('Rectifier Site (Y/N)') or '0').strip() not in ('0','N','') else 'N',
      'rectifierCost':num(v('Rectifier Site Cost (500/site)')),'surfaceSiteCost':num(v('Surface Site Cost (2000/acre)')),'bonusPayment':num(v('Bonus Payment (1000/acre)')),
      'infraTotalCost':num(v('Infrastructure Total Cost')),'totalCost':num(v('Total Cost'))})
# weekly summary: brokerage/bonus
ws=sheet(lambda t:t=='Weekly Summary'); wr=list(ws.iter_rows(values_only=True))
def block(title):
    i=[k for k,r in enumerate(wr) if r[0]==title][0]; out=[]
    for r in wr[i+2:]:
        if not r[0] or r[0]=='Total': break
        out.append(r)
    return out
BRK=[{'name':r[0],'prev':round(r[1],2),'curr':round(r[2],2),'total':round(r[3],2),'budget':r[4]} for r in block('EPPS - Brokerage')]
BON=[{'name':r[0],'prev':round(r[1],2),'curr':round(r[2],2),'total':round(r[3],2)} for r in block('EPPS - Bonus Payments')]
json.dump({'HIER':HIER,'history':hist,'landownerData':lodata,'snap':snap,'details':det,'lineList':LL,'iol':IOL,'brokerage':BRK,'bonus':BON,'MS':MS,'H':H},open(OUT,'w'),default=str)
print('ok',len(snap),len(LL),len(IOL),HIER)
