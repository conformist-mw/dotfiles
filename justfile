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

update-mac-configs:
  uv run ansible-playbook macos.yml --skip-tags "install,uv"

# === Utilities ===
list-tags-bee:
  uv run ansible-playbook beelink.yml --list-tags

list-tags-hetzner:
  uv run ansible-playbook hetzner.yml --list-tags

syntax-check:
  uv run ansible-playbook beelink.yml --syntax-check
  uv run ansible-playbook hetzner.yml --syntax-check
  uv run ansible-playbook macos.yml --syntax-check
