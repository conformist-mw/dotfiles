#!/usr/bin/env python3
"""Delete music from the library on a marker set from any Subsonic client.

Two entry points share one delete path:

  daemon  poll the annotation table for tracks marked with the reap rating and
          remove them; this is what makes "mark it on the phone" work.
  nope    remove whatever is playing right now, no marker needed.

Either marker works: a star, or a rating of 1.

The star is the one that matters. It is the gesture this workflow was built on
long before this script existed, it is one tap in every Subsonic client, and it
is what the hand reaches for. An earlier version of this file moved the marker
to a rating alone, on the theory that the star should stay free to mean
"favourite" for smart playlists. That was a design opinion imposed on someone
else's established habit, and the first thing that happened was a track starred
for deletion that quietly survived. The rating is kept as a second way in for
anyone who does want the star back for favourites.

Three things the previous shell version got wrong, all fixed here:
  - it never cleared the marker, so every run re-found rows whose files were
    already gone and logged "File not found" forever (49605 such lines against
    2172 real deletes);
  - it left the row in navidrome, so the track kept showing up until an
    unrelated timer happened to purge it;
  - it joined MUSIC_DIR to a DB path with no check that the result stayed
    inside MUSIC_DIR.

The database is only ever opened read-only. Every write goes through the API,
because navidrome holds the sqlite file open with a WAL and a second writer can
corrupt it.
"""
import argparse, datetime as dt, hashlib, json, os, random, shutil
import sqlite3, string, sys, time
import urllib.parse
import httpx

MUSIC_DIR = os.environ.get("REAPER_MUSIC_DIR", "{{ MUSIC_DIR }}")
DB_PATH   = os.environ.get("REAPER_DB_PATH",   "{{ DATABASE_PATH }}")
BASE_URL  = os.environ.get("ND_BASE_URL",      "http://localhost:4533").rstrip("/")
USERNAME  = os.environ.get("ND_USERNAME", "")
PASSWORD  = os.environ.get("ND_PASSWORD", "")
REAP_RATING = int(os.environ.get("REAPER_RATING", "1"))
POLL_SECONDS = int(os.environ.get("REAPER_POLL_SECONDS", "5"))
# How long a mark has to sit before the file goes.
#
# Not a safety margin for the person, a margin for the *player*. Marking a track
# and skipping it does not mean the client is finished with it: it prefetches and
# revisits its queue, and measured against a real listening session it came back
# asking for deleted tracks a median of 37 seconds later. At 15 seconds only 10
# of 32 such requests would have been covered, at 60 seconds 25 of 32, and five
# minutes only buys four more. Requests arriving minutes later come from a queue
# the client cached and no server-side delay can help those.
MARK_GRACE_SECONDS = int(os.environ.get("REAPER_MARK_GRACE_SECONDS", "60"))
# One mistaken bulk-rating must not be able to empty the library.
MAX_PER_SWEEP = int(os.environ.get("REAPER_MAX_PER_SWEEP", "25"))
# How long to wait for navidrome's watcher to flag a deleted file as missing.
PURGE_TIMEOUT = int(os.environ.get("REAPER_PURGE_TIMEOUT", "120"))

AUDIO = {".mp3", ".flac", ".m4a", ".wma", ".wav", ".ogg", ".opus", ".aac"}


def log(msg):
    print(msg, flush=True)


def subsonic_params():
    salt = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
    token = hashlib.md5((PASSWORD + salt).encode()).hexdigest()
    return {"u": USERNAME, "t": token, "s": salt,
            "v": "1.16.1", "c": "nd_reaper", "f": "json"}


def subsonic(client, endpoint, **extra):
    p = subsonic_params(); p.update(extra)
    r = client.get(f"{BASE_URL}/rest/{endpoint}", params=p, timeout=30)
    r.raise_for_status()
    body = r.json()["subsonic-response"]
    if body.get("status") != "ok":
        raise RuntimeError(f"{endpoint}: {body.get('error')}")
    return body


def native_token(client):
    r = client.post(f"{BASE_URL}/auth/login",
                    json={"username": USERNAME, "password": PASSWORD}, timeout=30)
    r.raise_for_status()
    return r.json()["token"]


