set dotenv-load

install:
  uv run ansible-galaxy install -r requirements.yml

# === Beelink (home server) ===
deploy-bee:
  uv run ansible-playbook beelink.yml

deploy-bee-tag tag:
  uv run ansible-playbook beelink.yml --tags {{ tag }}

# === Hetzner (VPS) ===
deploy-hetzner:
  uv run ansible-playbook hetzner.yml

deploy-hetzner-tag tag:
  uv run ansible-playbook hetzner.yml --tags {{ tag }}

# === MacOS ===
deploy-mac:
  uv run ansible-playbook macos.yml

deploy-mac-tag tag:
  uv run ansible-playbook macos.yml --tags {{ tag }}

update-mac-configs:
  uv run ansible-playbook macos.yml --skip-tags "install,uv"

# === Secrets (sops + age) ===
# edit the encrypted secret files (needs your age key, see docs/SECRETS.md)
secrets-all:
  sops group_vars/all/secrets.sops.yaml

secrets-bee:
  sops host_vars/bee/secrets.sops.yaml

secrets-hetzner:
  sops host_vars/hetzner/secrets.sops.yaml

# re-encrypt every sops file to the current recipients in .sops.yaml (run after adding a key)
secrets-rekey:
  find group_vars host_vars roles -name '*.sops.yaml' -exec sops updatekeys -y {} \;

# === Utilities ===
list-tags-bee:
  uv run ansible-playbook beelink.yml --list-tags

list-tags-hetzner:
  uv run ansible-playbook hetzner.yml --list-tags

syntax-check:
  uv run ansible-playbook beelink.yml --syntax-check
  uv run ansible-playbook hetzner.yml --syntax-check
  uv run ansible-playbook macos.yml --syntax-check
