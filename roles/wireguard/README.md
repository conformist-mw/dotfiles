# wireguard

A generic role that configures one or more WireGuard interfaces on a host from a
declarative `wg_interfaces` map. Topology lives in inventory
(`host_vars/<host>/wireguard.yml`), server private keys in SOPS — the role itself
is host-agnostic.

## Networks (hetzner)

| Interface | Who | Access | DNS |
|---|---|---|---|
| `wg0` | family | internet **+ LAN** (`192.168.1.0/24`, `*.bee.home`) | pihole (`10.0.0.1`) |
| `wg1` | guests | internet **only**, LAN hard-blocked | pihole adblock (`10.0.40.1`) |

LAN reachability on `wg0` comes from the `keenetic` peer advertising
`192.168.1.0/24` (`allowed_ips`); the server just forwards `wg0 -> wg0`. `wg1` has
`isolated: true`, so the firewall script `DROP`s any forward into RFC1918 — guest
isolation is enforced, not merely "no route".

## How `wg_interfaces` maps to config

Per interface: `address`, `port`, `public_key` (server, plaintext — not secret),
`private_key` (from SOPS), `peers[]` (each `name` / `address` / `public_key`,
optional `allowed_ips`). Behaviour flags:

- `allow_lan: true` — add `FORWARD -i wgX -o wgX ACCEPT` (peers + advertised LAN).
- `isolated: true` — `DROP` all forwards into `10/8`, `172.16/12`, `192.168/16`.
- `dns_local: true` — DNAT `:53` aimed at the gateway to `127.0.0.1` (pihole) and
  set `route_localnet` on the interface at PostUp.

The external interface for NAT is detected at deploy time
(`ansible_default_ipv4.interface`) — nothing is hardcoded to `eth0`.

## Secrets

Only the two **server** private keys are secret:

```yaml
# host_vars/hetzner/secrets.sops.yaml  (edit with: just secrets-hetzner)
wg0_private_key: <key>
wg1_private_key: <key>
```

Peer **public** keys are not secret and live in `wireguard.yml` in plaintext.
Client **private** keys are never stored — they live only in the config/QR handed
to the client (see onboarding).

## Onboarding a client

```bash
roles/wireguard/onboard-client.sh <name> <addr/32> <endpoint:port> <server_pubkey> [dns]
```

Prints the client config + QR (private key shown once, stored nowhere) and the
`peers:` block to paste into `wireguard.yml`. Then deploy:

```bash
ansible-playbook hetzner.yml --tags wireguard
```

To revoke/rotate: generate a new client (new keypair), replace the peer's
`public_key`, redeploy.

## Moving to a new VPS (same domain)

Clients pin the **server public key** + **endpoint domain** (`conformist.name`).
Both are preserved across a move, so:

1. Stand up the new VPS, point `conformist.name` at its IP.
2. Deploy — the same server private keys come from SOPS, the same public keys and
   peers from `wireguard.yml`.

Clients reconnect transparently. Nothing is re-sent. (Never regenerate the server
keys — that is the one thing that would break every client.)
