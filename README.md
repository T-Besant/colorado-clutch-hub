# 2027 Colorado Clutch 13U Training Hub

A daily-drills website for the 2027 Colorado Clutch 13U baseball team. The coach
posts a video into one of six sections; players log in, watch, and mark the
drill done — with a scoreboard and streaks to keep them coming back.

## Branding / logo

The header and favicon use `static/logo.svg` (a recreation of the team badge).
**To use the exact team logo:** save your logo image as
`static/logo.png` (any square PNG). The site automatically prefers `logo.png`
when it's present and falls back to the SVG if it isn't. Colors throughout come
from the badge — sky blue `#58a8dd`, deep blue `#123f66`, white, and black.

## Run it (locally, for now)

Double-click **`start.cmd`**, then open **http://127.0.0.1:5055** in any browser.
Leave the black window open while you're using it; close it (or Ctrl+C) to stop.

It uses the Python + Flask already installed for the bookkeeping app, so there's
nothing to install.

## How it works

- **Players** log in with their **name + a personal PIN** (they create it on
  first login). Once in: open a section → watch the video → tap **Mark done**.
  A player can only check off **their own** name — nobody can touch anyone
  else's. They can also **log their own activities** (tee work, batting
  practice, etc.) on their **My Page**, which count just like coach drills.
- **Scoreboard** (top nav, public): ranks everyone by total activities
  completed, with a 🔥 **day-streak** (consecutive days they did *something* —
  a coach drill or a self-logged activity). Miss a day and the streak resets.
- **Coach** (top-right "Coach" link): enter the coach PIN (default **`1234`**)
  to post drills, manage the roster, **reset a player's forgotten PIN**, and
  see who's completed each drill.

Videos are **embedded from links** — paste a YouTube, Facebook, or Instagram
URL and it plays inline. Nothing is uploaded or stored here.

## Player PINs

Each player sets their own PIN the first time they log in (pick name → create
PIN). If a player forgets it, the coach clicks **reset PIN** next to their name
on the Coach dashboard; the player then sets a new one at next login. PINs are
stored hashed, not in plain text.

## Sections

Pitching · Infielding · Outfielding · Catching · Hitting · Speed & Agility

## Files

| File | What it is |
|------|-----------|
| `app.py` | The whole app (routes, video embedding, database). |
| `templates/` | The HTML pages. |
| `static/style.css` | The look/theme. |
| `hub.db` | SQLite database — players (+ PINs), drills, completions, personal logs. Back this up. |
| `start.cmd` | Double-click to run. |

## Notes / next steps (not built yet)

- **Change the coach PIN** — currently `1234`, stored in the `settings` table.
- **Put it on the internet** — this runs on your computer only. Deploying to a
  cheap host (Render / Railway / PythonAnywhere) gives it a real URL players can
  reach from anywhere. That's the planned phase 2.
- Possible later: per-day streaks, "today's drills" summary, parent view,
  photo/comment on completion.
