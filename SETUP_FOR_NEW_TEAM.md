# Set up this Training Hub for YOUR team

This is a ready-to-run web app for a youth sports team: a coach posts drill
videos into sections; players log in with a personal PIN, watch, and mark drills
done; a scoreboard and streaks keep them coming back. It was built for a baseball
team but works for any sport.

**You can hand this whole file to Claude and say "help me set this up."** It's
written so Claude (or you) can follow it start to finish. Below is (A) what to
customize to make it yours, and (B) how to put it online for free.

You do NOT need to be a programmer. You DO need to create two free accounts
(GitHub and PythonAnywhere) — those are yours to make; nobody can make them for you.

---

## A. Make it your team's (customize)

Three things: the name, the colors, and the logo. All quick.

### 1. Team name — edit `app.py`
Near the top of `app.py` is a clearly-marked block. Change these three lines:
```python
TEAM_NAME = "2027 Colorado Clutch"     # big name in the header
TEAM_SUBTITLE = "13U Training Hub"      # small line under the name
TEAM_SHORT = "Colorado Clutch"          # short name used in browser tab titles
```
to your team, e.g.:
```python
TEAM_NAME = "Northside Thunder"
TEAM_SUBTITLE = "12U Training Hub"
TEAM_SHORT = "Thunder"
```
That's the only place the name lives — it updates the whole site.

### 2. Colors — edit the top of `static/style.css`
At the very top is a `:root { ... }` block. Change these to your colors:
```css
--sky:   #58a8dd;   /* main accent (light) */
--blue:  #1f83c6;   /* buttons */
--navy:  #0e2c47;   /* top bar / headings */
```
(Leave the rest as-is unless you want to tweak more.)

### 3. Logo — replace two files in the `static/` folder
- `static/logo.png` — your team logo (any square PNG; ~200×200 or larger is great)
- `static/logo.svg` — a fallback. Simplest: just copy your PNG over both names,
  or ask Claude to make a simple SVG version.

### 4. The six sections (optional)
The sections (Pitching, Hitting, etc.) are the `SECTIONS` list in `app.py`. For a
different sport, change the names/slugs there and swap the matching icon files in
`static/icons/`. For baseball, leave them.

> The database (`hub.db`) is NOT included — your app starts empty and you add your
> own roster and drills. Nobody else's data comes with it.

---

## B. Put it online for free (PythonAnywhere)

This hosts the app so your team can reach it from any phone, with free HTTPS, and
your data persists.

### 1. Get the code onto your computer, then GitHub
- Create a free account at **github.com**.
- Make a new **empty** repository (New repository → name it e.g. `team-hub` →
  Private is fine → do NOT add a README).
- Get this project's files onto your machine (whoever shared it can send you a zip,
  or you download it from their GitHub repo with the green **Code → Download ZIP**
  button). Unzip it.
- In a terminal inside the project folder, run (replace YOURNAME/team-hub):
```
git init -b main
git add -A
git commit -m "Initial commit"
git remote add origin https://github.com/YOURNAME/team-hub.git
git push -u origin main
```
  (Claude can run these for you and walk through the GitHub login popup.)

### 2. Create the PythonAnywhere web app
- Create a free **"Beginner"** account at **pythonanywhere.com**. Your username
  becomes your web address: `https://USERNAME.pythonanywhere.com`.
- **Consoles** → start a **Bash** console → clone your repo:
```
git clone https://github.com/YOURNAME/team-hub.git team-hub
```
  (If it's a private repo and asks for a password, either make the repo public —
  there are no secrets in the code — or set up a GitHub token.)
- Install Flask:
```
pip3.10 install --user Flask Werkzeug
```
- **Web** tab → **Add a new web app** → **Manual configuration** → **Python 3.10**.
- Click the **WSGI configuration file** link, delete everything, paste this
  (replace YOURUSERNAME) and Save:
```python
import sys
project = "/home/YOURUSERNAME/team-hub"
if project not in sys.path:
    sys.path.insert(0, project)
from app import app as application
```
- **Web** tab → big green **Reload** button → open your
  `https://USERNAME.pythonanywhere.com`. It should load.

### 3. First-run setup
- Open the site → **Coach** (top right) → log in with the default PIN **`1234`**.
- Immediately use **"Change coach PIN"** (bottom of the coach dashboard) to set a
  real one.
- Add your players from the roster box, and post your first drills (paste a
  YouTube / Facebook / Instagram link into a section).
- Share the URL with your team. Each player taps their name and sets their own PIN.

---

## Good to know
- **Your data is safe on updates.** `hub.db` (your roster/drills/streaks) is kept
  out of source control, so pulling code changes never overwrites it.
- **Free PythonAnywhere apps** must be renewed every ~3 months (they email you;
  just click the button on the Web tab). Your data is not lost if you miss it.
- **Videos:** YouTube embeds most reliably (unlisted videos work). Facebook videos
  must be public to embed. Vertical Shorts/Reels are auto-framed.
- Stuck on any step? Paste the error to Claude — it can read this file and fix it.
