#!/usr/bin/env python3
"""Snapshot the family-hub database before a migration is run against it.

The nightly vps-backup role already covers this database, and covers it well.
What it cannot cover is the window between last night and now: migrations run
whenever somebody deploys, and 0006 — which dropped three columns off
regular_slots — went out at 19:53, sixteen hours after the newest snapshot.
Nothing was lost, because the snapshot that time was taken by hand. This is
that hand, written down.

Deliberately self-contained rather than calling the nightly script. Deploys run
as `just deploy-hetzner-tag family-hub`, which runs this role and nothing else,
so anything installed by the backup role may legitimately not be there. A
safety net that is missing exactly when it is needed is worse than none,
because it is believed in. The cost is the ~15 lines of snapshot logic below
also existing in roles/vps-backup/templates/vps-backup.sh.j2; if either
changes, change both.

Usage: premigrate-snapshot.py <database> <output-dir> <keep>
"""

import glob
import gzip
import os
import shutil
import sqlite3
import sys
import tempfile
import time

# The prefix must NOT start with "family-hub-": the nightly script rotates on
# that glob and keeps a fixed number, so sharing it would let a busy day of
# deploys push out the dailies this exists to complement.
PREFIX = "premigrate-family-hub-"


def main() -> int:
    src, outdir, keep = sys.argv[1], sys.argv[2], int(sys.argv[3])

    # A fresh install has no database and nothing to protect. Not an error:
    # the deploy that creates it must not be the one that fails.
    if not os.path.exists(src):
        print(f"no database at {src} — nothing to snapshot")
        return 0

    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, PREFIX + time.strftime("%Y%m%d-%H%M%S") + ".db.gz")

    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        # Not a file copy: the app is running and the database is in WAL mode,
        # so copying it under a live writer yields a file that only looks
        # intact. sqlite's own backup API takes a consistent snapshot of a
        # database being written to.
        con = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
        dst = sqlite3.connect(tmp)
        with dst:
            con.backup(dst)
        # A snapshot that cannot be read back is worse than a missing one: it
        # would be trusted, and it would rotate a good one out.
        if dst.execute("pragma integrity_check").fetchone()[0] != "ok":
            print(f"integrity check failed for {src}", file=sys.stderr)
            return 1
        # Counted so the deploy log says what was saved rather than only that
        # something was. Tolerated when the tables are absent: a database file
        # that exists but holds nothing is the "-db pointed somewhere new"
        # accident, and the snapshot of it is still worth taking — reporting it
        # as empty is more use than failing here with a schema error.
        try:
            rows = dst.execute(
                "SELECT (SELECT COUNT(*) FROM visits), (SELECT COUNT(*) FROM appointments)"
            ).fetchone()
        except sqlite3.Error:
            rows = None
        dst.close()
        con.close()

        # Written aside and moved, so an interrupted run cannot leave a
        # half-written file that looks like a snapshot.
        with open(tmp, "rb") as f, gzip.open(out + ".tmp", "wb") as g:
            shutil.copyfileobj(f, g)
        os.replace(out + ".tmp", out)
    finally:
        os.unlink(tmp)

    size = os.path.getsize(out)
    held = f"{rows[0]} visits, {rows[1]} appointments" if rows else "no recognisable tables"
    print(f"{os.path.basename(out)} ({size} bytes, {held})")

    # Keep the newest few. These accumulate per deploy rather than per day, and
    # the nightly snapshots are the actual history — what is wanted here is the
    # state immediately before the last handful of schema changes.
    stale = sorted(glob.glob(os.path.join(outdir, PREFIX + "*.db.gz")), reverse=True)[keep:]
    for path in stale:
        os.unlink(path)
        print(f"pruned {os.path.basename(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
