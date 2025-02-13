# Terrerov Network Project

This project sets up a complete Docker-based network infrastructure with DNS, reverse proxy, web server, and database services. It's designed to be easily deployable on both Raspberry Pi and standard computers running Docker.

## Prerequisites

- Docker CE (Community Edition) installed
- Docker Compose installed (version 1.29.0 or higher)
- Basic understanding of Docker and networking concepts

## Services Included

- **Bind9**: DNS server for domain name resolution
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

Once deployed, you can access the services at:

- Traefik Dashboard: https://traefik.terrerov.com
- Web Server: https://www.terrerov.com
- Database: db.terrerov.com:5432

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

3. **SSL certificate issues**
   - Verify Cloudflare API token is correct
   - Check Traefik logs for certificate errors

### Installation Logs

Check `install.log` for detailed information about the installation process and any errors that occurred.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.