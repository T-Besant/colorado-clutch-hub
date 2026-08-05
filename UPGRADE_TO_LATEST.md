# Bring your Training Hub up to date

You set up your team's hub a while ago from the original starter files. Since
then the app has grown a lot — badges, a per-player coach review, three bonus-
point systems, coach "development focus" with video, a weekly drill challenge,
and more. This file gets your site up to the **current version** while keeping
**your team name/colors/logo** and **all of your existing data** (roster,
drills, streaks, everything).

**You can hand this whole file to Claude and say "help me upgrade my hub to
this."** It's written so Claude (or you) can follow it start to finish.

> **Two promises before you start:**
> 1. **Your data is safe.** Your database file (`hub.db`) is never part of a
>    code update — you keep your own. When the new code loads for the first
>    time it automatically adds the new tables/columns to your existing
>    database, so your players and their history are preserved *and* gain the
>    new features. There is nothing to migrate by hand.
> 2. **Your branding stays yours.** You'll re-apply three small things (team
>    name, colors, logo). That's the only manual part.

---

## What you're getting (new since the original)

- **Badges** — 10 achievement badges (streaks, totals, all-around), computed
  from history so they never un-earn.
- **My Page** — each player gets personal stats and can **log their own
  activities** (tee work, cage time), edit/delete them, and undo completions.
- **Scoreboard ranks by Points** = activities completed **plus bonus points**.
- **Streaks** with **one forgiven rest day per week**, so a single missed day
  doesn't reset a kid's streak.
- **Team view + player profiles** — players can see what teammates are working
  on (read-only), which drives friendly competition.
- **Coach dashboard upgrades**:
  - **Post drills** now grouped **by section, newest first**.
  - **Announcement banner** shown at the top of everyone's home page.
  - **"Needs a nudge"** list — players with no activity in 3+ days.
  - **"Today"** participation view.
  - **Backup download** — one click to save a full copy of your data.
- **Per-player coach review** — a timeline of everything a player has done,
  where you can **leave notes the player sees on their page**, reverse a
  completion, edit self-logs, **export CSV**, and print.
- **Coach "Development Focus"** — set one thing for a player to work on
  (headline + optional area + details + an optional **video link**). It shows
  at the top of their page with a "New" flag, a "log it for a point" nudge, and
  a collapsible history of past focuses.
- **Three bonus-point systems** (all fold into Points, shown as ⚡ Bonus):
  1. **Speed & Agility daily bonus** — first S&A activity each day = +1.
  2. **Bonus Drill of the Day** — you feature one posted drill; completing it = +1.
  3. **Weekly drill challenge** — completing **7 different** coach drills in one
     week = +1, with a progress tracker on each player's page.

---

## The upgrade — step by step

### Step 1 — Get the current code
Get a fresh copy of the latest files. Either:
- Download the ZIP from the GitHub repo the code lives in
  (`https://github.com/T-Besant/colorado-clutch-hub` → green **Code → Download
  ZIP**), **or**
- Ask the person who shared it with you to send you a current ZIP.

Unzip it somewhere separate from your existing project for now — call it
`new-code`.

### Step 2 — Note your branding (so you can re-apply it)
Open **your existing** project and jot down / keep:
- **Your three name lines** near the top of your `app.py`:
  ```python
  TEAM_NAME = "Your Team Name"
  TEAM_SUBTITLE = "12U Training Hub"
  TEAM_SHORT = "Your Team"
  ```
- **Your colors** — the `--sky`, `--blue`, `--navy` values in the `:root { ... }`
  block at the very top of `static/style.css`.
- **Your logo** — `static/logo.png` and `static/logo.svg`.
- If you renamed the **sections** (the `SECTIONS` list in `app.py`) for a
  different sport, note those too.

### Step 3 — Copy the new code over your project
Copy everything from `new-code` into your project folder, **overwriting the old
files** — with these **exceptions, which you keep as yours**:
- **`hub.db`** (and any `hub.db-*` files) — your data. The new ZIP doesn't
  include one; just make sure you don't delete yours.
- **`static/logo.png`** and **`static/logo.svg`** — your logo (don't let the
  sample logo overwrite yours).
- **`static/icons/`** — only if you changed them for another sport.
- **`secret_key.txt`** — if you have one, keep it (keeps everyone logged in).

### Step 4 — Re-apply your branding
In the newly copied files, put your branding back:
- Set your three `TEAM_` lines in `app.py` (Step 2).
- Set your `--sky` / `--blue` / `--navy` colors in `static/style.css`.
- (Confirm your logo files are still yours, not the sample.)

> Handing this to Claude? It can do Step 4 for you automatically — point it at
> your old `app.py` and `style.css` and it will carry your name and colors into
> the new files.

### Step 5 — Push, pull, reload
From a terminal in your project folder:
```
git add -A
git commit -m "Upgrade to latest hub"
git push
```
Then in your **PythonAnywhere Bash console**:
```
cd ~/your-project-folder && git pull && git log -1 --oneline
```
Finally, **Web tab → big green Reload button**, then open your site and
**hard-refresh** (Ctrl+F5 / Cmd+Shift+R) so the new styles load.

That's it. On that first load the app quietly upgrades your database, and all
the new features are live with your existing roster and history intact.

---

## New settings you can tune (optional)
Near the top of `app.py`:
- `BONUS_SECTION = "speed-agility"` — which section earns the daily +1 bonus.
  Set to `None` to turn that bonus off.
- `WEEKLY_DRILL_GOAL = 7` — how many *different* coach drills in a week earns
  the weekly-challenge bonus. Lower it (e.g. `5`) if 7 feels too hard for your
  team, or set `0` to disable it.

---

## If something looks off
- **A page shows an error (500):** that's a code/template problem — the most
  common cause is a file that didn't copy fully. Re-copy that file, or paste the
  error to Claude.
- **Site won't load at all / "connection timed out":** that's PythonAnywhere's
  host, not your app — usually clears on its own; try again shortly.
- **Changes didn't show up:** you must click **Reload** on the Web tab after a
  pull, then hard-refresh your browser. Most "it didn't work" is a missed reload
  or a cached page.
- **Renewal:** free PythonAnywhere apps need a click to renew every ~3 months
  (they email you). Your data is not lost if you miss it.
