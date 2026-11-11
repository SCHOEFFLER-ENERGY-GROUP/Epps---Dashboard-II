"""Splice new.json + notes_analysis_block.js into data.js.
Usage: python3 epps_write_datajs.py <base data.js> <out data.js> "<stamp>" <WEEK> <PREV_WEEK>
  e.g. python3 epps_write_datajs.py base.js data.js "11/10/2026 · 2:42 PM CST" "Nov 10" "Nov 3"
Reads new.json, prev.json (dump of base.js) and notes_analysis_block.js from the current dir.
base must NOT already contain WEEK (for a same-week rerun, use the data.js from before that week's commit)."""
import json,re,sys,collections
BASE,OUT,STAMP,WEEK,PREV=sys.argv[1:6]
src=open(BASE).read()
n=json.load(open('new.json')); p=json.load(open('prev.json'))
def fix(o):
    if isinstance(o,float) and o.is_integer(): return int(o)
    if isinstance(o,list): return [fix(x) for x in o]
    if isinstance(o,dict): return {k:fix(v) for k,v in o.items()}
    return o
J=lambda o:json.dumps(fix(o),separators=(',',':'),ensure_ascii=False)
def block(name):
    m=re.search(r'^(?:const|let) '+name+r' = ',src,re.M); st=m.start()
    nx=re.search(r'^// ----',src[m.end():],re.M); en=m.end()+nx.start() if nx else len(src)
    return st,en
def rep(name,text):
    global src; st,en=block(name); src=src[:st]+text+'\n\n'+src[en:]
src=re.sub(r"const EPPS_LAST_UPDATED = '[^']*';",f"const EPPS_LAST_UPDATED = '{STAMP}';",src)
src=re.sub(r'const STATUS_HIERARCHY = \[[^\]]*\];','const STATUS_HIERARCHY = ['+',  '.join(json.dumps(s) for s in n['HIER'])+'];',src)
h=n['history']
def lit(d): return '{'+', '.join((k if re.match(r'^[A-Z_]+$',k) else repr(k))+':'+repr(v) for k,v in d.items())+'}'
ent=f"  {{ date:'{WEEK}', totalLandowners:{h['totalLandowners']}, totalAcres:{h['totalAcres']!r},\n    acres:{lit(h['acres'])},\n    landowners:{lit(h['landowners'])} }},\n"
assert f"date:'{WEEK}'" not in src, 'base already has '+WEEK
i=src.index('];',src.index('const history = ['))
src=src[:i]+ent+src[i:]
rep('landownerData','const landownerData = '+J(n['landownerData'])+';')
st,en=block('landownerSnapshots'); blk=src[st:en]
k=blk.rindex('};'); blk=blk[:k]+f"  '{WEEK}': "+J(n['snap'])+',\n'+blk[k:]
src=src[:st]+blk+src[en:]
rep('landownerDetails','const landownerDetails = {\n'+''.join('  '+json.dumps(k,ensure_ascii=False)+':'+J(v)+',\n' for k,v in n['details'].items())+'};')
rep('eppsLineList','const eppsLineList = [\n'+',\n'.join(J(r) for r in n['lineList'])+'\n];')
rep('iolTracking','let iolTracking = [\n'+',\n'.join(J(r) for r in n['iol'])+'\n];')
RANK={s:i for i,s in enumerate(reversed(n['HIER']))}
prevS={o['aid']:o['status'] for o in p['landownerSnapshots'][PREV]}
c=collections.Counter()
for o in n['snap']:
    a=prevS.get(o['aid'])
    if a and a!=o['status']: c[(a,o['status'])]+=1
tr=''.join(f'  {{"from":"{a}","to":"{b}","count":{v},"dir":"{"fwd" if RANK.get(b,0)>RANK.get(a,0) else "bwd"}"}},\n' for (a,b),v in c.most_common())
rep('transitions','const transitions = [\n'+tr+'];')
cols=['var(--series-1)','var(--series-2)','var(--series-3)']
def money(x): return repr(fix(x))
rep('brokerage','const brokerage = [\n'+''.join(f"  {{ name:'{r['name']}', prev:{money(r['prev'])}, curr:{money(r['curr'])}, total:{money(r['total'])}, budget:{money(r['budget'])}, color:'{cols[i]}' }},\n" for i,r in enumerate(n['brokerage']))+'];')
rep('bonus','const bonus = [\n'+''.join(f"  {{ name:'{r['name']}', prev:{money(r['prev'])}, curr:{money(r['curr'])}, total:{money(r['total'])}, color:'{cols[i]}' }},\n" for i,r in enumerate(n['bonus']))+'];')
na=open('notes_analysis_block.js').read().strip()
st,en=block('NOTES_ANALYSIS'); src=src[:st]+na+'\n'
open(OUT,'w').write(src)
print(c)
