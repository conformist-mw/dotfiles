# Dotfiles & Infrastructure

Ansible playbooks for deploying:
- **beelink** — home server (Jellyfin, Navidrome, Traefik, etc.)
- **hetzner** — VPS (oauth2-proxy, segments, commeilfaut, etc.)
- **macos** — MacBook setup (Homebrew, dev tools, configs)

## Quick Start

```bash
# Install dependencies
just install

# Deploy everything to a host
just deploy-bee
just deploy-hetzner
just deploy-mac
```

## Deploy Specific Roles

```bash
# Single role
just deploy-bee-tag homepage
just deploy-hetzner-tag segments

# Multiple roles
just deploy-bee-tag "traefik,homepage"

# By category
just deploy-bee-tag apps      # all applications
just deploy-bee-tag base      # system setup only
just deploy-bee-tag infra     # infrastructure (traefik, cockpit)

# Skip certain roles
uv run ansible-playbook beelink.yml --skip-tags base
```

## Available Tags

```bash
just list-tags-bee
just list-tags-hetzner
```

### Beelink
| Category | Tags |
|----------|------|
| Base | `base`, `beelink`, `docker`, `vim` |
| Infra | `infra`, `traefik`, `cockpit` |
| Apps | `apps`, `jellyfin`, `navidrome`, `homepage`, `dozzle`, `glances`, `portainer`, `gitea`, `pgadmin`, `filebrowser`, `immich`, `samba`, `torrent`, `sponsorblock`, `redis`, `backup` |

### Hetzner
| Category | Tags |
|----------|------|
| Base | `base`, `vps`, `docker`, `vim`, `wireguard` |
| Apps | `apps`, `segments`, `commeilfaut`, `homepage`, `dozzle`, `glances`, `rsstt`, `memos`, `flatnotes` |

### MacOS
| Tags | Description |
|------|-------------|
| `install` | Homebrew packages and casks |
| `uv` | Python versions and tools |

## Requirements

- [uv](https://github.com/astral-sh/uv) — Python package manager
- [just](https://github.com/casey/just) — command runner
- [bws](https://github.com/bitwarden/sdk-sm/releases) — Bitwarden Secrets Manager CLI

## Other Commands

```bash
# Update MacOS configs only (skip installs)
just update-mac-configs

# Syntax check all playbooks
just syntax-check
```
