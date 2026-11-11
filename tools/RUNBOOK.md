# EPPS weekly update: runbook

## data.js pipeline
- `epps_dump_datajs.js`: `node epps_dump_datajs.js data.js prev.json` dumps every const in a data.js to JSON.
- `epps_build_data.py`: `python3 epps_build_data.py export.xlsx "Nov 10" new.json` builds every weekly array from the export. Stops if a MAIL_STATUS isn't in the Rob_Join hierarchy.
- `epps_notes_themes.py`: `python3 epps_notes_themes.py export.xlsx "<export file name>"` writes `notes_analysis_block.js`. Its `ORDER` list must hold every status (least to most advanced).
- `epps_write_datajs.py`: `python3 epps_write_datajs.py base.js data.js "<stamp>" "<WEEK>" "<PREV WEEK>"` splices new.json + the notes block into base.js. prev.json must be the dump of base.js.
- Same-week rerun: base.js = the data.js from before that week's first commit. Verified 11/11/26: the 11.10.26 export rebuilt byte-for-byte to the live data.js.

## Statuses
- Order comes from Rob_Join `NEW_STATUS` (as of 11/11/26: ACQUIRED, SECOND OFFER LETTER, SURVEY REQUESTED, NEGOTIATING, DELIVERED, MAILED).
- A new status also goes into `index.html`: `STATUS_COLORS` and `STATUS_COLOR_MAP` (fallback colours; the live map's GIS symbology overrides them), the fallback list next to `STATUS_HIERARCHY_LIST`, and the Notes Analysis `const ST = [...]`. SECOND OFFER LETTER was added 11/11/26 with #ff9f40.

## Overview PDF
Output: `EPPS Dashboard - Overview - MM.DD.YY.pdf`, one page, 1224 x 963.75 pt. The top is the dashboard Overview tab captured at 3264 x 2170 (a 1632 x 1085 viewport at 2x). Below it is a 150 pt "Bonus Payments" panel with figures from the export's Weekly Summary tab ("EPPS - Bonus Payments" block).

### Capture in a cloud session (default)
`node epps_capture_overview.js overview.png` opens the live site in headless Chromium (Playwright, pre-installed in cloud sessions) at 1632x1085 and 2x, waits for the parcel layer, fits the map, hides scrollbars and writes a 3264x2170 PNG. It does steps 2-3 below for you. Run it after Vercel has deployed; check that the printed "Last updated" stamp is the new run and look at the PNG before building the PDF.
Network access for the environment must allow `epps-dashboard-ii.vercel.app`, `maps.segland.com` (parcels), `server.arcgisonline.com` (imagery) and `unpkg.com` (Leaflet). Verified 11/11/26: 168 parcels, zoom 13.

### Capture in the desktop app's built-in browser (fallback)
1. Open https://epps-dashboard-ii.vercel.app/ in the built-in browser. Overview tab, latest week, filters on All. Confirm the "Last updated" stamp shows the new run.
2. `resize_window` to 1632x1085, set `document.documentElement.style.overflow='hidden'` (otherwise a 15 px scrollbar gutter makes the page 1617 wide), then fit the map to the parcels:
   `let b=null; leafletParcelLayer.eachFeature(l=>{const bb=l.getBounds(); b=b?b.extend(bb):L.latLngBounds(bb.getSouthWest(),bb.getNorthEast())}); leafletMap.fitBounds(b,{padding:[4,4]})` (zoom 13). If it throws "Bounds are not valid", the parcel layer hasn't loaded yet; wait and retry.
3. Hide scrollbars: inject `*::-webkit-scrollbar{display:none!important;width:0!important;height:0!important}*{scrollbar-width:none!important}`, and set `overflow-x:hidden` on any element whose scrollWidth > clientWidth (the Landowner Movement card shows a horizontal scrollbar otherwise).
4. Screenshots come back at the pane size, which varies (724x481, 800x531). Check one full-scale screenshot first. With pane width P, scale s = 2*1632/P, and each tile covers P/2 x Hp/2 CSS px. Step through 5x5 tiles with `body.style.transformOrigin='0 0'; body.style.transform = scale(s) translate(-i*P/2 px, -j*Hp/2 px)`. Take every screenshot at scale 1.
5. Stitch the tiles at P x Hp steps and crop to 3264x2170. Reset the transform, the html overflow and the viewport afterwards.

### PDF
`python3 make_overview.py overview.png out.pdf <acreage prev> <acreage curr> <acreage total> <infra prev> <infra curr> <infra total> [title]` (reportlab, DejaVu fonts). A Current Week value of $0.00 is grey, non-zero white; totals are blue.

## Pushing
Push from a session that has this repo attached (start it from the Code tab with `SCHOEFFLER-ENERGY-GROUP/Epps---Dashboard-II` selected). In sessions without the repo attached, git push is refused by the session proxy.
