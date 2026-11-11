"""EPPS notes thematic coding + Notes Analysis tab data. Usage: python3 epps_notes_themes.py "EPPS - Mapper Export - MM.DD.YY.xlsx" [source-name]
Reads Raw Data + Notes tabs, codes each note against the codebook, rolls up by distinct landowner, writes notes_analysis_block.js.
10/14/26: accepts MAIL_STATUS or 'MAIL STATUS'; optional argv[2] overrides the source file name.
11/11/26: added SECOND OFFER LETTER to ORDER; unknown statuses sort as least advanced instead of crashing."""
import sys
import openpyxl,collections,re
wb=openpyxl.load_workbook(sys.argv[1],read_only=True,data_only=True)
raw=list(wb[next(n for n in wb.sheetnames if n.startswith('Raw Data'))].iter_rows(values_only=True)); H=raw[0]; ix={h:i for i,h in enumerate(H)}
rd=[dict(zip(H,r)) for r in raw[1:] if r[0]]
MSCOL='MAIL_STATUS' if 'MAIL_STATUS' in H else 'MAIL STATUS'
def norm(s): return re.sub(r'[^a-z0-9]','',(s or '').lower())
bykey={}
for r in rd: bykey[(r['TRACT_ID'],norm(r['LAND_OWNER']))]=r
notes=[r for r in list(wb[next(n for n in wb.sheetnames if n.strip().lower()=='notes')].iter_rows(values_only=True))[1:] if r[0]]
def clean(t): return (t or '').replace('%u2019',"'").replace('%u2026','…').replace('\n',' ').strip()

import json
CODES=[
# group C = landowner concerns, D = deal dynamics
('price','C','Price pushback or counter','Owner rejects or questions the offer amount, or a counter is made/approved.', r"counter|not satisfied with the offer|not enough money|did not like (the|to) offer|not happy with the offer|not accept our current offer|one time payment"),
('value','C','Valuation support asked','Owner or counsel asks how the price was set: appraisals, comparables, valuation docs, payment breakdowns.', r"appraisal|valuation document|comparable|payment breakdown"),
('surface','C','Surface, depth and scope terms','Concerns about surface use, mineral rights, depth limits, Pugh clause, or what land the agreement covers.', r"surface (rights|language)|no surface|to surface rights|pugh clause|go deeper|depths|item 11|outside of the reservoir|mineral rights"),
('redline','C','Redlines and form edits','Owner/counsel marks up the agreement or asks for an editable Word version.', r"redline|bluelined|marked up|word form|word version|in word|revisions"),
('title','C','Title, heirship and curative','Ownership is unclear or contested: successions, deceased owners, reservations, deeds, usufruct.', r"succession|obituary|deceased|reservation|deed|usufruct|flow of ownership"),
('fol','C','Expropriation / FOL raised','The FOL, expropriation, or "what if we don\'t agree" comes up, or competing offers are mentioned.', r"\bfol\b|expropriation|suit to follow|what happens if we can't agree|other companies contacting"),
('counsel','D','Represented by counsel','An attorney or outside reviewer is involved; contact routes through them.', r"attorney|\bcarroll\b|woltz|ben marshall|veron|hoychick|molly clement|ellington|kevin frederick|doughty|bethard|on behalf of|represent"),
('spokes','D','Family spokesperson / POA','One family member negotiates or decides for others; signing waits on that person.', r"negotiating for her|is negotiating\.|standby on signing until|once mrs\. slaughter|talk to her sisters|her and her siblings|her and her sister|with his family members|with family members|\bpoa\b"),
('collective','D','Cross-owner coordination','Owners (outside the Carroll block) sharing an attorney, following a relative\'s lead, or waiting on a neighbor\'s deal.', r"hoychick|several landowners|handling his tracts the same way|waiting for the poverty point"),
('contact','D','Hard to reach / unavailable','No real conversation yet: bad numbers, unreturned VMs, wrong or empty addresses, owner away.', r"left vm|lvm|left message|l/m|no answer|not in service|wrong number|bad number|no one (came|home|responded)|no house there|no home at that address|could not leave|couldn't leave|unable to leave|disconnected|not accepting calls|hoping that she replies|abandoned|not been able to connect|he is not in|find info on"),
('early','D','Early stage / reviewing','Intro or notification made, or owner has the packet and is still thinking it over or asking general questions.', r"notify her|notified her that the offer|introductory email|discuss further once he received|put me in touch|got the letter|still thinking|meeting tonight to discuss|continue to review|still discussing|not ready to sign|willing to work with us|see if (we could answer|she had) |any more questions|had a few questions"),
('close','D','Signing and closing logistics','Executed agreements, notarization, initials, legal-description changes, checks delivered.', r"signed agreements|executed the agreement|executed agreement|notar|initial the|drop off his check|signed the agreement|plan(s|ned)? to sign|change the legal description|get it completed|take care of it today|executed shortly"),
('ourmove','D','Ball in our court','The next action is ours: answers, documents, approvals or revised agreements owed to the owner.', r"get back to (him|you)|upper management|we are gathering|i will get the answers|counter relayed|passed along for review|forwarded to client|approved through|need to send her an updated|address change forwarded|revise his agreement|will get back|let him know when"),
]
SUCCESS=r"returned (my|our) call|called me back|texted me back|replied|(?<!no one )responded|spoke|received|she stated"
FORCE=r"he is not in|won't be back|will update(d)? note if"
def codes_for(t):
    tl=t.lower(); out=[c[0] for c in CODES if re.search(c[4],tl)]
    if 'contact' in out and (re.search(SUCCESS,tl) or 'redline' in out): out.remove('contact')
    if re.search(FORCE,tl) and 'contact' not in out: out.append('contact')
    return out

