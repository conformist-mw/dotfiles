# speedtest

Installs the **official Ookla `speedtest` CLI** (from Ookla's packagecloud apt
repo) for accurate on-demand internet speed checks from a shell.

Why not the distro `speedtest-cli` package: that one is the old single-threaded
python client (sivel/speedtest-cli). It picks servers poorly and under-reports
throughput on fast/high-latency links. The Ookla CLI opens multiple connections,
selects a nearby server, and also reports jitter + bufferbloat. This role removes
the python package if present.

## Usage

```sh
speedtest              # human-readable
speedtest --format=json
speedtest --servers    # list nearby servers; pin with -s <id>
```

## Distro / arch

The repo path is built from `ansible_distribution | lower` +
`ansible_distribution_release`, with the arch mapped via `deb_architecture`.
Ookla lags new distro releases, so pin the codename in the playbook when needed:

- **bee** — Ubuntu 24.04 *noble*, but Ookla has no `noble` repo → pinned to
  `jammy` in `beelink.yml` (jammy debs run fine on noble).
- **hetzner** — Debian 12 *bookworm* (arm64), used as-is.
- **rpi** — Debian 13 *trixie* (arm64), published by Ookla, used as-is.

## Apt key

The signing key is downloaded armored to
`/etc/apt/keyrings/ookla_speedtest-cli-archive-keyring.asc` and referenced by
`signed-by`. Not `ansible.builtin.apt_key`: that module needs the `apt-key`
binary, which apt 3.0 (Debian 13) dropped. The `.list` file is written by `copy`,
so the role owns its content and cannot end up with duplicate entries.

License/GDPR are accepted once on install (`speedtest_accept_on_install`, guarded
by a `creates` on `~/.config/ookla/speedtest-cli.json`) so later runs never prompt.
