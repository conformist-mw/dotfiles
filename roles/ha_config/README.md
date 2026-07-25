# ha_config

Deploys the **config layer** of Home Assistant into the HAOS `/config` git
checkout on the HA VM (`ha` inventory host, reached via the Advanced SSH & Web
Terminal addon, `hassio@192.168.1.223` + passwordless sudo).

What it does:

1. `git pull --ff-only` the [`conformist-mw/ha-config`](https://github.com/conformist-mw/ha-config)
   repo in `/config` (deploy key `/config/.ssh/gh_ha`).
2. Renders `/config/secrets.yaml` from sops vars (`ha_recorder_db_url`,
   `ha_tg_*`) — so secrets live in one place and never touch the repo.
3. Reloads automations/scripts/scenes via the core REST API (config-checked
   first).

Run: `just deploy-ha` (or `deploy-ha-tag` — n/a, single role).

## Scope / caveats

- **Pull-only.** Edit config in the local clone `~/dev/ha-config`, push, then
  `just deploy-ha`. Don't edit tracked files on the server.
- **Config layer only.** `.storage` (integrations, OAuth, registries, users) is
  runtime state — backed up, not reproducible here. This is not full DR.
- **Assumes the repo is already initialised in `/config`** (HAOS pre-populates
  the dir, so the initial `git init`/remote setup was done manually once).
- `configuration.yaml`-level changes (recorder, packages, integrations) need a
  full HA restart — the reload handler only covers automations/scripts/scenes.
- The addon must be running for the deploy to reach the host.
