# Quick Deployment Guide

## Prerequisites

- Ansible installed
- Access to VPS server
- WireGuard VPN configured for local network access

## Deployment Steps

1. **Update variables** (if needed):
   ```bash
   # Edit automation/roles/segments/vars/main.yml
   # Change local_network_ip if your local network uses different IP
   ```

2. **Deploy the role**:
   ```bash
   cd automation
   ansible-playbook -i inventory.yml vps.yml
   ```

3. **Verify DNS resolution**:
   ```bash
   # Test from a device connected via WireGuard
   nslookup photo.bee.home
   # Should return 192.168.1.222
   ```

## Troubleshooting

- **DNS not resolving**: Check if Pi-hole container is running and port 53 is accessible
- **Wrong IP**: Update `local_network_ip` variable and redeploy
- **Domain not working**: Verify WireGuard routing and DNS server configuration

## Configuration Files

- **dnsmasq config**: `/etc/dnsmasq.d/bee-home.conf` (inside Pi-hole container)
- **Variables**: `automation/roles/segments/vars/main.yml`
- **Template**: `automation/roles/segments/templates/bee-home.conf.j2` 