CARROLL=r"\bcarroll\b"   # flag, not a theme (excludes McCarroll)

bytract=collections.defaultdict(list)
for r in rd: bytract[r['TRACT_ID']].append(r)
ORDER=['MAILED','DELIVERED','NEGOTIATING','SURVEY REQUESTED','SECOND OFFER LETTER','COMMITTED','ACQUIRED','STATE LANDS']  # least -> most advanced; add new statuses here
def oidx(s): return ORDER.index(s) if s in ORDER else -1
def redact(t):
    t=re.sub(r'\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}','[phone]',t)
    t=re.sub(r'\S+@\S+','[email]',t)
    return t
SKIP=r"incar"   # never show excerpt
name2a={norm(r['LAND_OWNER']):r['ASSOCIATEID'] for r in rd}
owners={}
for n in notes:
    t=clean(n[17]); tr=n[5]; nm=n[7] or ''
    r=bykey.get((tr,norm(nm)))
    if not r:
        cands=bytract.get(tr,[])
        r=next((c for c in cands if norm(nm)[:10] and norm(c['LAND_OWNER']).startswith(norm(nm)[:10])),None) or (cands[0] if cands else None)
    key=('A',name2a[norm(nm)]) if norm(nm) in name2a else (('A',r['ASSOCIATEID']) if r and nm and norm(r['LAND_OWNER']).startswith(norm(nm)[:10]) else ('N',norm(nm) or tr))
    st=r[MSCOL] if r else None
    o=owners.setdefault(key,{'name':nm or (r['LAND_OWNER'] if r else tr),'tracts':set(),'statuses':[],'codes':set(),'notes':{},'agents':set(),'acres':0})
    o.setdefault('raw', r['LAND_OWNER'] if r else None); o.setdefault('tract1', tr)
    o['tracts'].add(tr); o['statuses'].append(st); o['agents'].add(n[2])
    o['acres']+= (n[9] or 0)
    c=codes_for(t); o['codes'].update(c)
    o['notes'].setdefault(t,(n[0],n[2],c))
for o in owners.values():
    cnt=collections.Counter(s for s in o['statuses'] if s)
    o['status']=max(cnt,key=lambda s:(cnt[s],-oidx(s))) if cnt else 'UNKNOWN'

# ---- report ----
import datetime
ST=['MAILED','DELIVERED','NEGOTIATING','SURVEY REQUESTED','SECOND OFFER LETTER','ACQUIRED']
ref=max(n[0] for n in notes)
print(f"Notes: {len(notes)}  Distinct landowners: {len(owners)}  As of: {ref:%m/%d/%y}")
print("Theme | Owners | " + " | ".join(s.title() for s in ST))
for c in CODES:
    os_=[o for o in owners.values() if c[0] in o['codes']]
    print(f"{c[2]} | {len(os_)} | " + " | ".join(str(sum(o['status']==s for o in os_)) for s in ST))
car=[o for o in owners.values() if any(re.search(CARROLL,t.lower()) for t in o['notes'])]
print(f"Carroll flag: {len(car)} owners")
op=[o for o in owners.values() if o['status']!='ACQUIRED']
print(f"Open owners with latest note 21+ days old: {sum((ref-max(d for d,_,_ in o['notes'].values())).days>=21 for o in op)} of {len(op)}")
unc=[o['name'] for o in owners.values() if not o['codes']]
print(f"Uncoded owners: {len(unc)} {unc}")

# ---- dashboard data block ----
import json,datetime
def dk(t): return re.sub(r'[^a-z]','',re.sub(r'\b(today|on)\b','',t.lower()))[:60]
olist=list(owners.values())
idx={id(o):i for i,o in enumerate(olist)}
notes_out={};
for o in olist:
    for t,(d,a,cs) in o['notes'].items():
        e=notes_out.setdefault(dk(t),{'t':t,'d':d,'a':a,'k':set(),'o':set()})
        e['k'].update(cs); e['o'].add(idx[id(o)])
        if d>e['d']: e['d']=d
NL=[]
for e in notes_out.values():
    hide=bool(re.search(SKIP,e['t'],re.I))
    NL.append({'d':e['d'].strftime('%Y-%m-%d'),'a':e['a'],'k':sorted(e['k']),'o':sorted(e['o']),'t':None if hide else redact(e['t'])})
NL.sort(key=lambda n:n['d'],reverse=True)
OL=[]
for o in olist:
    OL.append({'n':o['name'].title() if o['name'].isupper() else o['name'],'m':o.get('raw'),'tr':o.get('tract1'),
      's':o['status'],'a':sorted(o['agents']),'k':sorted(o['codes']),
      'c':any(re.search(CARROLL,t.lower()) for t in o['notes']),
      'd':max(d for d,_,_ in o['notes'].values()).strftime('%Y-%m-%d'),'nt':len(o['tracts'])})
asof=max(n[0] for n in notes)
src=sys.argv[2] if len(sys.argv)>2 else __import__('os').path.basename(sys.argv[1])
NA={'asOf':asof.strftime('%Y-%m-%d'),'source':src,'noteRows':len(notes),
    'themes':[{'k':c[0],'g':c[1],'n':c[2],'def':c[3]} for c in CODES],'owners':OL,'notes':NL}
s=json.dumps(NA,separators=(',',':'),ensure_ascii=False)
open('notes_analysis_block.js','w',encoding='utf-8').write('const NOTES_ANALYSIS = '+s+';\n')
print('Wrote notes_analysis_block.js')
