# ha_config

Syncs the **config layer** of Home Assistant with the `ha` inventory host (HAOS
guest, reached via the Advanced SSH & Web Terminal addon, `hassio@192.168.1.223`
+ passwordless sudo).

HA writes into `/config` itself — the automation and script editors, HACS,
blueprint imports. So the role syncs each half of the tree in the direction its
owner works, rather than deploying over the top of live edits:

1. Renders `/config/secrets.yaml` from sops (`ha_recorder_db_url`).
2. **Pushes the git-owned layer** — `configuration.yaml`, `packages/` — from
   `~/dev/ha-config`. This is the only place `!secret` may be referenced.
3. **Snapshots the HA-owned layer back into the repo** — `automations.yaml`,
   `scripts.yaml`, `scenes.yaml`, `blueprints/`, `themes/` — so UI-made changes
   land in git for diff and blame. Read with `slurp`, not `fetch`: `fetch` reads
   as the login user and ignores `become`, and the addon's ssh has no sftp/scp
   server side.
4. Config-checks and reloads automations/scripts/scenes via the core REST API.

Run: `just deploy-ha`, then commit whatever the snapshot pulled into
`~/dev/ha-config`.

## Scope / caveats

- **`/config` is not a git checkout.** A checkout there conflicted with every UI
  save; the repo lives only on the Mac now.
- **No `!secret` in the HA-owned layer.** The editor rewrites its whole file on
  save and cannot round-trip a YAML tag ("Message malformed"), and
  `/api/config/script/config/<id>` returns 500 for every script in a file that
  contains one.
- **Config layer only.** `.storage` (integrations, OAuth, registries, users) is
  runtime state — backed up, not reproducible here. This is not full DR.
- `configuration.yaml`-level changes (recorder, rest, integrations) need a full
  HA restart — the reload handler only covers automations/scripts/scenes.
- The addon must be running for the deploy to reach the host.
