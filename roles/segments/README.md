# Segments Role

This role sets up various services including Pi-hole with automatic DNS resolution for local domains.

## Features

- OAuth2 Proxy for authentication
- Traefik reverse proxy with Let's Encrypt
- Pi-hole DNS server with automatic local domain resolution
- Various application containers

## Local Domain DNS Resolution

The role automatically configures Pi-hole to resolve all subdomains of `*.bee.home` to your local network IP address (default: `192.168.1.222`).

### Configuration

You can customize the local domain and IP address by modifying the variables in `vars/main.yml`:

```yaml
# Local domain for automatic DNS resolution
local_domain: "bee.home"
# IP address for local network (bee.home domain)
local_network_ip: "192.168.1.222"
```

### How it works

1. A dnsmasq configuration file is created at `/etc/dnsmasq.d/local.conf` inside the Pi-hole container
2. The configuration uses the `address=/domain/ip` directive to automatically resolve all subdomains
3. Pi-hole is configured to load additional dnsmasq configuration files (`etc_dnsmasq_d=true`)
4. Any request to `*.bee.home` will be resolved to your local network IP

### Example

With the default configuration:
- `photo.bee.home` → `192.168.1.222`
- `jellyfin.bee.home` → `192.168.1.222`
- `any-subdomain.bee.home` → `192.168.1.222`

### Benefits

- No need to manually add DNS records for each subdomain
- Automatic resolution for any subdomain under your local domain
- Works with WireGuard VPN connections
- Centralized DNS management through Pi-hole

### Troubleshooting

**Wildcard DNS not working?** Check if Pi-hole is configured to load dnsmasq configuration files:

1. In Pi-hole web interface, go to Settings → DNS
2. Make sure "Load additional dnsmasq configuration files from /etc/dnsmasq.d/" is enabled
3. Or check the setting `etc_dnsmasq_d=true` in `/etc/pihole/setupVars.conf`

## Usage

Deploy the role using Ansible:

```bash
ansible-playbook -i inventory.yml vps.yml
```

After deployment, ensure your devices are using the Pi-hole DNS server (port 53) and have access to the local network through WireGuard. 