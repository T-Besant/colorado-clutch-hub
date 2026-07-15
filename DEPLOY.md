# Deploying the Colorado Clutch Training Hub (PythonAnywhere, free)

Goal: a public HTTPS site at `https://YOURNAME.pythonanywhere.com` the team can
reach from any phone, with the database persisting across restarts and updates.

The app is already production-ready: debug is off under the real server, the
session secret is auto-generated and kept out of source control, and `hub.db`
(your live data) is never overwritten by a code update.

---

## 1. Create the account
- Go to **pythonanywhere.com** → sign up for the **free "Beginner"** plan.
- Your username becomes your URL: `https://USERNAME.pythonanywhere.com`
  (e.g. `coloradoclutch` → `coloradoclutch.pythonanywhere.com`).

## 2. Get the code onto PythonAnywhere (GitHub — recommended for easy updates)
You'll need a free **GitHub** account.

**a. Push the code (from your PC, one time).** The project is already a git repo
with the first commit made and `.gitignore` protecting your data. Create an empty
repo at github.com (New repository → name it e.g. `colorado-clutch-hub` → Private
is fine → do NOT add a README). Then, in a terminal in
`C:\Users\travi\.claude\baseball-training-hub`:
```
git remote add origin https://github.com/YOURGITHUB/colorado-clutch-hub.git
git push -u origin main
```

**b. Clone it on PythonAnywhere.** PythonAnywhere → **Consoles** → start a **Bash**
console, then:
```
git clone https://github.com/YOURGITHUB/colorado-clutch-hub.git baseball-training-hub
```

> No-GitHub alternative: on your PC, zip the project folder. PythonAnywhere →
> **Files** → Upload the zip into your home folder → in a Bash console run
> `unzip <file>.zip -d baseball-training-hub`. (Updating later then means
> re-uploading changed files, which is why GitHub is nicer.)

## 3. Create the web app
- PythonAnywhere → **Web** tab → **Add a new web app** → **Manual configuration**
  (NOT the "Flask" template) → pick the newest Python offered (e.g. 3.10).
- On the Web tab, click the **WSGI configuration file** link. Delete everything in
  it and paste this, replacing `YOURUSERNAME`:
```
import sys
project = "/home/YOURUSERNAME/baseball-training-hub"
if project not in sys.path:
    sys.path.insert(0, project)
from app import app as application
```
  (Same content as `pa_wsgi_reference.py` in the project.) Save.

## 4. Install Flask
In a Bash console (match the Python version you picked):
```
pip3.10 install --user Flask Werkzeug
```

## 5. Reload & open
- Web tab → big green **Reload** button.
- Open `https://YOURUSERNAME.pythonanywhere.com` — the hub should load over HTTPS.

## 6. Bring over your current roster (optional)
The server starts with an empty database. To carry over the players you've already
added: PythonAnywhere → **Files** → open
`/home/USERNAME/baseball-training-hub/` → **Upload** your local
`C:\Users\travi\.claude\baseball-training-hub\hub.db` (it replaces the empty one)
→ Web tab → **Reload**. (Or just re-add players on the live Coach page instead.)

## 7. Lock it down before sharing
- On the live site: **Coach** → log in with `1234` → **Change coach PIN** → set a
  real one.
- Share the URL. Each player taps their name and creates their own PIN on first use.

---

## Updating later (when the code changes)
```
# on your PC, after the new commit is made:
git push
# then in the PythonAnywhere Bash console:
cd baseball-training-hub && git pull
# then Web tab → Reload
```
`hub.db` is gitignored, so **updates never touch your data.**

## Keeping the free app alive
PythonAnywhere emails you every ~3 months to renew the free app — just log in and
click the button on the Web tab. If you miss it the app pauses, but **your data is
not deleted.**
