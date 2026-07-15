"""
2027 Colorado Clutch 13U Training Hub — a daily-drills site for the team.

The coach posts a video (YouTube / Facebook / Instagram link) into one of six
sections. Players log in with their name + a personal PIN, watch the clip, and
mark it done — a player can only check off their OWN name. Players can also log
their own activities (tee work, batting practice, etc.). A scoreboard ranks
everyone by total activities completed and by day-streak.

Run locally:
    <python-with-flask> app.py
then open http://127.0.0.1:5055

The coach area is behind a separate coach PIN. Storage is a single SQLite file
(hub.db) — no external database needed.
"""
import os
import re
import sqlite3
import urllib.parse
from datetime import datetime, date, timedelta
from functools import wraps

from flask import (
    Flask, g, render_template, request, redirect, url_for,
    session, flash, abort, jsonify,
)
from markupsafe import Markup
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB location can be overridden with the HUB_DB env var; defaults to a file
# next to the code (which is a persistent location on PythonAnywhere).
DB_PATH = os.environ.get("HUB_DB") or os.path.join(BASE_DIR, "hub.db")


def _secret_key():
    """Stable session secret. From SECRET_KEY env var, else a random key
    persisted to a gitignored file so sessions/PINs stay valid across restarts
    without committing the secret to source control."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    path = os.path.join(BASE_DIR, "secret_key.txt")
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        import secrets
        key = secrets.token_hex(32)
        with open(path, "w") as f:
            f.write(key)
        return key

# ---------------------------------------------------------------------------
# Sections — the six training categories. `slug` is used in URLs.
# ---------------------------------------------------------------------------
SECTIONS = [
    {"slug": "pitching",      "name": "Pitching",         "emoji": "⚾"},
    {"slug": "infielding",    "name": "Infielding",       "emoji": "🧤"},
    {"slug": "outfielding",   "name": "Outfielding",      "emoji": "🏃"},
    {"slug": "catching",      "name": "Catching",         "emoji": "🥎"},
    {"slug": "hitting",       "name": "Hitting",          "emoji": "🏏"},
    {"slug": "speed-agility", "name": "Speed & Agility",  "emoji": "⚡"},
]
SECTION_BY_SLUG = {s["slug"]: s for s in SECTIONS}

app = Flask(__name__)
app.config["SECRET_KEY"] = _secret_key()
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS players (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL,
            pin_hash TEXT,
            active   INTEGER NOT NULL DEFAULT 1,
            created  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS activities (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            section     TEXT NOT NULL,
            title       TEXT NOT NULL,
            notes       TEXT,
            video_url   TEXT,
            repeatable  INTEGER NOT NULL DEFAULT 0,
            active      INTEGER NOT NULL DEFAULT 1,
            created     TEXT NOT NULL
        );

        -- One row per (player, drill, DAY): repeatable drills accrue one per day.
        CREATE TABLE IF NOT EXISTS completions (
            activity_id INTEGER NOT NULL,
            player_id   INTEGER NOT NULL,
            done_on     TEXT NOT NULL,       -- 'YYYY-MM-DD'
            done_at     TEXT NOT NULL,       -- full timestamp
            PRIMARY KEY (activity_id, player_id, done_on),
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
            FOREIGN KEY (player_id)   REFERENCES players(id)    ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS personal_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id  INTEGER NOT NULL,
            title      TEXT NOT NULL,
            section    TEXT,
            logged_on  TEXT NOT NULL,       -- 'YYYY-MM-DD'
            created    TEXT NOT NULL,
            FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    # Migration: add pin_hash to an older players table if it's missing.
    cols = [r[1] for r in db.execute("PRAGMA table_info(players)")]
    if "pin_hash" not in cols:
        db.execute("ALTER TABLE players ADD COLUMN pin_hash TEXT")
    # Migration: add the repeatable flag to an older activities table.
    acols = [r[1] for r in db.execute("PRAGMA table_info(activities)")]
    if "repeatable" not in acols:
        db.execute("ALTER TABLE activities ADD COLUMN repeatable INTEGER NOT NULL DEFAULT 0")
    # Migration: rebuild an older completions table (PK activity+player, single
    # done_at) into the per-day model (PK activity+player+done_on).
    ccols = [r[1] for r in db.execute("PRAGMA table_info(completions)")]
    if ccols and "done_on" not in ccols:
        db.executescript(
            """
            CREATE TABLE completions_new (
                activity_id INTEGER NOT NULL,
                player_id   INTEGER NOT NULL,
                done_on     TEXT NOT NULL,
                done_at     TEXT NOT NULL,
                PRIMARY KEY (activity_id, player_id, done_on),
                FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
                FOREIGN KEY (player_id)   REFERENCES players(id)    ON DELETE CASCADE
            );
            INSERT OR IGNORE INTO completions_new (activity_id, player_id, done_on, done_at)
                SELECT activity_id, player_id, substr(done_at, 1, 10), done_at FROM completions;
            DROP TABLE completions;
            ALTER TABLE completions_new RENAME TO completions;
            """
        )
    # Default coach PIN on first run.
    if db.execute("SELECT value FROM settings WHERE key='coach_pin'").fetchone() is None:
        db.execute("INSERT INTO settings(key, value) VALUES('coach_pin', ?)", ("1234",))
    db.commit()
    db.close()


def get_setting(key, default=None):
    row = get_db().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


# ---------------------------------------------------------------------------
# Video embedding — turn a pasted share link into an inline player.
# ---------------------------------------------------------------------------
def embed_for(url):
    """Return safe embed HTML (Markup) for a pasted video URL, or None."""
    if not url:
        return None
    url = url.strip()

    m = re.search(r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([A-Za-z0-9_-]{6,})", url)
    if m:
        src = f"https://www.youtube.com/embed/{m.group(1)}"
        # YouTube Shorts are vertical — frame them portrait so they aren't tiny + letterboxed.
        cls = "video video-portrait" if "/shorts/" in url else "video"
        return Markup(
            f'<div class="{cls}"><iframe src="{src}" title="video" '
            f'frameborder="0" allowfullscreen '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
            f'gyroscope; picture-in-picture"></iframe></div>'
        )

    m = re.search(r"instagram\.com/(reel|reels|p|tv)/([A-Za-z0-9_-]+)", url)
    if m:
        kind = "reel" if m.group(1) in ("reel", "reels") else "p"
        src = f"https://www.instagram.com/{kind}/{m.group(2)}/embed"
        return Markup(
            f'<div class="video video-portrait"><iframe src="{src}" title="video" '
            f'frameborder="0" scrolling="no" allowfullscreen></iframe></div>'
        )

    if "facebook.com" in url or "fb.watch" in url:
        # Facebook's official responsive <fb-video> plugin (rendered by the SDK
        # loaded in base.html). It sizes the player to the video and fills the
        # space cleanly — unlike the bare video.php iframe, which shows small
        # and only looks right in fullscreen.
        m = (re.search(r"[?&]v=(\d+)", url) or re.search(r"/videos/(\d+)", url)
             or re.search(r"/reel/(\d+)", url))
        href = f"https://www.facebook.com/watch/?v={m.group(1)}" if m else url
        is_reel = "/reel" in url
        width = "340" if is_reel else "640"      # reels are vertical → narrower
        h = Markup.escape(href)
        return Markup(
            f'<div class="fbwrap">'
            f'<div class="fb-video" data-href="{h}" data-show-text="false" '
            f'data-width="{width}" data-allowfullscreen="true"></div>'
            f'<p class="videolink"><a href="{h}" target="_blank" rel="noopener">Open on Facebook ↗</a></p>'
            f'</div>'
        )

    safe = Markup.escape(url)
    return Markup(f'<p class="videolink"><a href="{safe}" target="_blank" rel="noopener">▶ Open video</a></p>')


app.jinja_env.globals["embed_for"] = embed_for
app.jinja_env.globals["SECTIONS"] = SECTIONS


@app.template_filter("nicedate")
def nicedate(iso):
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%a %b %d").replace(" 0", " ")
    except (ValueError, TypeError):
        return iso


# ---------------------------------------------------------------------------
# Player identity (name + PIN) and coach auth
# ---------------------------------------------------------------------------
def current_player():
    pid = session.get("player_id")
    if not pid:
        return None
    row = get_db().execute(
        "SELECT * FROM players WHERE id=? AND active=1", (pid,)
    ).fetchone()
    if row is None:
        session.pop("player_id", None)
        session.pop("player_name", None)
    return row


def player_required(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        if current_player() is None:
            return redirect(url_for("login", next=request.path))
        return fn(*a, **k)
    return wrapper


def coach_required(fn):
    @wraps(fn)
    def wrapper(*a, **k):
        if not session.get("coach"):
            return redirect(url_for("coach_login", next=request.path))
        return fn(*a, **k)
    return wrapper


app.jinja_env.globals["current_player"] = current_player
app.jinja_env.globals["is_coach"] = lambda: bool(session.get("coach"))


# ---------------------------------------------------------------------------
# Stats: totals and day-streaks
# ---------------------------------------------------------------------------
def _activity_dates(pid):
    """Set of date objects on which this player did *something*."""
    db = get_db()
    dates = set()
    for r in db.execute("SELECT done_on FROM completions WHERE player_id=?", (pid,)):
        try:
            dates.add(date.fromisoformat(r["done_on"][:10]))
        except (ValueError, TypeError):
            pass
    for r in db.execute("SELECT logged_on FROM personal_logs WHERE player_id=?", (pid,)):
        try:
            dates.add(date.fromisoformat(r["logged_on"][:10]))
        except (ValueError, TypeError):
            pass
    return dates


def _drill_streak(activity_id, pid):
    """Consecutive-day streak for one repeatable drill (ends today/yesterday)."""
    db = get_db()
    dates = set()
    for r in db.execute(
        "SELECT done_on FROM completions WHERE activity_id=? AND player_id=?",
        (activity_id, pid),
    ):
        try:
            dates.add(date.fromisoformat(r["done_on"][:10]))
        except (ValueError, TypeError):
            pass
    return _streak(dates)


def _streak(dates):
    """Current consecutive-day streak ending today or yesterday."""
    if not dates:
        return 0
    today = date.today()
    if today in dates:
        cursor = today
    elif (today - timedelta(days=1)) in dates:
        cursor = today - timedelta(days=1)
    else:
        return 0
    n = 0
    while cursor in dates:
        n += 1
        cursor -= timedelta(days=1)
    return n


def player_stats(pid):
    db = get_db()
    drills = db.execute(
        "SELECT COUNT(*) n FROM completions WHERE player_id=?", (pid,)
    ).fetchone()["n"]
    personal = db.execute(
        "SELECT COUNT(*) n FROM personal_logs WHERE player_id=?", (pid,)
    ).fetchone()["n"]
    dates = _activity_dates(pid)
    week_start = (date.today() - timedelta(days=6)).isoformat()
    week = db.execute(
        "SELECT COUNT(*) n FROM completions WHERE player_id=? AND done_on>=?",
        (pid, week_start),
    ).fetchone()["n"] + db.execute(
        "SELECT COUNT(*) n FROM personal_logs WHERE player_id=? AND logged_on>=?",
        (pid, week_start),
    ).fetchone()["n"]
    return {
        "drills": drills,
        "personal": personal,
        "total": drills + personal,
        "streak": _streak(dates),
        "active_days": len(dates),
        "did_today": date.today() in dates,
        "week": week,
    }


# ---------------------------------------------------------------------------
# Player-facing routes
# ---------------------------------------------------------------------------
def _scoreboard_rows():
    """Ranked scoreboard rows, shared by the home page and /scoreboard."""
    db = get_db()
    players = db.execute("SELECT * FROM players WHERE active=1").fetchall()
    rows = [{"name": p["name"], "id": p["id"], **player_stats(p["id"])} for p in players]
    rows.sort(key=lambda r: (-r["total"], -r["streak"], r["name"].lower()))
    return rows


@app.route("/")
def home():
    db = get_db()
    counts = {s["slug"]: 0 for s in SECTIONS}
    for row in db.execute(
        "SELECT section, COUNT(*) n FROM activities WHERE active=1 GROUP BY section"
    ):
        counts[row["section"]] = row["n"]
    me = current_player()
    stats = player_stats(me["id"]) if me else None
    board = _scoreboard_rows()
    return render_template(
        "home.html", counts=counts, stats=stats,
        board=board, my_id=(me["id"] if me else None),
    )


@app.route("/s/<slug>")
def section(slug):
    if slug not in SECTION_BY_SLUG:
        abort(404)
    db = get_db()
    activities = db.execute(
        "SELECT * FROM activities WHERE section=? AND active=1 ORDER BY created DESC",
        (slug,),
    ).fetchall()
    players = db.execute(
        "SELECT * FROM players WHERE active=1 ORDER BY name COLLATE NOCASE"
    ).fetchall()
    me = current_player()
    today = date.today().isoformat()
    done = {}      # activity_id -> set of players "done" (today if repeatable, else ever)
    mine = {}      # activity_id -> {done, times, streak} for the logged-in player
    for a in activities:
        aid = a["id"]
        if a["repeatable"]:
            done[aid] = {
                r["player_id"] for r in db.execute(
                    "SELECT player_id FROM completions WHERE activity_id=? AND done_on=?",
                    (aid, today))
            }
        else:
            done[aid] = {
                r["player_id"] for r in db.execute(
                    "SELECT DISTINCT player_id FROM completions WHERE activity_id=?", (aid,))
            }
        if me:
            times = db.execute(
                "SELECT COUNT(*) n FROM completions WHERE activity_id=? AND player_id=?",
                (aid, me["id"])).fetchone()["n"]
            mine[aid] = {
                "done": me["id"] in done[aid],
                "times": times,
                "streak": _drill_streak(aid, me["id"]) if a["repeatable"] else 0,
            }
    return render_template(
        "section.html",
        section=SECTION_BY_SLUG[slug],
        activities=activities,
        players=players,
        done=done,
        mine=mine,
    )


@app.route("/toggle", methods=["POST"])
def toggle():
    """Logged-in player marks/unmarks their OWN completion of a drill."""
    me = current_player()
    nxt = request.form.get("next") or url_for("home")
    if me is None:
        return redirect(url_for("login", next=nxt))
    activity_id = request.form.get("activity_id", type=int)
    if not activity_id:
        abort(400)
    db = get_db()
    act = db.execute("SELECT repeatable FROM activities WHERE id=?", (activity_id,)).fetchone()
    if act is None:
        abort(404)
    today = date.today().isoformat()
    if act["repeatable"]:
        # Per-day: toggle just today's completion; past days stay for credit.
        existing = db.execute(
            "SELECT 1 FROM completions WHERE activity_id=? AND player_id=? AND done_on=?",
            (activity_id, me["id"], today),
        ).fetchone()
        if existing:
            db.execute(
                "DELETE FROM completions WHERE activity_id=? AND player_id=? AND done_on=?",
                (activity_id, me["id"], today))
            now_done = False
        else:
            db.execute(
                "INSERT OR IGNORE INTO completions(activity_id, player_id, done_on, done_at) "
                "VALUES(?,?,?,?)",
                (activity_id, me["id"], today, datetime.now().isoformat(timespec="seconds")))
            now_done = True
    else:
        # One-time: done once ever; toggle removes all rows for the pair.
        existing = db.execute(
            "SELECT 1 FROM completions WHERE activity_id=? AND player_id=?",
            (activity_id, me["id"]),
        ).fetchone()
        if existing:
            db.execute(
                "DELETE FROM completions WHERE activity_id=? AND player_id=?",
                (activity_id, me["id"]))
            now_done = False
        else:
            db.execute(
                "INSERT OR IGNORE INTO completions(activity_id, player_id, done_on, done_at) "
                "VALUES(?,?,?,?)",
                (activity_id, me["id"], today, datetime.now().isoformat(timespec="seconds")))
            now_done = True
    db.commit()
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(done=now_done)
    return redirect(nxt)


# ---------------------------------------------------------------------------
# Player login / PIN
# ---------------------------------------------------------------------------
@app.route("/login")
def login():
    players = get_db().execute(
        "SELECT * FROM players WHERE active=1 ORDER BY name COLLATE NOCASE"
    ).fetchall()
    return render_template("login.html", players=players, next=request.args.get("next", ""))


@app.route("/login/<int:pid>", methods=["GET", "POST"])
def login_pin(pid):
    p = get_db().execute(
        "SELECT * FROM players WHERE id=? AND active=1", (pid,)
    ).fetchone()
    if p is None:
        abort(404)
    has_pin = bool(p["pin_hash"])
    nxt = request.values.get("next", "")
    if request.method == "POST":
        pin = (request.form.get("pin") or "").strip()
        if has_pin:
            if check_password_hash(p["pin_hash"], pin):
                session["player_id"] = p["id"]
                session["player_name"] = p["name"]
                return redirect(nxt or url_for("me"))
            flash("That PIN didn't match. Try again.", "error")
        else:
            confirm = (request.form.get("confirm") or "").strip()
            if len(pin) < 4:
                flash("Pick a PIN of at least 4 digits.", "error")
            elif pin != confirm:
                flash("The two PINs didn't match. Try again.", "error")
            else:
                get_db().execute(
                    "UPDATE players SET pin_hash=? WHERE id=?",
                    (generate_password_hash(pin), p["id"]),
                )
                get_db().commit()
                session["player_id"] = p["id"]
                session["player_name"] = p["name"]
                flash("PIN set! You're logged in.", "ok")
                return redirect(nxt or url_for("me"))
    return render_template("login_pin.html", player=p, has_pin=has_pin, next=nxt)


@app.route("/logout")
def logout():
    session.pop("player_id", None)
    session.pop("player_name", None)
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# My Page — personal stats + log-your-own-activity
# ---------------------------------------------------------------------------
@app.route("/me")
@player_required
def me():
    p = current_player()
    db = get_db()
    stats = player_stats(p["id"])
    logs = db.execute(
        "SELECT * FROM personal_logs WHERE player_id=? ORDER BY logged_on DESC, id DESC",
        (p["id"],),
    ).fetchall()
    recent = db.execute(
        """SELECT a.title, a.section, c.done_at
             FROM completions c JOIN activities a ON a.id=c.activity_id
            WHERE c.player_id=? ORDER BY c.done_at DESC LIMIT 10""",
        (p["id"],),
    ).fetchall()
    return render_template(
        "me.html", player=p, stats=stats, logs=logs, recent=recent, today=date.today().isoformat()
    )


@app.route("/me/log", methods=["POST"])
@player_required
def me_log():
    p = current_player()
    title = (request.form.get("title") or "").strip()
    sec = request.form.get("section") or None
    if sec not in SECTION_BY_SLUG:
        sec = None
    when = (request.form.get("logged_on") or "").strip() or date.today().isoformat()
    try:
        date.fromisoformat(when)
    except ValueError:
        when = date.today().isoformat()
    if not title:
        flash("Give your activity a name.", "error")
        return redirect(url_for("me"))
    get_db().execute(
        "INSERT INTO personal_logs(player_id, title, section, logged_on, created) VALUES(?,?,?,?,?)",
        (p["id"], title, sec, when, datetime.now().isoformat(timespec="seconds")),
    )
    get_db().commit()
    flash("Activity logged.", "ok")
    return redirect(url_for("me"))


@app.route("/me/log/<int:lid>/delete", methods=["POST"])
@player_required
def me_log_delete(lid):
    p = current_player()
    get_db().execute(
        "DELETE FROM personal_logs WHERE id=? AND player_id=?", (lid, p["id"])
    )
    get_db().commit()
    flash("Removed.", "ok")
    return redirect(url_for("me"))


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------
@app.route("/scoreboard")
def scoreboard():
    me = current_player()
    return render_template(
        "scoreboard.html",
        rows=_scoreboard_rows(),
        my_id=(me["id"] if me else None),
    )


# ---------------------------------------------------------------------------
# Coach routes
# ---------------------------------------------------------------------------
@app.route("/coach/login", methods=["GET", "POST"])
def coach_login():
    if request.method == "POST":
        pin = request.form.get("pin", "")
        if pin and pin == get_setting("coach_pin"):
            session["coach"] = True
            return redirect(request.args.get("next") or url_for("coach_home"))
        flash("Wrong PIN.", "error")
    return render_template("coach_login.html")


@app.route("/coach/logout")
def coach_logout():
    session.pop("coach", None)
    return redirect(url_for("home"))


@app.route("/coach/pin", methods=["POST"])
@coach_required
def coach_change_pin():
    current = request.form.get("current", "")
    new = (request.form.get("new") or "").strip()
    confirm = (request.form.get("confirm") or "").strip()
    if current != get_setting("coach_pin"):
        flash("Current coach PIN is wrong.", "error")
    elif len(new) < 4:
        flash("New PIN must be at least 4 digits.", "error")
    elif new != confirm:
        flash("The new PINs didn't match.", "error")
    else:
        get_db().execute("UPDATE settings SET value=? WHERE key='coach_pin'", (new,))
        get_db().commit()
        flash("Coach PIN updated.", "ok")
    return redirect(url_for("coach_home"))


@app.route("/coach")
@coach_required
def coach_home():
    db = get_db()
    players = db.execute(
        "SELECT * FROM players WHERE active=1 ORDER BY name COLLATE NOCASE"
    ).fetchall()
    activities = db.execute(
        "SELECT * FROM activities WHERE active=1 ORDER BY created DESC"
    ).fetchall()
    comp = {}
    for r in db.execute(
        "SELECT activity_id, COUNT(*) n FROM completions GROUP BY activity_id"
    ):
        comp[r["activity_id"]] = r["n"]
    return render_template(
        "coach_home.html", players=players, activities=activities, comp=comp
    )


@app.route("/coach/activity/new", methods=["POST"])
@coach_required
def activity_new():
    section = request.form.get("section", "")
    title = request.form.get("title", "").strip()
    notes = request.form.get("notes", "").strip()
    video = request.form.get("video_url", "").strip()
    repeatable = 1 if request.form.get("repeatable") else 0
    if section not in SECTION_BY_SLUG or not title:
        flash("Pick a section and give it a title.", "error")
        return redirect(url_for("coach_home"))
    get_db().execute(
        "INSERT INTO activities(section, title, notes, video_url, repeatable, created) "
        "VALUES(?,?,?,?,?,?)",
        (section, title, notes, video, repeatable, datetime.now().isoformat(timespec="seconds")),
    )
    get_db().commit()
    flash("Posted!", "ok")
    return redirect(url_for("section", slug=section))


@app.route("/coach/activity/<int:aid>/delete", methods=["POST"])
@coach_required
def activity_delete(aid):
    get_db().execute("UPDATE activities SET active=0 WHERE id=?", (aid,))
    get_db().commit()
    flash("Removed.", "ok")
    return redirect(request.form.get("next") or url_for("coach_home"))


@app.route("/coach/player/new", methods=["POST"])
@coach_required
def player_new():
    name = request.form.get("name", "").strip()
    if name:
        get_db().execute(
            "INSERT INTO players(name, created) VALUES(?,?)",
            (name, datetime.now().isoformat(timespec="seconds")),
        )
        get_db().commit()
        flash(f"Added {name}.", "ok")
    return redirect(url_for("coach_home"))


@app.route("/coach/player/<int:pid>/delete", methods=["POST"])
@coach_required
def player_delete(pid):
    get_db().execute("UPDATE players SET active=0 WHERE id=?", (pid,))
    get_db().commit()
    flash("Removed player.", "ok")
    return redirect(url_for("coach_home"))


@app.route("/coach/player/<int:pid>/resetpin", methods=["POST"])
@coach_required
def player_resetpin(pid):
    get_db().execute("UPDATE players SET pin_hash=NULL WHERE id=?", (pid,))
    get_db().commit()
    flash("PIN reset — the player will set a new one at next login.", "ok")
    return redirect(url_for("coach_home"))


@app.route("/coach/activity/<int:aid>")
@coach_required
def activity_detail(aid):
    db = get_db()
    activity = db.execute("SELECT * FROM activities WHERE id=?", (aid,)).fetchone()
    if not activity:
        abort(404)
    players = db.execute(
        "SELECT * FROM players WHERE active=1 ORDER BY name COLLATE NOCASE"
    ).fetchall()
    # Per player: how many days done + the most recent day.
    done = {
        r["player_id"]: {"times": r["n"], "last": r["last"]}
        for r in db.execute(
            "SELECT player_id, COUNT(*) n, MAX(done_on) last "
            "FROM completions WHERE activity_id=? GROUP BY player_id", (aid,)
        )
    }
    return render_template(
        "activity_detail.html",
        activity=activity,
        section=SECTION_BY_SLUG.get(activity["section"]),
        players=players,
        done=done,
    )


@app.route("/coach/today")
@coach_required
def coach_today():
    db = get_db()
    today = date.today().isoformat()
    players = db.execute(
        "SELECT * FROM players WHERE active=1 ORDER BY name COLLATE NOCASE"
    ).fetchall()
    activities = db.execute(
        "SELECT * FROM activities WHERE active=1 ORDER BY created DESC"
    ).fetchall()
    done_today = {}
    for a in activities:
        done_today[a["id"]] = {
            r["player_id"] for r in db.execute(
                "SELECT player_id FROM completions WHERE activity_id=? AND done_on=?",
                (a["id"], today))
        }
    active_today = set()
    for r in db.execute("SELECT DISTINCT player_id FROM completions WHERE done_on=?", (today,)):
        active_today.add(r["player_id"])
    for r in db.execute("SELECT DISTINCT player_id FROM personal_logs WHERE logged_on=?", (today,)):
        active_today.add(r["player_id"])
    return render_template(
        "coach_today.html", players=players, activities=activities,
        done_today=done_today, active_today=active_today, today=today,
    )


# Initialise the schema whenever the module is imported — this is what runs
# under a production WSGI server (PythonAnywhere), which imports `app` and never
# executes the __main__ block below.
init_db()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5055)
