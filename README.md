# Terrerov Network Project

This project sets up a complete Docker-based network infrastructure with DNS, reverse proxy, web server, and database services. It's designed to be easily deployable on both Raspberry Pi and standard computers running Docker.

## Prerequisites

- Docker CE (Community Edition) installed
- Docker Compose installed (version 1.29.0 or higher)
- Basic understanding of Docker and networking concepts

## Services Included

- **Bind9**: DNS server for internal domain name resolution
- **Pi-hole**: DNS server and ad-blocker for external access
- **Traefik**: Reverse proxy and SSL certificate manager
- **Nginx**: Web server for hosting static content
- **PostgreSQL**: Database server

## Quick Start

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd terrerov_net
   ```

2. Create and configure the `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your preferred text editor and set your values
   ```

3. Make the installation script executable:
   ```bash
   chmod +x install.sh
   ```

4. Run the installation script:
   ```bash
   ./install.sh
   ```

## Environment Variables

Configure the following variables in your `.env` file:

- `USER`: Your username
- `EMAIL`: Your email address (used for SSL certificates)
- `ADMIN_PASSWORD`: Admin password for services
- `TRAEFIK_PASSWORD`: Password for Traefik dashboard
- `ROOT_PASSWORD`: Root password for services
- `CF_API_TOKEN`: Cloudflare API token for DNS challenge
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: PostgreSQL database name

## Accessing Services

The services can be accessed through both VPN (Twingate) and local network:

### VPN Access (Twingate)

When connected through Twingate VPN, services are automatically accessible at:

- Traefik Dashboard: https://traefik.terrerov.com
- Web Server: https://www.terrerov.com
- Database: db.terrerov.com:5432
- Pi-hole Admin Interface: https://pihole.terrerov.com

#### Configuring Twingate with Pi-hole

1. Access your Twingate Admin Console
2. Navigate to the Network Settings
3. Set the Primary DNS to the Pi-hole container's IP address within the terrerov_net network
4. All VPN clients will now use Pi-hole for DNS resolution

### DNS Resolution Flow

The network implements a dual-DNS server setup with Pi-hole as the primary external DNS server:

1. **External Access (VPN Clients)**:
   - Pi-hole handles all DNS queries (172.20.0.53)
   - Custom DNS records for terrerov.com managed through /pihole/custom.list
   - Uses Cloudflare DNS (1.1.1.1, 1.0.0.1) for external domains

2. **Internal Access (Docker Containers)**:
   - Bind9 handles internal DNS resolution
   - Manages service discovery within terrerov_net
   - Provides authoritative DNS for the internal network

### Managing Custom DNS Records

Pi-hole is configured to resolve terrerov.com and its subdomains using custom DNS records. To add or modify DNS records:

1. Edit the `/pihole/custom.list` file on the host machine
2. Format: `<ip-address> <domain>`
3. Use ${HOST_IP} variable for the Docker host's IP address
4. Example entries:
   ```
   ${HOST_IP} terrerov.com
   ${HOST_IP} *.terrerov.com
   ${HOST_IP} service.terrerov.com
   ```
5. Pi-hole will automatically detect changes and update its DNS records

### SSL Security Configuration

Traefik is configured with enhanced SSL security features:

1. **HSTS (HTTP Strict Transport Security)**:
   - Enabled with a 1-year duration (31536000 seconds)
   - Includes subdomains
   - Preload list enabled

2. **TLS Configuration**:
   - Minimum TLS version: 1.2
   - Modern cipher suites only:
     - ECDHE with AES-GCM
     - ECDHE with ChaCha20-Poly1305

3. **Certificate Management**:
   - Automatic SSL certificates via Let's Encrypt
   - DNS challenge through Cloudflare
   - Automatic certificate renewal

### Local Network Access

To access services from your local network, you'll need to configure your hosts file. This is the recommended method for local development and testing.

#### Configuring Local Hosts File

1. Locate your hosts file:
   - **Linux/macOS**: `/etc/hosts`
   - **Windows**: `C:\Windows\System32\drivers\etc\hosts`

2. Add the following entries (replace `192.168.1.100` with your Docker host's IP address):
   ```
   192.168.1.100 terrerov.com
   192.168.1.100 www.terrerov.com
   192.168.1.100 traefik.terrerov.com
   192.168.1.100 db.terrerov.com
   ```

3. Save the file (you may need administrator/root privileges)

4. Test the configuration:
   ```bash
   # Test DNS resolution
   ping www.terrerov.com
   
   # Test HTTPS access
   curl -k https://www.terrerov.com
   ```

#### Notes on Local Access
- The hosts file method requires manual configuration on each client machine
- This solution is ideal for development and testing environments
- SSL certificates will show warnings when accessed locally (expected behavior)
- For production environments, consider using proper DNS configuration

## Testing the Network

The installation script performs automatic testing, but you can manually test:

1. DNS Resolution:
   ```bash
   docker exec -it bind9 nslookup www.terrerov.com
   ```

2. Web Access:
   ```bash
   curl -H "Host: www.terrerov.com" http://localhost
   ```

3. Database Connection:
   ```bash
   docker exec -it postgres psql -U $POSTGRES_USER -d $POSTGRES_DB
   ```

## Security Notes

- All sensitive information should be stored in the `.env` file
- The `.env` file should never be committed to version control
- SSL certificates are automatically managed by Traefik
- Basic authentication is enabled for the Traefik dashboard

## Maintenance

### Updating Services

```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose down
docker-compose up -d
```

### Viewing Logs

```bash
# View logs for all services
docker-compose logs

# View logs for a specific service
docker-compose logs [service_name]
```

### Backup

To backup the PostgreSQL database:

```bash
docker exec -t postgres pg_dumpall -c -U $POSTGRES_USER > dump_$(date +%Y-%m-%d_%H_%M_%S).sql
```

## Customization

### Adding Custom Domain Names

1. Add DNS records in `bind/db.terrerov.com`
2. Add reverse DNS records in `bind/db.172.18.in-addr.arpa`
3. Restart the bind9 service:
   ```bash
   docker-compose restart bind9
   ```

### Modifying Web Content

Place your web content in the `nginx/html` directory.

## Troubleshooting

### Common Issues

1. **Services won't start**
   - Check if required ports are available
   - Verify Docker daemon is running
   - Check logs with `docker-compose logs`

2. **DNS resolution fails**
   - Verify bind9 container is running
   - Check bind9 logs for errors
   - Verify DNS records in bind configuration files
   - For local access, verify hosts file entries are correct

3. **SSL certificate issues**
   - Verify Cloudflare API token is correct
   - Check Traefik logs for certificate errors
   - For local access, SSL warnings are expected and can be safely ignored

4. **Local network access issues**
   - Verify your hosts file entries match your Docker host's IP
   - Ensure your firewall allows traffic to ports 80 and 443
   - Check if Traefik is properly binding to all network interfaces
   - Test connectivity using `curl -k` to bypass SSL verification

### Installation Logs

Check `install.log` for detailed information about the installation process and any errors that occurred.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.