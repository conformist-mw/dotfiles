#!/usr/bin/env bash
# Pull the Keenetic running-config + components list over SSH for backup / diffing.
#
# Keenetic's native CLI is SSH password-only, so we drive it with `expect`. Output is
# written to roles/keenetic/backups/ (git-ignored). Nothing here contains a password;
# it is read from the environment.
#
# Usage:
#   KEEN_PASS=... ./dump-config.sh                 # uses defaults host=192.168.1.1 user=admin
#   KEEN_HOST=192.168.1.1 KEEN_USER=admin KEEN_PASS=... ./dump-config.sh
#   ./dump-config.sh --sanitize                    # strip secrets from the saved file
#
# Recommended entrypoint is `just keenetic-backup`, which sources the password from SOPS.
set -euo pipefail

KEEN_HOST="${KEEN_HOST:-192.168.1.1}"
KEEN_USER="${KEEN_USER:-admin}"
: "${KEEN_PASS:?set KEEN_PASS (e.g. via 'just keenetic-backup')}"

SANITIZE=0
[[ "${1:-}" == "--sanitize" ]] && SANITIZE=1

command -v expect >/dev/null || { echo "expect not found (brew install expect)"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="$SCRIPT_DIR/backups"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/running-config.txt"
COMP="$OUT_DIR/components.txt"

run_cli() {
  # $1 = CLI command. Logs in, runs it, exits. Strips CR + the ANSI line-clear codes
  # and the interactive echo/prompt noise that the Keenetic CLI emits.
  KP="$KEEN_PASS" KH="$KEEN_HOST" KU="$KEEN_USER" CMD="$1" expect <<'EOF' 2>&1
set timeout 30
spawn ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o PubkeyAuthentication=no -o ConnectTimeout=10 $env(KU)@$env(KH)
expect {
    -re "(?i)password:" { send "$env(KP)\r" }
    -re "(?i)yes/no"    { send "yes\r"; exp_continue }
    timeout { puts "ERR: no password prompt"; exit 1 }
}
expect {
    -re {\(config\)>} {}
    -re "(?i)denied|incorrect" { puts "ERR: auth failed"; exit 2 }
    timeout { puts "ERR: no prompt"; exit 3 }
}
send "$env(CMD)\r"
expect {
    -re "(?i)--more--|press any key" { send " "; exp_continue }
    -re {\(config\)>} {}
    timeout {}
}
send "exit\r"
expect eof
EOF
}

# strip CR + ANSI line-clears, then keep only the lines between the echoed command
# and the trailing "(config)> exit" — i.e. drop the SSH banner, prompt and login noise.
clean() {
  local cmd="$1"
  tr -d '\r' | sed 's/\x1b\[K//g' \
    | awk -v cmd="$cmd" '
        !started { if ($0 ~ (cmd "$")) started=1; next }   # skip banner up to the echoed cmd
        /^\(config\)>/ { exit }                            # stop at the next prompt
        { print }
      '
}

echo "==> dumping running-config from $KEEN_USER@$KEEN_HOST"
run_cli "show running-config" | clean "show running-config" > "$OUT"
echo "==> dumping components list"
run_cli "components list" | clean "components list" > "$COMP"

if [[ "$SANITIZE" == "1" ]]; then
  # redact the secret-bearing lines so the file is safe to read/share
  sed -i.bak -E \
    -e 's/(authtoken )[^ ]+/\1<REDACTED>/' \
    -e 's/(password (nt|md5) ).*/\1<REDACTED>/' \
    -e 's/(authentication wpa-psk ns3 ).*/\1<REDACTED>/' \
    -e 's/(iapp key ns3 ).*/\1<REDACTED>/' \
    "$OUT" && rm -f "$OUT.bak"
  echo "==> sanitized secrets in $OUT"
fi

echo "saved:"
echo "  $OUT"
echo "  $COMP"
