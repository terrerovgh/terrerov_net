# Terrerov.com Network Infrastructure

This repository contains the configuration for the terrerov.com network infrastructure, featuring Pi-hole as a DNS proxy for the local network and Traefik as the DNS resolver for terrerov.com domain.

## Architecture Overview

### DNS Resolution Flow
1. Local network devices (192.168.0.0/25) use Pi-hole as their primary DNS server
2. Pi-hole forwards terrerov.com domain requests to Traefik
3. Traefik resolves terrerov.com requests to the host's local IP address
4. All other domain requests are handled by Pi-hole using Cloudflare DNS (1.1.1.1)

## Setup Instructions

### 1. Environment Configuration
1. Copy `.env.example` to `.env`
2. Configure the following variables:
   - `DOMAIN_NAME`: Your domain name (e.g., terrerov.com)
   - `LAN_NETWORK`: Your local network CIDR (e.g., 192.168.0.0/25)
   - Set other required passwords and API tokens

### 2. Local Network DNS Configuration

Configure your local devices to use Pi-hole as their DNS server:

1. **Manual Configuration:**
   - Set primary DNS to Pi-hole's IP address
   - Remove any secondary DNS to ensure all queries go through Pi-hole

2. **DHCP Configuration:**
   - Configure your router's DHCP server to distribute Pi-hole's IP as the DNS server
   - Alternative: Enable Pi-hole's built-in DHCP server

### 3. Verification

To verify the setup is working correctly:

1. From a local network device, ping terrerov.com
   - Should resolve to the host's local IP address
2. Visit http://pi.hole/admin
   - Check DNS query log to verify proper forwarding
3. Access services via https://service.terrerov.com
   - Should resolve and connect successfully

## Network Details

### DNS Resolution
- **Local Network:** 192.168.0.0/25
- **Docker Network:** 172.20.0.0/16
- **Pi-hole Container:** 172.20.0.53
- **Traefik Container:** 172.20.0.2

### Service Access
- Pi-hole Admin: https://pihole.terrerov.com
- Traefik Dashboard: https://traefik.terrerov.com

## Troubleshooting

### Common Issues

1. **DNS Resolution Failures**
   - Verify Pi-hole is accessible from local network
   - Check Pi-hole logs for forwarding errors
   - Ensure Traefik DNS service is running

2. **Cannot Access Services**
   - Verify local DNS resolution is working
   - Check Traefik logs for routing issues
   - Ensure SSL certificates are valid

## Security Considerations

- Pi-hole is configured to accept DNS queries only from the local network
- All web services are protected with SSL certificates
- Traefik dashboard is secured with basic authentication
- Regular security updates are recommended