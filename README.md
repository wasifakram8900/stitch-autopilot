# Stitch Website Autopilot

Google Sheet row → Google Stitch generates a single-page site → auto-deploy live on Netlify
→ live URL + "Done" written back to the sheet. Pure Python, no LLM in the loop.

## Flow
```
autopilot.py (poll loop)
  └─ sheets_client.read_pending(SHEET_ID)        # rows where Status blank/Pending
       └─ stitch_client.generate_site_html(prompt)   # create_project → generate_screen → download HTML
            └─ netlify_deploy.deploy_html(html)       # → https://<random>.netlify.app
                 └─ sheets_client.mark(row,"Done",url)
```

## Setup
1. **Stitch key** → `.stitch_key` (done ✅)
2. **Netlify token** → `.netlify_token`
   - netlify.com → User settings → Applications → Personal access tokens → New token
   - `echo 'TOKEN' > .netlify_token`
3. **Google Sheets service account** → `.gcp_sa.json`
   - Google Cloud Console → enable *Google Sheets API*
   - Credentials → Create → Service account → Keys → Add key → JSON → save as `.gcp_sa.json`
   - Open the JSON, copy `client_email`, **share your Sheet with that email as Editor**
4. **Sheet** columns A–N: ClientName, Industry, Location, Services, Colors, Phone, Email, Images, Audience, Requirements, DesignStyle, Status, LiveURL, DoneAt
   - put the sheet id (from its URL) into `SHEET_ID=` in `.env`
   - DoneAt (col N) is filled automatically — it's the daily-cap ledger

## Run (no Sheets — test list of 3 fake businesses)
Sequential trigger chain: site 1 generates + deploys LIVE, *then* site 2 starts, *then* site 3.
Edit the `BUSINESSES` list in `run_batch.py` to change the test data.
```
./venv/bin/python run_batch.py          # 3 businesses -> 3 live Netlify URLs
```
Live URLs print at the end and are saved to `out/batch_results.json`; HTML copies in `out/batch/<slug>/index.html`.

## Run (Google Sheets — real rows, later)
```
./venv/bin/python netlify_deploy.py     # test deploy (prints a live URL)
./venv/bin/python sheets_client.py      # test: lists pending rows
./venv/bin/python autopilot.py --once   # one pass
./venv/bin/python autopilot.py          # continuous poll loop
```

## Tune (.env)
`DAILY_CAP` (default 44), `PER_RUN_CAP` (0=unlimited per pass), `POLL_SECONDS` (180), `DEVICE` (DESKTOP/MOBILE).

## Run on cloud — batch test (GitHub Actions, no Sheets)
`.github/workflows/batch.yml` runs `run_batch.py` (the 3 baked-in businesses) on GitHub's runner.
Needs only 2 repo secrets: `STITCH_KEY`, `NETLIFY_TOKEN`. Live URLs appear in the run log and as the
`batch-results` artifact. Trigger it from the Actions tab → "stitch-batch" → "Run workflow".

## Run on cloud (GitHub Actions — free, Mac off)
The cron workflow is at `.github/workflows/autopilot.yml` (runs `autopilot.py --once` every 15 min).
Daily cap survives ephemeral runners because it counts DoneAt rows in the sheet.

1. Make a GitHub repo (**public** = unlimited free Actions minutes; private = 2000 min/mo).
   Secrets are NOT in the code — safe to be public. `.gitignore` already excludes all key files.
2. Push this folder:
   ```
   git init && git add -A && git commit -m "stitch autopilot"
   git branch -M main && git remote add origin <your-repo-url> && git push -u origin main
   ```
3. Repo → Settings → Secrets and variables → Actions → add 4 **secrets**:
   - `STITCH_KEY`     = contents of `.stitch_key`
   - `NETLIFY_TOKEN`  = contents of `.netlify_token`
   - `GCP_SA_JSON`    = the FULL JSON from `.gcp_sa.json` (paste whole file)
   - `SHEET_ID`       = your sheet id
4. Actions tab → enable workflows → "Run workflow" to test, then it self-runs every 15 min.

Credit budget: ~9 credits/site, 400/day → cap 44/day. `PER_RUN_CAP=8` keeps each pass short.
