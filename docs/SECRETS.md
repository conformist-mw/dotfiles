# Secrets (SOPS + age)

Secrets live in **age-encrypted SOPS files**, committed to git, auto-decrypted at deploy time.
No more hunting through roles — everything is in three known files.

## Where secrets live

| File | Scope | Edit with |
|---|---|---|
| `group_vars/all/secrets.sops.yaml` | shared by **all** hosts (e.g. telegram alerts bot) | `just secrets-all` |
| `host_vars/bee/secrets.sops.yaml` | **bee** only | `just secrets-bee` |
| `host_vars/hetzner/secrets.sops.yaml` | **hetzner** only | `just secrets-hetzner` |

Ansible auto-loads & decrypts these via the `community.sops` vars plugin
(`vars_plugins_enabled` in `ansible.cfg`). A variable defined here is available to any
role/template on that host as `{{ var_name }}` — no `load_vars`, no per-role files.

> Encryption rule lives in `.sops.yaml` (`creation_rules` → age recipient). Any file matching
> `*.sops.yaml` is encrypted to that recipient automatically.

## The age key (read this)

- Decryption needs your **age private key**. sops looks for it at
  `~/.config/sops/age/keys.txt` (or `$SOPS_AGE_KEY_FILE`).
- **Encryption needs only the public recipient** (already in `.sops.yaml`) — so anyone can
  *add* a secret, but only the key holder can *read/edit*.
- ⚠️ **Lose the key = lose every secret.** Back it up: store in 1Password and/or print it.
- The public recipient currently trusted: `age15q64pz4lwtf95vw3afmku5pzuexnsshm6ndfxhhnkqzj6rc3vc9su8fefq`.

## Common tasks

**Edit / add a secret**
```bash
just secrets-hetzner          # opens the file decrypted in $EDITOR, re-encrypts on save
```
Then reference it in a role/template as `{{ my_secret }}`.

**Add a second recipient (backup key / new machine)**
1. Add the new `age1...` recipient to `.sops.yaml` under the `age:` list.
2. Re-encrypt all files to both recipients:
   ```bash
   just secrets-rekey
   ```

**Naming:** one secret = one flat, descriptive variable (`telegram_alerts_bot_token`,
`navidrome_admin_password`, …). We do **not** mirror Bitwarden's `note`/`value` shape — a
Bitwarden item that packed e.g. a chat-id in `note` and a token in `value` is split into two
named vars.

## Migration from Bitwarden (in progress)

We are moving off Bitwarden Secrets Manager. In the secret files, any value that is a **UUID**
is a Bitwarden reference that still needs to be replaced with the real secret:

1. `just secrets-<host>` and replace the UUID with the real value (pull it from Bitwarden once).
2. In the consuming role, swap `lookup('community.general.bitwarden_secrets_manager', '<uuid>')`
   for `{{ var_name }}`.
3. Done role-by-role; `wireguard` is intentionally deferred.