def db():
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def _age_seconds(stamp):
    """Seconds since an ISO timestamp from navidrome, or None if unparseable."""
    if not stamp:
        return None
    try:
        t = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return (dt.datetime.now(dt.timezone.utc) - t).total_seconds()


def marked_tracks(grace=None):
    """Tracks flagged for removal by either marker, oldest mark first.

    A mark younger than the grace period is skipped this round, not dropped: the
    next sweep picks it up once it has aged.
    """
    grace = MARK_GRACE_SECONDS if grace is None else grace
    con = db(); con.row_factory = sqlite3.Row
    rows = con.execute(
        """select m.id, m.path, m.title, m.artist,
                  a.starred, a.rating,
                  max(coalesce(a.starred_at, ''), coalesce(a.rated_at, '')) marked_at
             from annotation a join media_file m on m.id = a.item_id
            where a.item_type = 'media_file'
              and (a.starred = 1 or a.rating = ?)
            order by marked_at asc""", (REAP_RATING,)).fetchall()
    con.close()
    ready = []
    for r in rows:
        d = dict(r)
        age = _age_seconds(d.get("marked_at"))
        # An unparseable or absent timestamp must not strand a mark forever.
        if age is not None and age < grace:
            continue
        ready.append(d)
    return ready


def track_by_id(track_id):
    con = db(); con.row_factory = sqlite3.Row
    r = con.execute("select id, path, title, artist from media_file where id = ?",
                    (track_id,)).fetchone()
    con.close()
    return dict(r) if r else None


def safe_full_path(rel):
    """Join and prove the result is still inside the library."""
    root = os.path.realpath(MUSIC_DIR)
    full = os.path.realpath(os.path.join(root, rel))
    if full != root and not full.startswith(root + os.sep):
        raise ValueError(f"path escapes library: {rel!r}")
    return full


def prune_empty_parents(path):
    """Walk up from a deleted file, removing directories that it emptied."""
    root = os.path.realpath(MUSIC_DIR)
    d = os.path.dirname(os.path.realpath(path))
    while d.startswith(root + os.sep):
        try:
            if any(os.scandir(d)):
                return
            os.rmdir(d)
        except OSError:
            return
        d = os.path.dirname(d)


def clear_marker(client, track_id):
    """Drop both markers, so a vanished file is never re-processed.

    Clearing unconditionally rather than only the marker that fired: the row is
    about to stop existing anyway, and leaving half of it set is exactly the
    loop the shell version got stuck in.
    """
    for call, kwargs in (("unstar", {"id": track_id}),
                         ("setRating", {"id": track_id, "rating": 0})):
        try:
            subsonic(client, call, **kwargs)
        except Exception as e:
            log(f"ERROR clearing {call} for {track_id}: {e}")


def ids_present(ids):
    """Which of `ids` navidrome still has a row for."""
    if not ids:
        return set()
    con = db()
    q = "select id from media_file where id in (%s)" % ",".join("?" * len(ids))
    present = {r[0] for r in con.execute(q, tuple(ids))}
    con.close()
    return present


def purge_missing(client, wait_for=(), timeout=PURGE_TIMEOUT):
    """Make navidrome forget rows whose files are gone, now rather than later.

    Deleting a file does not by itself update navidrome: its filesystem watcher
    has to notice and flag the row `missing` first, which takes a few seconds.
    Purging immediately would find nothing and leave a phantom track in the UI,
    so keep going until the rows we care about are actually gone.

    Waiting on the specific ids matters: counting purged rows instead would let
    an unrelated leftover satisfy the wait and return before our own delete had
    even been noticed.
    """
    token = native_token(client)
    headers = {"x-nd-authorization": f"Bearer {token}"}
    wait_for = set(wait_for)
    removed = 0
    backoff = 1.0
    deadline = time.monotonic() + timeout
    while True:
        r = client.get(f"{BASE_URL}/api/missing",
                       params={"_start": 0, "_end": 100}, headers=headers, timeout=30)
        r.raise_for_status()
        items = r.json()
        if items:
            qs = "&".join("id=" + urllib.parse.quote(i["id"]) for i in items)
            resp = client.request("DELETE", f"{BASE_URL}/api/missing?{qs}",
                                  headers=headers, timeout=60)
            if resp.status_code < 400:
                removed += len(items)
                backoff = 1.0
                continue
            # navidrome answers 500 when its own DELETE hits SQLITE_BUSY, which
            # it does while it is busy writing play counts for something being
            # streamed. Retrying immediately makes that worse and leaves the row
            # in place, so the track stays in playlists with no file behind it
            # and playback 404s. Back off instead.
            log(f"purge refused ({resp.status_code}), retrying in {backoff:.0f}s")
            if time.monotonic() + backoff >= deadline:
                log(f"purge gave up with {len(items)} row(s) still missing")
                return removed
            time.sleep(backoff)
            backoff = min(backoff * 2, 15)
            continue
        if not ids_present(wait_for) or time.monotonic() >= deadline:
            return removed
        time.sleep(2)


