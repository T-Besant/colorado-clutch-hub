# How to update the live Training Hub website

Plain-English checklist for pushing new changes to the live site at
**https://coclutch13u.pythonanywhere.com**.

The big picture: your code lives in two places — **your computer** (where changes
get made) and **PythonAnywhere** (the live website). Updating = shipping the code
from your computer up to PythonAnywhere, then restarting the site.

**Your team's data (roster, drills, logs) is never touched by any of this** — only
the code moves. So you can't lose player data by updating.

It's always the same 3 steps: **SEND → RECEIVE → RESTART.**

---

## First: open a terminal in the hub folder

A "terminal" is just a window where you type commands instead of clicking buttons.

1. Open **File Explorer** (yellow folder icon on the taskbar).
2. Go to this folder:
   `C:\Users\travi\.claude\baseball-training-hub`
   - Can't see the `.claude` folder? Click **View → Show → Hidden items** at the
     top of File Explorer (folders starting with a dot are hidden by default).
3. Click in the **address bar** at the top (the strip that shows the folder path).
4. Type **`powershell`** over it and press **Enter**.

A blue window opens, already pointed at the hub folder. You'll see the line end
with `...\baseball-training-hub>` — that's how you know you're in the right place.

---

## Step 1 — SEND the changes up (in that terminal, on your computer)

Type this and press Enter:

```
git push
```

That uploads the latest changes to GitHub.
(A browser window may pop up asking you to log into GitHub the first time — that's normal.)

## Step 2 — RECEIVE the changes (on PythonAnywhere)

1. Go to **pythonanywhere.com** and log in.
2. Click the **Consoles** tab → open your **Bash** console.
3. Type these two lines, pressing Enter after each:

```
cd baseball-training-hub
git pull
```

That downloads the changes onto the live server.

## Step 3 — RESTART the site (on PythonAnywhere)

1. Click the **Web** tab at the top.
2. Click the big green **Reload** button.

Wait about 10 seconds, then open your website — the update is live. ✅

---

## If something looks wrong after a reload

On the **Web** tab there's an **error log** link. Open it, copy the last chunk of
text, and send it to Claude — that's the fastest way to find what went wrong.

## Reminder

- `hub.db` (your player data) is deliberately excluded from all of this, so
  pushing/pulling code never overwrites your roster, drills, or logs.
- Every future update is the same three steps: **`git push`** (your computer) →
  **`git pull`** (PA Bash console) → **Reload** (PA Web tab).
