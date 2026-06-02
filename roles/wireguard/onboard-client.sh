#!/usr/bin/env bash
# Generate a NEW WireGuard client config LOCALLY. The client private key is
# printed once (config + QR) and never stored anywhere — not on the server,
# not in this repo. To revoke/replace a client, just generate a new one.
#
# Usage:
#   ./onboard-client.sh <name> <address/32> <endpoint:port> <server_pubkey> [dns]
#
# Example (guest on wg1):
#   ./onboard-client.sh bob 10.0.40.30/32 conformist.name:51830 <wg1_server_pubkey> 10.0.40.1
#
# After running: copy the printed public key into the matching interface's
# `peers:` list in host_vars/hetzner/wireguard.yml, then deploy the wireguard role.
set -euo pipefail

name="${1:?name}"
addr="${2:?client address, e.g. 10.0.40.30/32}"
endpoint="${3:?server endpoint, e.g. conformist.name:51830}"
srv_pub="${4:?server public key}"
dns="${5:-1.1.1.1}"

priv="$(wg genkey)"
pub="$(printf '%s' "$priv" | wg pubkey)"

conf="$(cat <<EOF
[Interface]
PrivateKey = $priv
Address = $addr
DNS = $dns

[Peer]
PublicKey = $srv_pub
Endpoint = $endpoint
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 20
EOF
)"

echo "=== client config ($name) — send this file or the QR below ==="
printf '%s\n' "$conf"
echo
echo "=== QR (scan in the WireGuard mobile app) ==="
printf '%s\n' "$conf" | qrencode -t ansiutf8
echo
echo "=== add this peer to host_vars/hetzner/wireguard.yml ==="
cat <<EOF
      - name: $name
        address: "$addr"
        public_key: "$pub"
EOF
echo
echo "(the private key exists only in the config/QR above — store nothing)"
