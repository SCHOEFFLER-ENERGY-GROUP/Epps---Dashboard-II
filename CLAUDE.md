# EPPS Dashboard: weekly update

Static dashboard (`index.html` + `data.js`) deployed by Vercel from `main` to https://epps-dashboard-ii.vercel.app/. `api/` holds Vercel serverless helpers. The weekly update tools are in `tools/` (not deployed; see `.vercelignore`). Full details, including the Overview PDF, are in `tools/RUNBOOK.md`.

## Weekly update
The user attaches `EPPS - Mapper Export - MM.DD.YY.xlsx` and says "update". Run the whole routine without asking questions unless a step says to stop.

1. `WEEK` = the export date as `Mon D` (11.17.26 -> `Nov 17`). `PREV` = the last `date:` in `history` in `data.js`.
2. Base file, in a scratch dir outside the repo:
   - New week: copy the repo's `data.js` to `base.js`.
   - Same-week rerun (a revised export for a week already in `history`): use the data.js from before that week's first commit (`git log --format='%h %s' -- data.js`, then `git show <sha>^:data.js > base.js`), and `PREV` = the week before it.
3. Build (`T` = the repo's `tools/` dir; run from the scratch dir, because `epps_write_datajs.py` reads `new.json`, `prev.json` and `notes_analysis_block.js` from the current dir):
   ```
   pip install openpyxl reportlab --break-system-packages   # if missing
   node $T/epps_dump_datajs.js base.js prev.json
   python3 $T/epps_build_data.py export.xlsx "<WEEK>" new.json
   python3 $T/epps_notes_themes.py export.xlsx "<original export file name>"
   python3 $T/epps_write_datajs.py base.js data.js "<MM/DD/YYYY · h:mm AM CST>" "<WEEK>" "<PREV>"
   ```
   The stamp is the current America/Chicago time.
4. Check: `node $T/epps_dump_datajs.js data.js check.json` must load, and `history` must end with `WEEK`.
5. New status: if `epps_build_data.py` stops with `STATUS NOT IN Rob_Join HIERARCHY`, or Rob_Join has a status the dashboard doesn't know, add it to `ORDER` in `tools/epps_notes_themes.py` and, in `index.html`, to `STATUS_COLORS`, `STATUS_COLOR_MAP`, the fallback list next to `STATUS_HIERARCHY_LIST` and the Notes Analysis `const ST = [...]`. Tell the user which fallback colour you picked.
6. Copy `data.js` into the repo, commit `Weekly update MM/DD/YY (Mapper Export MM.DD.YY)` and push to `main`. Vercel deploys in about a minute.
7. Overview PDF: after Vercel has deployed (the live "Last updated" stamp shows the new run), follow `tools/RUNBOOK.md`:
   ```
   node $T/epps_capture_overview.js overview.png
   python3 $T/make_overview.py overview.png "EPPS Dashboard - Overview - MM.DD.YY.pdf" <bonus figures from the Weekly Summary tab>
   ```
   Look at the PNG before building the PDF, then send the PDF to the user. This works in cloud sessions whose network access allows `epps-dashboard-ii.vercel.app`, `maps.segland.com`, `server.arcgisonline.com` and `unpkg.com`. If those are blocked, say the dashboard is updated and name the hosts to allow (or make the PDF from the desktop app, see the runbook).
8. Reply briefly: landowners and acres by status vs `PREV`, status transitions, the commit, and the PDF.
