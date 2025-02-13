# terrerov.com Infrastructure

This repository contains the Docker-based infrastructure for terrerov.com, featuring a robust Traefik reverse proxy setup that handles both LAN and internal Docker network traffic.

## Network Architecture
```
                                    Internet
                                        |
                                        |
                                   [Cloudflare]
                                        |
                                        v
[LAN Network] <---------------> [Traefik Proxy] <----+
192.168.0.0/25                        |             |
                                      |             |
                                      v             |
                          +----------------------+  |
                          |   Docker Network     |  |
                          |   (172.20.0.0/16)   |  |
                          |                      |  |
                          |  +---------------+   |  |
                          |  |   Website    |   |  |
                          |  | (Nginx)      |   |  |
                          |  +---------------+   |  |
                          |                      |  |
                          |  +---------------+   |  |
                          |  |   Pi-hole    |   |  |
                          |  | DNS Server   |   |  |
                          |  +---------------+   |  |
                          |                      |  |
                          |  +---------------+   |  |
                          |  |   Traefik    |<--+  |
                          |  | Dashboard    |      |
                          |  +---------------+      |
                          |                         |
                          +-------------------------+
```

## Features

- **Traefik Reverse Proxy**: Configured using best practices from Christian Lempa's boilerplates
  - Handles both LAN (192.168.0.0/25) and Docker internal network (terrerov_net) traffic
  - Automatic SSL certificate management via Cloudflare DNS challenge
  - Enhanced security with custom middleware configurations
  - Rate limiting and compression enabled

- **Services**:
  - Traefik Dashboard: `https://traefik.terrerov.com`
  - Website: `https://www.terrerov.com`
  - Pi-hole: `https://pihole.terrerov.com`

## Network Configuration

- **LAN Network**: 192.168.0.0/25
  - All services are accessible from LAN devices
  - Automatic HTTPS redirection
  - SSL certificates via Cloudflare DNS

- **Docker Network**: terrerov_net (172.20.0.0/16)
  - Internal container communication
  - Secure service-to-service access

## Security Features

- HTTPS enforcement with automatic redirects
- Strict security headers
- Rate limiting protection
- Basic authentication for sensitive endpoints
- TLS configuration with modern security standards

## Testing Access

### From LAN
1. Connect to the local network (192.168.0.0/25)
2. Access services using their respective domains (e.g., https://www.terrerov.com)
3. SSL certificates should be automatically validated

### From Docker Network
1. Services can communicate using their container names or network aliases
2. Internal services use the same domain names as external access
3. All security policies and SSL certificates are enforced

## Environment Variables

Create a `.env` file with the following variables:

```env
ADMIN_PASSWORD=your_pihole_password
CF_API_TOKEN=your_cloudflare_api_token
EMAIL=your_email
TRAEFIK_PASSWORD=your_traefik_dashboard_password
```

## Usage

1. Clone the repository
2. Create and configure the `.env` file
3. Start the services:
   ```bash
   docker-compose up -d
   ```
4. Access services through their respective domains

## Maintenance

- Monitor the Traefik dashboard for routing and service health
- Check Pi-hole logs for DNS resolution issues
- Regularly update container images for security patches