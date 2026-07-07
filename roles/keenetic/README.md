# keenetic

Reference + backup for the **Keenetic Giga (KN-1011)** home router (`KeeneticOS 5.x`).

This is not a deploy role like the others — Keenetic has no good declarative API, its
config *is* a list of CLI commands. So this directory is:

1. **This README** — the human map of how the network is wired and *why*, so future-you
   doesn't have to reverse-engineer it again.
2. **`dump-config.sh`** — pull `running-config` + `components list` over SSH for backup /
   diffing (`just keenetic-backup`).

Source of truth for exact settings is the device itself; this README is the explanation
layer. The router is reached at `192.168.1.1`, user `admin`, **SSH password only** (Keenetic
doesn't do key auth for the native CLI). The password lives in SOPS (see *Secrets* below).

---

## Hardware & port map

Only **3 of the 4 LAN ports are LAN** — port 1 was repurposed as a second WAN.

| Keenetic port | Role | What's behind it |
|---|---|---|
| Internet (dedicated) | **WAN1** — ISP "Союз Телеком", DHCP | the internet |
| LAN **1** | **WAN2** — `Vlan4` "Dlan", `10.1.13.72/19` via `10.1.4.4` | second provider uplink |
| LAN **2** | trunk (Home untagged + VLAN2 tagged) | Keenetic PoE switch → Buddy + Voyager (mesh APs) + SLZB-06 Zigbee dongle |
| LAN **3** | trunk (Home untagged + VLAN2 tagged) | TP-Link **TL-SG108E** (uplink on sw p1) → hall switch (sw p2), son's room PC+MikroTik (sw p5/p6), NVR (sw p7), 8-cam PoE switch (sw p8) |
| LAN **4** | trunk (Home untagged + VLAN2 tagged) | Beelink (`bee`, `192.168.1.222`) |

**Dual-WAN:** both WAN1 (ISP) and WAN2 (Dlan) are configured with default routes;
Keenetic picks the active one by connection priority (`ip global` weight: ISP `64851` >
Dlan `32425` → ISP is primary, Dlan is failover). Verify/adjust in the web UI under
*Internet → connection priorities*.

---

## Segments / VLANs

`isolate-private` is **on** globally — private segments can't talk to each other unless an
ACL explicitly allows it.

| Segment | Bridge | VLAN | Subnet | DHCP | Security | Notes |
|---|---|---|---|---|---|---|
| **Home** | `Bridge0` | 1 (untagged) | `192.168.1.0/24` | `.33–.152` | private | main LAN + Wi-Fi, NAT |
| **CCTV** | `Bridge1` | 2 (tagged) | `192.168.10.0/24` | `.50–.150` | protected (isolated from Home) | trunked on ports 2/3/4; NVR + wired cameras at `.112–.119`. Tag 2 ⇄ subnet `.10` (cosmetic mismatch). |

VLAN2 is tagged on every LAN trunk port. **Note the tag/subnet mismatch:** the 802.1Q tag is
`2` (what the ports trunk), the subnet is `192.168.10.0/24`.

**Home → CCTV** is permitted by `access-list _WEBADMIN_Home` (phone viewing of the NVR);
**CCTV → Home** is blocked by isolation, with one deliberate pinhole: `_CCTV_NVR_MOES` permits
the NVR (`192.168.10.112`) → the Wi-Fi Moes camera still in Home (`192.168.1.123`), applied
inbound on `Bridge1`. Remove it once Moes moves onto a CCTV Wi-Fi SSID.

---

## Wi-Fi

| AP | Band | SSID | Auth | State |
|---|---|---|---|---|
| `WifiMaster0/AccessPoint0` | 2.4 GHz | `Keenetic` | WPA2-PSK | up |
| `WifiMaster1/AccessPoint0` | 5 GHz | `Keenetic5` | WPA2-PSK | up |
| `WifiMaster0/AccessPoint1` (`GuestWiFi`) | 2.4 GHz | — | none | **down** |
| `WifiMaster1/AccessPoint1` (`GuestWiFi_5G`) | 5 GHz | — | none | **down** |

Band-steering is on (Home bridge). The two **guest** APs are pre-provisioned but disabled
and password-less — enabling them is Phase 2. The mesh (Buddy + Voyager) is managed via MWS
(controller member `50:ff:20:9d:d6:f9`).

---

## WireGuard — it's a *client/peer*, not a server

`Wireguard0` ("keenetic_wg") is this router joining the **hetzner `wg0` network** as a peer
— there is **no `wireguard-server`** on the router, and none is needed.

| | |
|---|---|
| Peer endpoint | `conformist.name:51820` (the hetzner VPS) |
| Router tunnel IP | `10.0.0.100/32` |
| Peer allowed-ips | `0.0.0.0/0` |
| Keepalive | 20s (keeps the NAT hole open — this router is behind **CGNAT**) |
| MTU | 1324 |
| Route | `10.0.0.0/24 → Wireguard0` |

The router **initiates** the tunnel (CGNAT means nothing can reach it inbound) and
**advertises `192.168.1.0/24` into the tunnel**. That is how family VPN clients on hetzner
`wg0` and services on the VPS reach the home LAN (e.g. Home Assistant at `192.168.1.223`).
The matching server side — `allowed_ips: 192.168.1.0/24` for the `keenetic` peer — lives in
`host_vars/hetzner/wireguard.yml` (see `roles/wireguard/README.md`). If you ever wondered
"how does WG work with no server installed" — this is the answer.

---

## DNS

- `service dns-proxy` is the LAN resolver, with **NextDNS as its filter engine** (profile
  assigned to the Home interface + one specific host). Fallback preset `cleanbrowsing-family`,
  `rebind-protect auto`.
- Upstream DNS on the Dlan WAN: `91.203.63.1`, `91.193.130.30`.
- Local DNS overrides: `*.bee.local → 192.168.1.222`. **Stale:** `*.rpi.local → 192.168.1.2`
  (that IP is now the TL-SG108E switch, not a Pi — cleanup candidate).

> Note for the future keen-pbr idea: its `dns-override` would put keen-pbr's own dnsmasq in
> front and bypass this `dns-proxy` path, so NextDNS would have to move to being keen-pbr's
> upstream (a local DoH proxy). Not done — parked.

---

## Services & hygiene

Running: `dhcp`, `dns-proxy`, `igmp-proxy`, `http`/`https`, `cifs`, `telnet`, `ssh`, `ntp`,
`upnp`.

- **`cifs`** shares the two USB-flash partitions: `backup` and `entware`. The flash also
  hosts Entware (`opkg disk entware:/`). The `bee` host rclone-pushes photos to the
  `backup/` share nightly (see `roles/backup`).
- **Hygiene candidates:** `telnet` (:23) is on — SSH is enough, disable it. `upnp` is on for
  Home — review. Stale `*.rpi.local` records — remove.

## Routing extras

- `192.168.88.0/24 → 192.168.1.11` (the MikroTik runs its own subnet).

## Firmware components

Entware/OPKG is installed on the flash. `opkg` is held mandatory by six kernel modules
(`opkg-kmod-{audio,dvb-tuner,fs,tc,usbip,video}`) that aren't used — removable. The future
keen-pbr (policy-routing some domains via the VPS WG) would instead need
`opkg-kmod-netfilter` + `opkg-kmod-netfilter-addons`, which are **not** installed.

---

## Secrets

Never commit these in plaintext (this repo is shared). They are: the **admin password**,
**Wi-Fi PSK**, and the **NextDNS auth token**. Only the admin password is needed by tooling
here — store it in SOPS:

```yaml
# group_vars/all/secrets.sops.yaml   (edit: just secrets-all)
keenetic_admin_password: <password>
```

The Wi-Fi PSK and NextDNS token live only on the device.

---

## Backup & restore

**Snapshot the config (for history / diffing):**

```bash
just keenetic-backup        # SSH in, pull running-config + components list
```

Output goes to `roles/keenetic/backups/` which is **git-ignored** — it contains MACs, device
names and (depending on flags) secrets. If you want it in git, encrypt it with sops first.

**Authoritative restore** is the binary config file via the web UI
(*System → Files → `running-config`/`startup-config`*, download/upload) — keep a recent copy
in a safe place. The text dump from `keenetic-backup` is for human reading and diffs, not a
one-click restore; individual settings can be re-applied by pasting CLI lines and running
`system configuration save`.

---

## Planned changes (tracked here so they don't get forgotten)

### 1. Cameras → isolated CCTV VLAN  *(Phase 1)*
Move NVR + the 8 cameras off Home (they sit at `192.168.1.112–119` today) into their own
VLAN. **Decisions:** reuse **VLAN2** (already trunked on port 3), subnet **`192.168.10.0/24`**
(matches the pre-built `_WEBADMIN_Home` "home to cctv" ACL), **internet allowed** for the
cameras (keep `ip nat Bridge1`).

> Note the cosmetic mismatch: the 802.1Q **tag stays `2`** (that's what port 3 trunks), while
> the **subnet is `.10`**. Tag 2 ⇄ subnet 192.168.10.0/24 — functional, just numbered
> differently.

- ✅ **Keenetic (`Bridge1`) — done:** re-addressed to `192.168.10.1/24`, DHCP pool
  `.50–.150`, 8 camera/NVR reservations moved to `.112–.119`, kept `security-level protected`
  + `ip nat Bridge1`. `_WEBADMIN_Home` permits **Home → CCTV**; **CCTV → Home** stays blocked
  except the `_CCTV_NVR_MOES` pinhole (see *Segments*). Safe to do ahead of the switch because
  VLAN2 had no clients.
- **TL-SG108E (802.1Q mode), CCTV = VLAN tag 2:** untagged + PVID 2 on sw-port 7 (NVR) and
  sw-port 8 (camera PoE switch); **tagged** VLAN2 on the uplink port to Keenetic; VLAN1
  untagged + PVID 1 everywhere else (incl. the uplink, so Home + switch mgmt `192.168.1.2`
  stay reachable).
- **TL-SG108E ports:** uplink = **p1** (untagged VLAN1 + tagged VLAN2, PVID 1); NVR = p7 and
  camera PoE switch = p8 (untagged VLAN2, PVID 2); everything else (hall switch p2, son's room
  p5/p6, spares p3/p4) stays untagged VLAN1, PVID 1. Management VLAN = 1.
- **⚠ Gotcha:** the NVR addresses cameras by their current `192.168.1.x` IPs. After the move
  they get `192.168.10.x` — the NVR must re-discover / re-add them (or set matching statics),
  or recording breaks.

### 2. Guest Wi-Fi  *(Phase 2)*
Enable `GuestWiFi` + `GuestWiFi_5G`, set a WPA2 password, confirm the guest segment is
internet-only and isolated from Home (Keenetic isolates guests by default).

### 3. Hygiene
Disable `telnet`; remove stale `*.rpi.local` records; review UPnP; drop the six unused
`opkg-kmod-*` components.
