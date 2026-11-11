const fs=require('fs');const src=fs.readFileSync(process.argv[2],'utf8');
const names=['EPPS_LAST_UPDATED','STATUS_HIERARCHY','history','landownerData','landownerSnapshots','landownerDetails','eppsLineList','iolTracking','transitions','brokerage','bonus','MAP_STATUS_OVERRIDES','NOTES_ANALYSIS'];
const f=new Function(src+';return {'+names.join(',')+'};');
fs.writeFileSync(process.argv[3],JSON.stringify(f()));