def reap(client, tracks, reason):
    """Delete the files behind `tracks`. Returns the ids that actually went."""
    gone = []
    for t in tracks:
        try:
            full = safe_full_path(t["path"])
        except ValueError as e:
            log(f"REFUSED {e}")
            continue
        label = f'{t.get("artist") or "?"} - {t.get("title") or t["path"]}'
        if os.path.exists(full):
            try:
                os.remove(full)
                prune_empty_parents(full)
                gone.append(t["id"])
                log(f"deleted [{reason}] {label}  <- {t['path']}")
            except OSError as e:
                log(f"ERROR deleting {t['path']}: {e}")
                continue
        else:
            log(f"already gone [{reason}] {t['path']}")
        # Clear the marker even when the file was already missing: that is the
        # exact state the old script looped on forever.
        try:
            clear_marker(client, t["id"])
        except Exception as e:
            log(f"ERROR clearing marker for {t['path']}: {e}")
    return gone


def cmd_nope(args):
    # The instant path. Deliberately ignores the grace period: this is the
    # explicit "kill what I am hearing right now" command, not a queued mark.
    with httpx.Client() as client:
        body = subsonic(client, "getNowPlaying")
        entries = body.get("nowPlaying", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        if not entries:
            log("nothing is playing")
            return 1
        entries.sort(key=lambda e: e.get("minutesAgo", 0))
        e = entries[0]
        t = track_by_id(e["id"])
        if not t:
            log(f"playing track {e['id']} is not in the database")
            return 1
        log(f'now playing: {t["artist"]} - {t["title"]}')
        if args.dry_run:
            log(f"would delete {t['path']}")
            return 0
        gone = reap(client, [t], "now-playing")
        if gone:
            purge_missing(client, wait_for=gone)
        return 0


def cmd_sweep(args):
    with httpx.Client() as client:
        tracks = marked_tracks()
        if not tracks:
            return 0
        if len(tracks) > MAX_PER_SWEEP and not args.force:
            log(f"REFUSED: {len(tracks)} tracks marked, cap is {MAX_PER_SWEEP}. "
                f"Re-run with --force if that is really intended.")
            return 1
        if args.dry_run:
            for t in tracks:
                log(f'would delete {t["artist"]} - {t["title"]}  <- {t["path"]}')
            return 0
        gone = reap(client, tracks, "marked")
        if gone:
            purge_missing(client, wait_for=gone)
        return 0


def cmd_daemon(args):
    log(f"reaper watching stars and rating={REAP_RATING} every {POLL_SECONDS}s, "
        f"acting {MARK_GRACE_SECONDS}s after a mark")
    while True:
        try:
            cmd_sweep(args)
        except Exception as e:
            log(f"sweep failed: {e}")
        time.sleep(POLL_SECONDS)


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dry-run", action="store_true")
    common.add_argument("--force", action="store_true",
                        help="allow a sweep larger than the safety cap")
    ap = argparse.ArgumentParser(description=__doc__, parents=[common])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, helptext in (("daemon", "poll for marked tracks and remove them"),
                           ("sweep",  "one pass over marked tracks"),
                           ("nope",   "delete whatever is playing right now")):
        sub.add_parser(name, help=helptext, parents=[common])
    args = ap.parse_args()
    if not (USERNAME and PASSWORD):
        log("ND_USERNAME / ND_PASSWORD are not set"); return 2
    return {"daemon": cmd_daemon, "sweep": cmd_sweep, "nope": cmd_nope}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
