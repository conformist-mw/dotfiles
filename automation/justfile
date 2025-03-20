set dotenv-load

install:
  uv run ansible-galaxy install -r requirements.yml

deploy-bee:
  uv run ansible-playbook beelink.yml

deploy-hetzner:
  uv run ansible-playbook hetzner.yml

deploy-mac:
  uv run ansible-playbook macos.yml

update-mac-configs:
  uv run ansible-playbook macos.yml --skip-tags "install,uv"

syntax-check:
  uv run ansible-playbook beelink.yml --syntax-check
  uv run ansible-playbook hetzner.yml --syntax-check
  uv run ansible-playbook macos.yml --syntax-check
