#!/usr/bin/env bash
# Apply a batch of Keenetic CLI configuration commands over SSH.
#
# Companion to dump-config.sh. Keenetic's native CLI is SSH password-only, so we drive
# it with `expect`. Commands are read from a file argument (or stdin) — one CLI command
# per line, blank lines skipped. Use `exit` to leave an interface/pool/etc. sub-context
# (the `!` separators seen in `show running-config` are cosmetic — send `exit` instead).
#
# The full CLI transcript is echoed so syntax errors are visible. Nothing here contains a
# password; the router password is read from the environment, the config-file (which may
# contain e.g. a Wi-Fi PSK) is passed as an argument and kept out of the repo.
#
# Usage:
#   KEEN_PASS=... ./apply-config.sh commands.txt          # apply + 'system configuration save'
#   KEEN_PASS=... ./apply-config.sh --no-save commands.txt # apply only (reboot reverts if unsaved)
#   KEEN_PASS=... ./apply-config.sh < commands.txt
#
# Recommended entrypoint is `just keenetic-apply <file>`, which sources the password from SOPS.
set -euo pipefail

KEEN_HOST="${KEEN_HOST:-192.168.1.1}"
KEEN_USER="${KEEN_USER:-admin}"
: "${KEEN_PASS:?set KEEN_PASS (e.g. via 'just keenetic-apply')}"

SAVE=1
if [[ "${1:-}" == "--no-save" ]]; then SAVE=0; shift; fi

SRC="${1:-/dev/stdin}"
CMDS="$(cat "$SRC")"
[[ -n "$CMDS" ]] || { echo "no commands to apply"; exit 1; }

command -v expect >/dev/null || { echo "expect not found (brew install expect)"; exit 1; }

echo "==> applying $(printf '%s\n' "$CMDS" | grep -c .) commands to $KEEN_USER@$KEEN_HOST (save=$SAVE)"

KP="$KEEN_PASS" KH="$KEEN_HOST" KU="$KEEN_USER" CMDS="$CMDS" SAVE="$SAVE" expect <<'EOF'
set timeout 30
set cmds [split $env(CMDS) "\n"]
spawn ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o PubkeyAuthentication=no -o ConnectTimeout=10 $env(KU)@$env(KH)
expect {
    -re "(?i)password:" { send "$env(KP)\r" }
    -re "(?i)yes/no"    { send "yes\r"; exp_continue }
    timeout { puts "ERR: no password prompt"; exit 1 }
}
expect {
    -re {\([a-z][a-z0-9-]*\)>} {}
    -re "(?i)denied|incorrect" { puts "ERR: auth failed"; exit 2 }
    timeout { puts "ERR: no config prompt"; exit 3 }
}
foreach c $cmds {
    if {[string trim $c] eq ""} { continue }
    send "$c\r"
    expect {
        -re "(?i)--more--|press any key" { send " "; exp_continue }
        -re {\([a-z][a-z0-9-]*\)>} {}
        timeout { puts "ERR: timeout waiting for prompt after: $c"; exit 4 }
    }
}
if {$env(SAVE) == "1"} {
    send "system configuration save\r"
    expect {
        -re {\([a-z][a-z0-9-]*\)>} {}
        timeout { puts "ERR: timeout on save"; exit 5 }
    }
}
send "exit\r"
expect eof
EOF

echo "==> done"
